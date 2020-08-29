# -*- coding: utf-8 -*-

"""
Created on Tuesday August 25 19:32:41 2020
@author: rahulsainipusa@gmail.com (Rahul Saini)
Python Script consisting necessary api related to database creation, facial recognition, 
finding a match in database if not then create a unique entry for each & every unkown faces on live streaming.

"""

import face_recognition
import cv2, time
from datetime import datetime, timedelta
import numpy as np
import argparse, subprocess, warnings, flask, platform
import json, os, signal, pickle, sqlite3

# Our list of known face encodings and a matching list of metadata about each face.
known_face_encodings = []
known_face_metadata = []    

#generates face id for next unknown face.
def get_face_id():
    conn=sqlite3.connect('face_image_database.db')
    cmd="SELECT Face_Id FROM face_image WHERE Face_Id = (SELECT MAX(Face_Id) FROM face_image)"
    cursor=conn.execute(cmd)
    id = cursor.fetchall()[-1][0]
    conn.commit()
    cursor.close()
    conn.close()
    return id

#feed known face encoding & metadata to database
def save_known_faces_details():
    with open("known_faces.dat", "wb") as face_data_file:
        face_data = [known_face_encodings, known_face_metadata]
        pickle.dump(face_data, face_data_file)
        print("Known faces saved into the database...")



#fetch data from database for known faces.
def load_known_faces_details():
    global known_face_encodings, known_face_metadata
    print('passing into the function!!!')

    try:
        with open("known_faces.dat", "rb") as face_data_file:
            known_face_encodings, known_face_metadata = pickle.load(face_data_file)
            print("getting information from database for known faces...")
    except FileNotFoundError as e:
        print("No previous face data found - start creating with a blank known face list.")
        pass

    
#detects unknown face, creates a new entry in database & stores face image in it
def register_unknown_face(face_encoding, face_image):
    """
    Add a new person to our list of known faces
    """
    # Add the face encoding to the list of known faces
    known_face_encodings.append(face_encoding)
    face_id = get_face_id()
    conn = sqlite3.connect('face_image_database.db')
    cursor = conn.cursor()
    cv2.imwrite(r"D:\Learning_material\Ideas\Face_rec\project\final_model\face_dataset\User_"+str(face_id+1)+str('.jpg'), face_image)
    with open(r"D:\Learning_material\Ideas\Face_rec\project\final_model\face_dataset\User_"+str(face_id+1)+str('.jpg'), 'rb') as image_file:
        image_data = image_file.read()
    # Add a matching dictionary entry to our metadata list.
    # We can use this to keep track of how many times a person has visited, when we last saw them, etc.
    known_face_metadata.append({
        "first_seen": datetime.now(),
        "face_id": int(face_id+1),
        "first_seen_this_interaction": datetime.now(),
        "last_seen": datetime.now(),
        "visit_count": 1,
        "seen_frames": 1,
        "face_image": face_image,
    })
    
    cursor.execute("""
    INSERT INTO face_image (Face_image, Visit_Count, Date) VALUES (?,?,?)""", (image_data, 1, datetime.now()))    
    conn.commit()
    cursor.close()
    conn.close()

#Everytime it will try to find a face match for a face comes in front of camera
def lookup_known_face(face_encoding):
    """
    See if this is a face we already have in our face list
    """
    metadata = None

    # If known face list is empty, just return nothing since we can't possibly have seen this face.
    if len(known_face_encodings) == 0:
        return metadata

    """
    Calculate the face distance between the unknown face and every face on in our known face list
    This will return a floating point number between 0.0 and 1.0 for each known face. The smaller the number,
    the more similar that face was to the unknown face.
    """
    face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)


    best_match_index = np.argmin(face_distances)
    #print(best_match_index)

    """
    If the face with the lowest distance had a distance under 0.6, we consider it a face match.
    0.6 comes from how the face recognition model is trained. It is trained to make sure pictures
    of the same person always were less than 0.6 away from each other.
    """
    if face_distances[best_match_index] < 0.60:
        # If we have a match, look up the metadata we've saved for it (like the first time we have seen it, etc)
        metadata = known_face_metadata[best_match_index]

        # Update the metadata for the face so we can keep track of how recently we have seen that particular face.
        metadata["last_seen"] = datetime.now()
        metadata["seen_frames"] += 1

        """
        We'll also keep a total "seen count" that tracks how many times this person has come in front of Camera.
        But we can say that if we have seen this person within the last 5 minutes, it is still the same
        visit, not a new visit. But if they go away for a while and come back, that is a new visit. This should be a good hypothesis
        as here we are capturing live feed of Camera so there may be chances that people come in front of camera for regular interfval of time.
        """
        if datetime.now() - metadata["first_seen_this_interaction"] > timedelta(minutes=5):
            metadata["first_seen_this_interaction"] = datetime.now()
            metadata["visit_count"] += 1
            conn = sqlite3.connect('face_image_database.db')
            cursor = conn.cursor()
            cmd = """UPDATE face_image SET Visit_Count =?  WHERE Face_Id = ?"""
            cursor.execute(cmd, (metadata["visit_count"], metadata['face_id']))
            conn.commit()
            cursor.close()
            conn.close()

    return metadata

