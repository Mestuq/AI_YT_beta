from flask import Blueprint, render_template, request
from app import app, socketio
from threading import Lock
import pandas as pd
import scipy as sc
import numpy as np
import time

timeline_bp = Blueprint('timeline', __name__)
timeline_lock = Lock()

@timeline_bp.route('/processTimeline', methods=['POST'])
def process_get_tags():
    if not timeline_lock.locked():
        return render_template('busy.html.j2')
    else:
        socketio.start_background_task(generate_timeline)
    return render_template('process.html.j2')

def get_year(date_string):
    if len(date_string) >= 4:
        year = int(date_string[-4:])
        return year
    else:
        raise ValueError("Input date string is too short to extract the year.")

def generate_timeline():
    time.sleep(1) # Waiting for client to load the website
    if not timeline_lock.acquire(blocking=False):
        return

    try:
        # EMIT socketio.emit('progress', {'data': "Progress: " + str(max_splits)}, namespace='/test')
        data = pd.read_csv('TrainingData.csv')
        Xval = data.iloc[:, :-2] # [...,'Views','Upload-date']
        yval = data.iloc[:, -2].values.ravel()
    except Exception as e:
        print(f"Error occurred: {e}")
        socketio.emit('errorOccured',{'errorContent': str(e)}, namespace='/test')
    
    timeline_lock.release() 
    socketio.emit('finished', namespace='/test')