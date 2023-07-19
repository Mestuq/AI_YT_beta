from flask import Blueprint,Flask,render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO
from app import app, socketio

import pandas as pd
import scipy as sc
import numpy as np
from threading import Thread, Lock

from routes import videosBP

clean_bp = Blueprint('clean', __name__)
search_lock = Lock()

# SEARCH FOR ACCURACY MODEL
@app.route('/processClean', methods=['POST'])
def processClean():
    if not search_lock.acquire(blocking=False):
        return render_template('busy.html')
    else:
        DeleteColumnsWithOnly = request.form.get('DeleteColumnsWithOnly')
        deleteRowsWithOnly = request.form.get('deleteRowsWithOnly')
        OutlinerPrecise = request.form.get('OutlinerPrecise')
        socketio.start_background_task(Clean,DeleteColumnsWithOnly,deleteRowsWithOnly,OutlinerPrecise)
    return render_template('process.html')

def Clean(DeleteColumnsWithOnly,deleteRowsWithOnly,OutlinerPrecise):
    DeleteColumnsWithOnly = float(DeleteColumnsWithOnly)
    deleteRowsWithOnly = float(deleteRowsWithOnly)
    OutlinerPrecise = float(OutlinerPrecise)

    # LOAD DATA
    socketio.emit('Loading Data', namespace='/test')
    videosBP.load_videos()
    video_data = pd.DataFrame(videosBP.video_data)
    
    # DEFAULT INDEXING
    video_data.columns = video_data.iloc[0]
    video_data = video_data[1:]


    # GET PREDICTORS (0 - CHANNEL NAME, 3 - TAGS)
    columns_to_merge = [0, 3]
    X = video_data.apply(lambda row: ' '.join([str(row[col]) for col in columns_to_merge]), axis=1)
    X = pd.DataFrame(X)
    X = X.rename(columns={0: 'keywords'})

    # GET TARGET VALUES (2 - VIEWS)
    columns_to_merge = [2]
    Y = video_data.apply(lambda row: ' '.join([str(row[col]) for col in columns_to_merge]), axis=1)
    Y = pd.DataFrame(Y)
    Y = Y.rename(columns={0: 'views'})

    # GET LIST OF ALL TAGS
    socketio.emit('List of keywords', namespace='/test')
    keywords_series = X['keywords'].str.split().explode().unique()

    # BOOLEAN TABLE 
    socketio.emit('Generating boolean table', namespace='/test')
    X_transformed = pd.DataFrame(index=range(len(X)), columns=keywords_series)
    for row, keywords in X.iterrows():
        for column in keywords_series:
            if column in keywords['keywords']:
                X_transformed.loc[int(row), str(column)] = True
    X_transformed = X_transformed.fillna(False)
    X_transformed = X_transformed[1:]

    # MERGE VALUES BACK
    merged_XY = pd.concat([X_transformed, Y], axis=1)
    merged_XY['views'] = merged_XY['views'].astype('int64')
    Y['views'] = Y['views'].astype('int64') 

    # Save pivot table
    merged_XY.to_csv('pivotTable.csv', index=False, encoding='utf-8')

    # DELETE OUTLINERS POINTS
    socketio.emit('Finding outliners points', namespace='/test')
    z_scores = sc.stats.zscore(Y)
    abs_z_scores = np.abs(z_scores)
    
    filtered_z_scores = (abs_z_scores < OutlinerPrecise).all(axis=1) #kind of mask
    NewMerged_XY = merged_XY[filtered_z_scores]
    
    

    # DEVIDE X AND Y ONCE MORE
    X_transformed = NewMerged_XY.iloc[:, :-1]
    Y = pd.DataFrame(NewMerged_XY.iloc[:, -1])

    # DELETE ALL COLUMNS(TAGS) WITH LESS THAN GIVEN NUMBER
    socketio.emit('Deleting columns', namespace='/test')
    counts = X_transformed.sum()
    columns_to_delete = counts[counts < DeleteColumnsWithOnly].index
    X_transformed = X_transformed.drop(columns=columns_to_delete)

    

    # REMOVE ROWS (VIDEOS) WITH THE SMALLEST AMOUNT OF TAGS (OR WITHOUT)
    socketio.emit('Deleting rows', namespace='/test')
    counts = X_transformed.sum(axis=1)
    rows_to_delete = counts[counts < deleteRowsWithOnly].index
    X_transformed = X_transformed.drop(rows_to_delete)
    Y = Y.drop(rows_to_delete)

    print(Y)

    # MERGEING AND SAVEING TO FILE
    socketio.emit('Saveing', namespace='/test')
    merged_XY = pd.concat([X_transformed, Y], axis=1)
    merged_XY.to_csv("TrainingData.csv", index=False, encoding='utf-8')

    # FINISHING PROCESS
    search_lock.release()
    socketio.emit('finished', namespace='/test')
