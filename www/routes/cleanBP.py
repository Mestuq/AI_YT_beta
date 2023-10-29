from flask import Blueprint, render_template, request, Response
from app import socketio
import pandas as pd
import matplotlib.pyplot as plt
import scipy as sc
import numpy as np
from threading import Lock
import os, time, io
from PIL import Image
from routes import videosBP

clean_bp = Blueprint('clean', __name__)
clean_lock = Lock()

@clean_bp.route('/processClean', methods=['POST'])
def process_clean():
    if clean_lock.locked():
        return render_template('busy.html.j2')
    else:
        delete_columns_with_only = request.form.get('DeleteColumnsWithOnly')
        delete_rows_with_only = request.form.get('DeleteRowsWithOnly')
        outliner_precise = request.form.get('OutlinerPrecise')
        socketio.start_background_task(clean_data, int(delete_columns_with_only), int(delete_rows_with_only), float(outliner_precise))
    return render_template('process.html.j2')

def generate_histogram(data, src, tagsNumberForDescription):
    plt.tight_layout()
    plt.figure(figsize=(10, 6))
    plt.xticks(rotation=45)
    plt.hist(data, bins=25, color='skyblue', edgecolor='black') 
    plt.title('Histogram '+src+" ("+str(len(data))+" videos, "+str(tagsNumberForDescription)+" tags)")
    plt.xlabel(src)
    plt.ylabel('Frequency')
    plt.savefig(src+'.png', dpi=100, bbox_inches='tight')

@clean_bp.route('/image', methods=['GET']) # Loading images for standalone version of app
def get_image():
    image_path = request.args.get('src')
    if not image_path:
        return "Image source path not provided.", 400
    image = Image.open(image_path)
    image_stream = io.BytesIO()
    image.save(image_stream, format='png')
    image_stream.seek(0) 
    headers = {'Content-Type': 'image/png'}
    return Response(image_stream, headers=headers)

def clean_data(delete_columns_with_only, delete_rows_with_only, outliner_precise):
    time.sleep(1) # Waiting for client to load the website
    if not clean_lock.acquire(blocking=False):
        return
    try:
        socketio.emit('progress', {'data':'Loading Data'}, namespace='/test')
        videosBP.load_videos()
        video_data = pd.DataFrame(videosBP.video_data)
        
        # Remove default indexing
        video_data.columns = video_data.iloc[0]
        video_data = video_data[1:]

        # Get predictors (0 - CHANNEL NAME, 3 - TAGS)
        columns_to_merge = [0, 3]
        X = video_data.apply(lambda row: ' '.join([str(row[col]) for col in columns_to_merge]), axis=1)
        X = pd.DataFrame(X)
        X = X.rename(columns={0: 'keywords'})

        # Get target values (2 - VIEWS)
        columns_to_merge = [2]
        Y = video_data.apply(lambda row: ' '.join([str(row[col]) for col in columns_to_merge]), axis=1)
        Y = pd.DataFrame(Y)
        Y = Y.rename(columns={0: 'views'})
        Y['views'] = Y['views'].astype('int64') 

        # List of all tags
        socketio.emit('progress', {'data':'List of keywords'}, namespace='/test')
        keywords_series = X['keywords'].str.split().explode().unique()

        # Generate histogram
        generate_histogram(Y['views'].values,'ViewsBefore',len(keywords_series))

        # Generate boolean table
        socketio.emit('progress', {'data':'Generating boolean table'}, namespace='/test')
        X_transformed = pd.DataFrame(index=range(len(X)), columns=keywords_series)
        for indx, keywords in X.iterrows(): # indx -> index, keywords -> bool
            for column in keywords_series: # column -> every possible tag
                keywordsExploded = keywords['keywords'].split()
                if column in keywordsExploded:
                    X_transformed.loc[int(indx), str(column)] = True
        X_transformed = X_transformed.fillna(False)
        X_transformed = X_transformed[1:]

        # Merge values back
        merged_XY = pd.concat([X_transformed, Y], axis=1)
        merged_XY['views'] = merged_XY['views'].astype('int64')
        Y['views'] = Y['views'].astype('int64') 

        # Delete outliners points
        socketio.emit('progress', {'data':'Finding outliners points'}, namespace='/test')
        z_scores = sc.stats.zscore(Y)
        abs_z_scores = np.abs(z_scores)
        
        filtered_z_scores = (abs_z_scores < outliner_precise).all(axis=1) #kind of mask
        new_data_XY = merged_XY[filtered_z_scores]
        
        # Devide X and Y once again
        X_transformed = new_data_XY.iloc[:, :-1]
        Y = pd.DataFrame(new_data_XY.iloc[:, -1])

        # Remove rows (videos) with the smallest amount of tags (or without)
        socketio.emit('progress', {'data':'Deleting rows'}, namespace='/test')
        counts = X_transformed.sum(axis=1)
        rows_to_delete = counts[counts < delete_rows_with_only].index
        X_transformed = X_transformed.drop(rows_to_delete)
        Y = Y.drop(rows_to_delete)

        # Delete all columns(tags) with less than given number
        socketio.emit('progress', {'data':'Deleting columns'}, namespace='/test')
        counts = X_transformed.sum()
        columns_to_delete = counts[counts < delete_columns_with_only].index
        X_transformed = X_transformed.drop(columns=columns_to_delete)

        # Generate histogram
        generate_histogram(Y['views'],'ViewsAfter',len(X_transformed.columns))

        # Mergeing and saveing to file
        socketio.emit('progress', {'data':'Saveing'}, namespace='/test')
        merged_XY = pd.concat([X_transformed, Y], axis=1)
        merged_XY.to_csv("TrainingData.csv", index=False, encoding='utf-8')

        socketio.emit('finished', namespace='/test')
    except Exception as e:
        socketio.emit('errorOccured',{'errorContent': str(e)}, namespace='/test')
    clean_lock.release()