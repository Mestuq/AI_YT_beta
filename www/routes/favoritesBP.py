from flask import Blueprint,Flask,render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO
from app import app, socketio
import pandas as pd
import scipy as sc
import numpy as np
import os, shutil
from routes import indexBP

favorites_bp = Blueprint('favorites', __name__)

def get_favorites(): # Favorites are got from folder /favorites content
    if not os.path.exists("favorites/"):
        os.makedirs("favorites/")
    name_set = set()
    file_list = os.listdir("favorites/")
    for file_name in file_list:
        if file_name.endswith(".csv"):
            parts = file_name.split("_")
            if len(parts) >= 2:
                name = parts[0]
                name_set.add(name)
    return name_set

@favorites_bp.route('/FavoriteSaveAs', methods=['GET'])
def favorite_save_as():
    name = request.args.get('name')
    favorite_save_as(name)
    return redirect(url_for('index.advanced_website')) 

def favorite_save_as(name):
    if not os.path.exists("favorites/"):
        os.makedirs("favorites/")
    shutil.copy("LinearRegression.csv"  , "favorites/"+name+"_LinearRegression.csv")
    shutil.copy("RandomForest.csv"      , "favorites/"+name+"_RandomForest.csv")
    shutil.copy("Accuracy.csv"          , "favorites/"+name+"_Accuracy.csv")

@favorites_bp.route('/favorites', methods=['GET'])
def favorites():
    name = request.args.get('name')
    results_logistic_regression = indexBP.load_csv("favorites/"+name+"_LinearRegression.csv")
    results_random_forest = indexBP.load_csv("favorites/"+name+"_RandomForest.csv")
    accuracy = indexBP.load_csv("favorites/"+name+"_Accuracy.csv")
    return render_template('favoritePreview.html.j2',
                           resultsLogisticRegression=results_logistic_regression,
                           resultsRandomForest=results_random_forest,
                           accuracy=accuracy)

@favorites_bp.route('/favoritesDelete', methods=['GET'])
def favorites_delete():
    name = request.args.get('name')
    files = ["favorites/"+name+"_LinearRegression.csv",
             "favorites/"+name+"_RandomForest.csv",
             "favorites/"+name+"_Accuracy.csv"]
    for file_name in files:
        if os.path.exists(file_name):
            os.remove(file_name)
    return redirect(url_for('index.advanced_website')) 
