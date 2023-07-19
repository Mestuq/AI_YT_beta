from flask import Blueprint,Flask,render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO
from app import socketio

from threading import Thread, Lock
import csv
import yt_dlp
import pandas as pd

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
        socketio.start_background_task(searchForYoutubeVideos,PagesNumber)
    return render_template('process.html')

def searchForYoutubeVideos(PagesNumber):
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
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            for count,url in enumerate(channelsBP.channels):
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
                        
                        backup = pd.DataFrame(video_data)
                        backup.to_csv('backup.csv', index=False)
            df = pd.DataFrame(video_data) 
            df.to_csv('videos.csv', index=False)
            #return df

        except Exception as e:
            print(f'Error processing URL: {url}')
            print(e)
    
    # SAVEING DATA 
    

    # FINISHING
    search_lock.release()
    socketio.emit('finished', namespace='/test')
    print("=============END==============")
