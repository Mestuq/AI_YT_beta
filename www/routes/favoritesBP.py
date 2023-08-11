from flask import Blueprint,Flask,render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO
from app import app, socketio

import pandas as pd
import scipy as sc
import numpy as np
import shutil
import os

from routes import indexBP

favorites_bp = Blueprint('favorites', __name__)

def getFavorites():

    if not os.path.exists("favorites/"):
        os.makedirs("favorites/")

    name_set = set()
    # List all files in the favorites folder
    file_list = os.listdir("favorites/")
    # Extract the "name" part from each file name and add it to the set
    for file_name in file_list:
        if file_name.endswith(".csv"):
            parts = file_name.split("_")
            if len(parts) >= 2:
                name = parts[0]
                name_set.add(name)
    return name_set

@favorites_bp.route('/FavoriteSaveAs', methods=['GET'])
def FavoriteSaveAs():
    name = request.args.get('name')
    # CREATE FOLDER IF NOT EXIST
    if not os.path.exists("favorites/"):
        os.makedirs("favorites/")

    shutil.copy("LinearRegression.csv"  , "favorites/"+name+"_LinearRegression.csv")
    shutil.copy("RandomForest.csv"      , "favorites/"+name+"_RandomForest.csv")
    shutil.copy("Accuracy.csv"  , "favorites/"+name+"_Accuracy.csv")

    return redirect(url_for('index.advanced')) 

@favorites_bp.route('/favorites', methods=['GET'])
def favorites():
    name = request.args.get('name')

    resultsLogisticRegression = indexBP.load_csv("favorites/"+name+"_LinearRegression.csv")
    resultsRandomForest = indexBP.load_csv("favorites/"+name+"_RandomForest.csv")
    accuracy = indexBP.load_csv("favorites/"+name+"_Accuracy.csv")

    return render_template('favoritePreview.html',
                           resultsLogisticRegression=resultsLogisticRegression,
                           resultsRandomForest=resultsRandomForest,
                           accuracy=accuracy)

@favorites_bp.route('/favoritesDelete', methods=['GET'])
def favoritesDelete():
    name = request.args.get('name')

    files = ["favorites/"+name+"_LinearRegression.csv",
             "favorites/"+name+"_RandomForest.csv",
             "favorites/"+name+"_Accuracy.csv"]

    for fileName in files:
        if os.path.exists(fileName):
            os.remove(fileName)

    return redirect(url_for('index.advanced')) 
