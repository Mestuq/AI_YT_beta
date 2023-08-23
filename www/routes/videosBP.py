from flask import Blueprint,Flask,render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO
from app import socketio
from threading import Thread, Lock
import pandas as pd
import yt_dlp, csv, os, time
from routes import channelsBP

videos_bp = Blueprint('videos', __name__)
video_data = []
videos_lock = Lock()

def load_videos():
    global video_data
    try:
        with open('videos.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            video_data = list(reader)
    except FileNotFoundError:
        video_data = []

def normalize_text(text): # Tags are distinguished by spaces, so spaces will be replaced with _
    return text.lower().replace(' ', '_').replace(',', ' ')

@videos_bp.route('/processSearchForYoutubeVideos', methods=['POST'])
def process_search_for_youtube_videos():
    if videos_lock.locked():
        return render_template('busy.html.j2')
    else:
        pages_number = request.form.get('PagesNumber')
        replace_CSV = request.form.get('ReplaceCSV')
        socketio.start_background_task(search_for_youtube_videos, pages_number, replace_CSV)
    return render_template('process.html.j2')

def get_list_of_downloaded_channels(): # Downloaded channels are got from folder /downloaded content
    if not os.path.exists("downloaded/"):
        os.makedirs("downloaded/")
    file_names_without_extension = []
    for file_name in os.listdir("downloaded/"):
        if os.path.isfile(os.path.join("downloaded/", file_name)):
            file_name_without_extension, file_extension = os.path.splitext(file_name)
            file_names_without_extension.append(file_name_without_extension)
    return file_names_without_extension

@videos_bp.route('/concatChannels', methods=['POST'])
def concat_and_delete_channels():
    if not os.path.exists("downloaded/"):
        os.makedirs("downloaded/")
    selected_channels = []
    form_data = request.form
    for key, value in form_data.items(): # Get selected checkboxes
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
    return redirect(url_for('index.advanced_website')) 

def delete_all_channels():
    if os.path.exists("downloaded/"):
        file_list = os.listdir("downloaded/")
        for file_name in file_list:
            file_path = os.path.join("downloaded/", file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)

def concat_all_channels():
    dataframes = []
    if os.path.exists("downloaded/"):
        file_list = os.listdir("downloaded/")
        for file_name in file_list:
            file_path = os.path.join("downloaded/", file_name)
            if os.path.isfile(file_path):
                df = pd.read_csv(file_path)
                dataframes.append(df)
    concatenated_df = pd.concat(dataframes, ignore_index=True)
    concatenated_df.to_csv('videos.csv', index=False)

def search_for_youtube_videos(pages_number, replace_CSV):
    time.sleep(1) # Waiting for client to load the website
    if not videos_lock.acquire(blocking=False):
        return
    if not os.path.exists("downloaded/"):
        os.makedirs("downloaded/")
    
    channelsBP.load_channels()
    global video_data
    video_data = []
    ydl_opts = {
        'verbose': True,
        'playlistend': pages_number
    }
    for count,url in enumerate(channelsBP.channels):
        user_videos = []
        if (replace_CSV == "on") or (not os.path.exists("downloaded/@"+url[0].split("@")[-1]+'.csv')):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    socketio.emit('progress', {'data': f'Processing step {count+1}/{len(channelsBP.channels)}:({url[0]})'}, namespace='/test')
                    info = ydl.extract_info(url[0]+"/videos", download=False)
                    if info is not None and hasattr(info, 'get'):
                        videos = info.get('entries')
                        for video in videos:
                            if video is not None and hasattr(info, 'get'):
                                video_info = {
                                    'Channel': normalize_text("(uploader)"+video.get('uploader', '')),
                                    'Title': video.get('title', '').lower(),
                                    'Views': video.get('view_count', ''),
                                    'Tags': normalize_text(','.join(["(tag)" + tag for tag in video.get('tags', [])])),
                                    }
                                video_data.append(video_info)
                                user_videos.append(video_info)
                        user_videos = pd.DataFrame(user_videos) 
                        user_videos.to_csv("downloaded/@"+url[0].split("@")[-1]+'.csv', index=False)
                except Exception as e:
                    print(f'Error processing URL: {url}')
                    socketio.emit('errorOccured',{'errorContent': str(e)}, namespace='/test')
    videos_lock.release()
    socketio.emit('finished', namespace='/test')
