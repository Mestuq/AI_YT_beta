
from flask import Blueprint,Flask,render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO
from app import app, socketio
from threading import Thread, Lock
import time
from routes import videosBP, channelsBP, cleanBP, tagsBP, accuracyBP, favoritesBP

simple_bp = Blueprint('simple', __name__)
search_lock = Lock()


@simple_bp.route('/processAll', methods=['POST'])
def process_search_for_youtube_videos():
    if not search_lock.acquire(blocking=False):
        return render_template('busy.html.j2')
    else:
        youtube_query = request.form.get('YoutubeQuery')
        socketio.start_background_task(process_all_tasks, youtube_query)
    return render_template('processAll.html.j2')

def handle_task(status_str, task_func, *args, **kwargs):
    socketio.emit('status',{'status': str(status_str)}, namespace='/test')
    try:
        task_func(*args, **kwargs)
    except Exception as e:
        print(f"Error occurred: {e}")
        socketio.emit('errorOccured',{'errorContent': str(e)}, namespace='/test')

def process_all_tasks(youtube_query):
    # Default settings:
    pages_number_channels = 25
    replace_channel = "on"
    pages_number_videos = 25
    replace_CSV = "on"
    delete_columns_with_only = 4
    delete_rows_with_only = 2
    outliner_precise = 2.0
    accept_error = 50
    amount_of_tags = 25
    # Handle automatic operations
    handle_task("Deleting ceche", videosBP.delete_all_channels)
    handle_task("Searching for Youtube channels", channelsBP.search_for_youtube_channels, youtube_query, pages_number_channels, replace_channel)
    handle_task("Downloading video informations", videosBP.search_for_youtube_videos, pages_number_videos, replace_CSV)
    handle_task("Merging results", videosBP.concat_all_channels)
    handle_task("Cleaning data", cleanBP.clean_data, delete_columns_with_only, delete_rows_with_only, outliner_precise)
    handle_task("Checking accuracy", accuracyBP.check_for_accuracy, accept_error)
    handle_task("Fetching tags", tagsBP.get_tags, amount_of_tags)
    handle_task("Saveing results", favoritesBP.favorite_save_as, youtube_query)
    # TO DO: REDIRECT TO FAVORITE
    socketio.emit('finishedAll', namespace='/test')

