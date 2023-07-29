from flask import Blueprint,Flask,render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO
from app import app, socketio

import csv

from routes import videosBP,channelsBP

index_bp = Blueprint('index', __name__)

# INDEX.HTML

@index_bp.route('/', methods=['GET', 'POST'])
def index():
    return render_template('./simple.html')

#@index_bp.route('/', methods=['GET', 'POST'])
@index_bp.route('/advanced', methods=['GET', 'POST'])
def advanced():
    channelsBP.load_channels()
    videosBP.load_videos()

    #resultsLogisticRegression
    #resultsRandomForest
    #accuracyLogisticRegression
    #accuracyRandomForest
    accuracy = load_csv("Accuracy.csv")
    resultsLogisticRegression = load_csv("LinearRegression.csv")
    resultsRandomForest = load_csv("RandomForest.csv")
    listOfDownloadedChannels = videosBP.getListOfDownloadedChannels()

    return render_template('./advanced.html', channels=channelsBP.channels,videos=videosBP.video_data, accuracy=accuracy, resultsLogisticRegression=resultsLogisticRegression, resultsRandomForest=resultsRandomForest, DownloadedChannels=listOfDownloadedChannels)

@socketio.on('connect', namespace='/test')
def test_connect():
    socketio.emit('connected', {'data': 'Connected'}, namespace='/test')

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')

def load_csv(source):
    try:
        with open(source, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            data = list(reader)
    except FileNotFoundError:
        data = []
    return data