def rescale_frame(frame, percent=75):
    width = int(frame.shape[1] * percent/ 100)
    height = int(frame.shape[0] * percent/ 100)
    dim = (width, height)
    return cv2.resize(frame, dim, interpolation =cv2.INTER_AREA)

#Main part of the program, from here program gets executed
def main():
    #video_capture = cv2.VideoCapture(0)
    video_capture = cv2.VideoCapture("rtsp://admin:enigma1234@110.93.237.209:554/live")
    # video_capture = cv2.VideoCapture("rtsp://admin:fahadisgreat777@98.201.221.206:3005/ch06/0")


    # Track how long since we last saved a copy of our known faces to disk as a backup.
    number_of_faces_since_save = 0

    while True:
        # Grab a single frame of video
        ret, frame = video_capture.read()

        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        #small_frame = rescale_frame(frame, percent=10)
        rgb_small_frame = small_frame[:, :, ::-1]
        # rgb_small_frame = frame[:, :, ::-1]

        # Find all the face locations and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        """
        Loop through each detected face and see if it is one we have seen before
        If so, we'll give it a label that we'll draw on top of the video.
        """
        face_labels = []
        for face_location, face_encoding in zip(face_locations, face_encodings):
            # See if this face is in list of known faces.
            metadata = lookup_known_face(face_encoding)

            # If we found the face, label the face with unique Face_Id generated for each face.
            if metadata is not None:
                time_at_camera = datetime.now() - metadata['first_seen_this_interaction']
                #id_face = get_face_id()
                id_face = metadata["face_id"]
                # face_label = f"Face_Id: {int(id_face)}"
                face_label = f"Face_id: {id_face}"

            # If this is a new or Unknown face, add it to our list of known faces & feed it to database as well.
            else:
                face_label = f"Unknown Face!"

                # Grab the image of the the face from the current frame of video
                top, right, bottom, left = face_location
                face_image = small_frame[top:bottom, left:right]
                face_image = cv2.resize(face_image, (150, 150))

                # Add the Unkown face to our known face data
                register_unknown_face(face_encoding, face_image)

            face_labels.append(face_label)

        # Draw a box around each face and label each face
        for (top, right, bottom, left), face_label in zip(face_locations, face_labels):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(frame, face_label, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 0, 255), 1)

        # Display recent visitor images
        number_of_recent_visitors = 0
        for metadata in known_face_metadata:
            # If we have seen this person in the last minute, draw their image
            if datetime.now() - metadata["last_seen"] < timedelta(seconds=10) and metadata["seen_frames"] > 5:
                # Draw the known face image
                x_position = number_of_recent_visitors * 150
                frame[30:180, x_position:x_position + 150] = metadata["face_image"]
                number_of_recent_visitors += 1

                # Label the image with how many times they have visited
                visits = metadata['visit_count']
                visit_label = f"'{id_face}:' {visits} visits"
                if visits == 1:
                    visit_label = "First time visit"
                cv2.putText(frame, visit_label, (x_position + 10, 170), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

        if number_of_recent_visitors > 0:
            cv2.putText(frame, "Recent Visitors...", (5, 20), cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 0, 255), 2)


        # Display the final frame of video with boxes drawn around each detected fames
        cv2.imshow('Video', frame)

        # Hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            save_known_faces_details()
            #stopServer()
            break

        # We need to save our known faces back to disk every so often in case something crashes.
        if len(face_locations) > 0 and number_of_faces_since_save > 15:
            save_known_faces_details()
            number_of_faces_since_save = 0
        else:
            number_of_faces_since_save += 1

    # Release handle to the webcam
    video_capture.release()
    cv2.destroyAllWindows()

load_known_faces_details()
main()    