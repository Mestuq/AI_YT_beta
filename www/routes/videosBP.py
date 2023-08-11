from flask import Blueprint,Flask,render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO
from app import socketio

from threading import Thread, Lock
import csv
import yt_dlp
import pandas as pd
import os
import time

from routes import channelsBP


videos_bp = Blueprint('videos', __name__)

video_data = []
search_lock = Lock()

def load_videos():
    global video_data
    try:
        with open('videos.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            video_data = list(reader)
    except FileNotFoundError:
        video_data = []

def normalizeText(text):
    return text.lower().replace(' ', '_').replace(',', ' ')

# SEARCH QUERRY FOR VIDEOS
@videos_bp.route('/processSearchForYoutubeVideos', methods=['POST'])
def processSearchForYoutubeVideos():
    if not search_lock.acquire(blocking=False):
        return render_template('busy.html')
    else:
        PagesNumber = request.form.get('PagesNumber')
        ReplaceCSV = request.form.get('ReplaceCSV')
        socketio.start_background_task(searchForYoutubeVideos,PagesNumber,ReplaceCSV)
    return render_template('process.html')

def getListOfDownloadedChannels():
    
    if not os.path.exists("downloaded/"):
        os.makedirs("downloaded/")

    file_names_without_extension = []
    for file_name in os.listdir("downloaded/"):
        # Check if it's a file and not a directory
        if os.path.isfile(os.path.join("downloaded/", file_name)):
            # Split the file name and extension
            file_name_without_extension, file_extension = os.path.splitext(file_name)
            file_names_without_extension.append(file_name_without_extension)
    return file_names_without_extension

@videos_bp.route('/concatChannels', methods=['POST'])
def concatChannels():

    if not os.path.exists("downloaded/"):
        os.makedirs("downloaded/")

    selected_channels = []
    form_data = request.form

    for key, value in form_data.items():
        if key != 'Concat' and key != 'Delete':
            selected_channels.append(key)

    if 'Concat' in form_data:
        dataframes = []
        for channel in selected_channels:
            file_path = os.path.join('downloaded', f'{channel}.csv')
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                dataframes.append(df)
        if dataframes:
            concatenated_df = pd.concat(dataframes, ignore_index=True)
            concatenated_df.to_csv('videos.csv', index=False)

    elif 'Delete' in form_data:
        for channel in selected_channels:
            file_path = os.path.join('downloaded', f'{channel}.csv')
            if os.path.exists(file_path):
                os.remove(file_path)

    return redirect(url_for('index.advanced')) 


    

def searchForYoutubeVideos(PagesNumber,ReplaceCSV):

    if not os.path.exists("downloaded/"):
        os.makedirs("downloaded/")

    time.sleep(1) # Waiting for client to load the website
    print("=============STARTING==============")
    # PREPARING DATA
    channelsBP.load_channels()
    global video_data
    video_data = []

    # YOUTUBE SEARCHING OPTIONS
    ydl_opts = {
        'verbose': True,
        'playlistend': PagesNumber
    }

    # DOWNLOADING VIDEO DATA
    for count,url in enumerate(channelsBP.channels):
        user_videos = []
        if (ReplaceCSV == "on") or (not os.path.exists("downloaded/@"+url[0].split("@")[-1]+'.csv')):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    print(f'-------------------Processing step {count+1}/{len(channelsBP.channels)}:({url[0]})')
                    socketio.emit('progress', {'data': f'Processing step {count+1}/{len(channelsBP.channels)}:({url[0]})'}, namespace='/test')

                    info = ydl.extract_info(url[0]+"/videos", download=False)
                    if info is not None and hasattr(info, 'get'):
                        videos = info.get('entries')

                        for video in videos:
                            if video is not None and hasattr(info, 'get'):
                                video_info = {
                                    'Channel': normalizeText("(uploader)"+video.get('uploader', '')),
                                    'Title': video.get('title', '').lower(),
                                    'Views': video.get('view_count', ''),
                                    #'Description': video.get('description', '').lower(),
                                    'Tags': normalizeText(','.join(["(tag)" + tag for tag in video.get('tags', [])])),
                                    #'PhrasesTitle': "",
                                    #'PhrasesDescription': ""
                                }
                                video_data.append(video_info)

                                user_videos.append(video_info)
                                
                            #backup = pd.DataFrame(video_data)
                            #backup.to_csv('backup.csv', index=False)
                            
                        user_videos = pd.DataFrame(user_videos) 
                        user_videos.to_csv("downloaded/@"+url[0].split("@")[-1]+'.csv', index=False)
                except Exception as e:
                    print(f'Error processing URL: {url}')
                    print(e)
                    socketio.emit('errorOccured',{'errorContent': str(e)}, namespace='/test')
    #df = pd.DataFrame(video_data) 
    #df.to_csv('videos.csv', index=False)
            #return df


    # SAVEING DATA 
    

    # FINISHING
    search_lock.release()
    socketio.emit('finished', namespace='/test')
    print("=============END==============")
