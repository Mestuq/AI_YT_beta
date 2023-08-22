from flask import Blueprint,Flask,render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO
from app import app, socketio
import csv
from routes import videosBP,channelsBP,favoritesBP

index_bp = Blueprint('index', __name__)

@index_bp.route('/')
def index_website():
    return render_template('./simple.html.j2')

@index_bp.route('/advanced', methods=['GET', 'POST'])
def advanced_website():
    channelsBP.load_channels()
    videosBP.load_videos()
    accuracy = load_csv("Accuracy.csv")
    results_logistic_regression = load_csv("LinearRegression.csv")
    results_random_forest = load_csv("RandomForest.csv")
    list_of_downloaded_channels = videosBP.get_list_of_downloaded_channels()
    favorites = favoritesBP.get_favorites()
    videos_sorted =sorted(videosBP.video_data, key=lambda x: int(x[2]) if x[2].isdigit() else float('inf'), reverse=True)
    return render_template('./advanced.html.j2', 
                           channels=channelsBP.channels,
                           videos=videos_sorted,
                           accuracy=accuracy, 
                           resultsLogisticRegression=results_logistic_regression, 
                           resultsRandomForest=results_random_forest, 
                           DownloadedChannels=list_of_downloaded_channels, 
                           favorites=favorites)

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