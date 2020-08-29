# -*- coding: utf-8 -*-

"""
Created on Tuesday August 25 19:32:41 2020
@author: rahulsainipusa@gmail.com (Rahul Saini)
Python Script consisting necessary api related to database creation, facial recognition, 
finding a match in database if not then create a unique entry for each & every unkown faces on live streaming.

"""


from flask import Flask, render_template
from flask_cors import CORS, cross_origin
from flask import Flask, jsonify, request, send_file
from flask import Flask, render_template, jsonify, request
import warnings, os, signal


# Flask Application Configuration and Defining flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
# Handling Cross Origin Reference Issue
CORS(app, support_credentials=True)
# Ignoring the errors during production
warnings.filterwarnings("ignore")

@app.route('/')
def index(name=None):
    return render_template('index.html',name=name)

@app.route('/face_rec')
def parse(name=None):
    import face_rec
    print("done")
    return render_template('index.html',name=name)
    
#Shutting down the server once we want to stop the live feed
@app.route('/stopServer')
def stopServer():
    os.kill(os.getpid(), signal.SIGINT)
    return jsonify({ "success": True, "message": "Server is shutting down..." })


if __name__ == '__main__':
    app.run()
    app.debug = True