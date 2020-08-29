"face_dataset" will be having best shot for a face & same will be passed to the database if model identifies an unkown face.

stored html file in "templates" folder for providing User experience Dashboard.

"face_image_database.db" SQLite database is having Face_Id, Face_image (best shot captured through the model), Visit_Count(how many times user has came in front of camera) & Date.

"known_faces.dat" contains face location & face encoding matrix.

"requirements.txt" all packages need to be installed before running any of the script.

"app.py" flask API file.

"face_rec.py" facial recognition file.


Workflow:-

    Clone the repository : git clone https://github.com/shameerahirji/face_rec_project.git
    
    cd face_rec_project
    
    pip install -r requirements.txt (for installing all necessary packages)
    
    
    python app.py (by executing the following script you can launch the API on browser)
    
        1). go to browser type the url shown on command line & click on Start Live Streaming, you can view the streaming where model will create bounding box for detected faces.
        
        2). If there is any face match, model will feed that data to databse. you can check that as well simply by logging into the "face_image_database.db" database.
        
            sqlite3 face_image_database.db
            
            .tables    (for listing the tables within this database)
            
            SELECT * FROM face_image
            
            """
            
            1|?PNG|1|2020-08-22 18:28:49.179448
            
            86|????|3|2020-08-25 22:43:22.140573
            
            87|????|1|2020-08-26 00:24:26.989561
            
            88|????|2|2020-08-26 00:27:00.044917
            
            89|????|4|2020-08-26 00:36:57.287523
            
            """
