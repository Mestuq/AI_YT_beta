from flask import Blueprint,Flask,render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO
from app import app, socketio

import pandas as pd
import matplotlib.pyplot as plt
import scipy as sc
import numpy as np
from threading import Thread, Lock
import time

from routes import videosBP

clean_bp = Blueprint('clean', __name__)
search_lock = Lock()

# SEARCH FOR ACCURACY MODEL
@clean_bp.route('/processClean', methods=['POST'])
def processClean():
    if not search_lock.acquire(blocking=False):
        return render_template('busy.html')
    else:
        DeleteColumnsWithOnly = request.form.get('DeleteColumnsWithOnly')
        deleteRowsWithOnly = request.form.get('deleteRowsWithOnly')
        OutlinerPrecise = request.form.get('OutlinerPrecise')
        socketio.start_background_task(Clean,DeleteColumnsWithOnly,deleteRowsWithOnly,OutlinerPrecise)
    return render_template('process.html')

def generateHistogram(data,src,tagsNumberForDescription):
    plt.tight_layout()  # Adjust the padding between the plot and the labels
    plt.figure(figsize=(10, 6))  # Adjust the figure size to avoid overlapping labels
    plt.xticks(rotation=45)  # Rotate x-axis labels by 45 degrees for better readability
    
    plt.hist(data, bins=25, color='skyblue', edgecolor='black') 
    plt.title('Histogram '+src+" ("+str(len(data))+" videos, "+str(tagsNumberForDescription)+" tags)")
    plt.xlabel(src)
    plt.ylabel('Frequency')
    
    plt.savefig('static/'+src+'.png', dpi=100, bbox_inches='tight')

def Clean(DeleteColumnsWithOnly,deleteRowsWithOnly,OutlinerPrecise):
    time.sleep(1) # Waiting for client to load the website
    DeleteColumnsWithOnly = float(DeleteColumnsWithOnly)
    deleteRowsWithOnly = float(deleteRowsWithOnly)
    OutlinerPrecise = float(OutlinerPrecise)

    # LOAD DATA
    socketio.emit('progress', {'data':'Loading Data'}, namespace='/test')
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
    Y['views'] = Y['views'].astype('int64') 

    # GET LIST OF ALL TAGS
    socketio.emit('progress', {'data':'List of keywords'}, namespace='/test')
    keywords_series = X['keywords'].str.split().explode().unique()

    # GENERATE HISTOGRAM
    generateHistogram(Y['views'].values,'Views before',len(keywords_series))

    # BOOLEAN TABLE 
    socketio.emit('progress', {'data':'Generating boolean table'}, namespace='/test')
    X_transformed = pd.DataFrame(index=range(len(X)), columns=keywords_series)

    for row, keywords in X.iterrows(): # row -> index, keywords -> bool
        for column in keywords_series: # column -> every possible tag
            keywordsExploded = keywords['keywords'].split()
            #print(keywordsExploded)
            if column in keywordsExploded:
                X_transformed.loc[int(row), str(column)] = True
            #if column in keywords['keywords']: #
            #    X_transformed.loc[int(row), str(column)] = True
    X_transformed = X_transformed.fillna(False)
    X_transformed = X_transformed[1:]

    # MERGE VALUES BACK
    merged_XY = pd.concat([X_transformed, Y], axis=1)
    merged_XY['views'] = merged_XY['views'].astype('int64')
    Y['views'] = Y['views'].astype('int64') 

    # Save pivot table
    merged_XY.to_csv('pivotTable.csv', index=False, encoding='utf-8')

    # DELETE OUTLINERS POINTS
    socketio.emit('progress', {'data':'Finding outliners points'}, namespace='/test')
    z_scores = sc.stats.zscore(Y)
    abs_z_scores = np.abs(z_scores)
    
    filtered_z_scores = (abs_z_scores < OutlinerPrecise).all(axis=1) #kind of mask
    NewMerged_XY = merged_XY[filtered_z_scores]
    
    # DEVIDE X AND Y ONCE MORE
    X_transformed = NewMerged_XY.iloc[:, :-1]
    Y = pd.DataFrame(NewMerged_XY.iloc[:, -1])

    # REMOVE ROWS (VIDEOS) WITH THE SMALLEST AMOUNT OF TAGS (OR WITHOUT)
    socketio.emit('progress', {'data':'Deleting rows'}, namespace='/test')
    counts = X_transformed.sum(axis=1)
    rows_to_delete = counts[counts < deleteRowsWithOnly].index
    X_transformed = X_transformed.drop(rows_to_delete)
    Y = Y.drop(rows_to_delete)

    # DELETE ALL COLUMNS(TAGS) WITH LESS THAN GIVEN NUMBER
    socketio.emit('progress', {'data':'Deleting columns'}, namespace='/test')
    counts = X_transformed.sum()
    columns_to_delete = counts[counts < DeleteColumnsWithOnly].index
    X_transformed = X_transformed.drop(columns=columns_to_delete)

    # GENERATE HISTOGRAM
    generateHistogram(Y['views'],'Views after',len(X_transformed.columns))

    # MERGEING AND SAVEING TO FILE
    socketio.emit('progress', {'data':'Saveing'}, namespace='/test')
    merged_XY = pd.concat([X_transformed, Y], axis=1)
    merged_XY.to_csv("TrainingData.csv", index=False, encoding='utf-8')

    # FINISHING PROCESS
    search_lock.release()
    socketio.emit('finished', namespace='/test')
    print("=============END==============")