from flask import Blueprint, render_template, request, jsonify
from app import socketio
from threading import Lock
import yt_dlp, csv, time

channels_bp = Blueprint('channels', __name__)
channels = []
channels_lock = Lock()
progress_info = 0

def load_channels():
    global channels
    try:
        with open('channels.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            channels = list(reader)
    except FileNotFoundError:
        channels = []

@channels_bp.route('/addChannel', methods=['POST'])
def add_channel():
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
def remove_channel():
    index = int(request.form.get('index'))
    if 0 <= index < len(channels):
        del channels[index]
        with open('channels.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(channels)
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})

class YtDlpProgress:
    def debug(self, msg):
        if msg.startswith('[debug] '):
            pass
        else:
            self.info(msg)
    def info(self, msg):
        global progress_info
        if '[download] Downloading item ' in msg:
            progress_info += 1
            socketio.emit('progress', {'data': f'Pages searched: {progress_info}'}, namespace='/test')
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        socketio.emit('errorOccured',{'errorContent': str(msg)}, namespace='/test')
        pass

@channels_bp.route('/processSearchForYoutubeChannels', methods=['POST'])
def process_search_for_youtube_channels():
    if channels_lock.locked():
        return render_template('busy.html.j2')
    else:
        youtube_query = request.form.get('YoutubeQuery')
        pages_number = request.form.get('PagesNumber')
        replace_channel = request.form.get('ReplaceChannel')
        socketio.start_background_task(search_for_youtube_channels, youtube_query, pages_number, replace_channel)
    return render_template('process.html.j2')

def search_for_youtube_channels(youtube_query, pages_number, replace_channel):
    time.sleep(1) # Waiting for client to load the website
    if not channels_lock.acquire(blocking=False):
        return
    global progress_info
    progress_info = 0
    global channels
    if (replace_channel == "on"):
        channels = []
    else:
        load_channels()
    url_test = "https://www.youtube.com/results?search_query="+youtube_query.replace(' ', '+')

    ydl_opts = {
        'logger': YtDlpProgress(),
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
        'playlistend': pages_number
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url_test, download=False)
        for count, entry in enumerate(info['entries']):
            try:
                if entry['uploader_url'] not in channels: # Removing duplicates
                    channels.append(entry['uploader_url'])
            except Exception as e:
                print(f"Error occurred: {e}")
                socketio.emit('errorOccured',{'errorContent': str(e)}, namespace='/test')
                continue
    try:
        with open(r'channels.csv', 'w') as fp:
            for item in channels:
                fp.write("%s\n" % item)
    except Exception as e:
        print(f"Error occurred: {e}")
        socketio.emit('errorOccured',{'errorContent': str(e)}, namespace='/test')
    
    channels_lock.release()
    socketio.emit('finished', namespace='/test')
