from flask import Blueprint,Flask,render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO
from app import app, socketio

from threading import Thread, Lock
import csv
import os
import sys 
import time
import yt_dlp

channels_bp = Blueprint('channels', __name__)

channels = []
search_lock = Lock()
progressInfo=0

def load_channels():
    global channels
    try:
        with open('channels.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            channels = list(reader)
    except FileNotFoundError:
        channels = []

@channels_bp.route('/addChannel', methods=['POST'])
def add():
    global channels
    text = request.form.get('text')
    if text:
        with open('channels.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            if [text] not in channels: # REMOVE DUPLICATES
                writer.writerow([text])
                channels.append(text)
                return jsonify({'success': True})
    return jsonify({'success': False})

@channels_bp.route('/removeChannel', methods=['POST'])
def remove():
    index = int(request.form.get('index'))
    if 0 <= index < len(channels):
        del channels[index]
        with open('channels.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(channels)
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})

class MyLogger:
    def debug(self, msg):
        if msg.startswith('[debug] '):
            pass
        else:
            self.info(msg)
    def info(self, msg):
        global progressInfo
        if '[download] Downloading item ' in msg:
            progressInfo+=1
            print(f'------ Downloaded items: {progressInfo}')
            socketio.emit('progress', {'data': f'Downloaded items: {progressInfo}'}, namespace='/test')
            #[youtube:search_url] query "a" page 1: Downloading API JSON
        print(msg)
        pass
    def warning(self, msg):
        print(msg)
        pass
    def error(self, msg):
        print(msg)

# SEARCH QUERRY FOR CHANNELS

@channels_bp.route('/processSearchForYoutubeChannels', methods=['POST'])
def processSearchForYoutubeChannels():
    if not search_lock.acquire(blocking=False):
        return render_template('busy.html')
    else:
        YoutubeQuery = request.form.get('YoutubeQuery')
        PagesNumber = request.form.get('PagesNumber')
        ReplaceChannel = request.form.get('ReplaceChannel')
        socketio.start_background_task(searchForYoutubeChannels,YoutubeQuery,PagesNumber,ReplaceChannel)
    return render_template('process.html')

def searchForYoutubeChannels(YoutubeQuery,PagesNumber,ReplaceChannel):
    time.sleep(1) # Waiting for client to load the website
    # PREPARING DATA
    global progressInfo
    progressInfo = 0

    global channels
    if (ReplaceChannel == "on"):
        channels = []
    else:
        load_channels()
    
    urlTest="https://www.youtube.com/results?search_query="+YoutubeQuery.replace(' ', '+')

    # YOUTUBE SEARCH OPTIONS
    ydl_opts = {
    'logger': MyLogger(),
    'noabortonerror': True,
    'ignoreerrors': True,
    'skip_download': True,
    'no_warnings': True,
    'writesubtitles': False,
    'writeautomaticsub': False,
    'allsubtitles': False,
    'listformats': False,
    'forcejson': False,
    'quiet': True,
    'no_warnings': True,
    'verbose': True,
    'playlistend': PagesNumber
    }

    # SEARCHING
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(urlTest, download=False)
        for count, entry in enumerate(info['entries']):
            try:
                if entry['uploader_url'] not in channels: # REMOVING DUPLICATES
                    channels.append(entry['uploader_url'])
            except Exception as e:
                print(f"Error occurred: {e}")
                socketio.emit('errorOccured',{'errorContent': str(e)}, namespace='/test')
                continue

    # SAVEING
    try:
        with open(r'channels.csv', 'w') as fp:
            for item in channels:
                fp.write("%s\n" % item)
    except Exception as e:
        print(f"Error occurred: {e}")
        socketio.emit('errorOccured',{'errorContent': str(e)}, namespace='/test')
    
    # FINISHING
    search_lock.release()
    socketio.emit('finished', namespace='/test')
