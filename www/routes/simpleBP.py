
from flask import Blueprint, render_template, request
from app import socketio
from threading import Lock
import time
from routes import videosBP, channelsBP, cleanBP, tagsBP, accuracyBP, favoritesBP, timelineBP

simple_bp = Blueprint('simple', __name__)
simple_lock = Lock()

@simple_bp.route('/processAll', methods=['GET'])
def process_search_for_youtube_videos():
    if simple_lock.locked():
        return render_template('busy.html.j2')
    else:
        youtube_query = request.args.get('YoutubeQuery')
        search_pages = request.args.get('SearchPages')
        socketio.start_background_task(process_all_tasks, youtube_query, int(search_pages))
    return render_template('processAll.html.j2')

def handle_task(status_str, task_func, *args, **kwargs):
    socketio.emit('status',{'status': str(status_str)}, namespace='/test')
    try:
        task_func(*args, **kwargs)
    except Exception as e:
        print(f"Error occurred: {e}")
        socketio.emit('errorOccured',{'errorContent': str(e)}, namespace='/test')

def process_all_tasks(youtube_query, search_pages):
    time.sleep(1) # Waiting for client to load the website
    if not simple_lock.acquire(blocking=False):
        return
    # Default settings:
    pages_number_channels = search_pages # DEFAULT 50
    replace_channel = "on"
    pages_number_videos = search_pages # DEFAULT 50
    replace_CSV = "on"
    delete_columns_with_only = 4
    delete_rows_with_only = 2
    outliner_precise = 2.0
    step_size = 1
    threads_amount = -1
    accepted_error = 50
    amount_of_tags = 25
    # Handle automatic operations
    handle_task("Deleting ceche", videosBP.delete_all_channels)
    handle_task("Searching for Youtube channels", channelsBP.search_for_youtube_channels, youtube_query, pages_number_channels, replace_channel)
    handle_task("Downloading video informations", videosBP.search_for_youtube_videos, pages_number_videos, replace_CSV)
    handle_task("Merging results", videosBP.concat_all_channels)
    handle_task("Cleaning data", cleanBP.clean_data, delete_columns_with_only, delete_rows_with_only, outliner_precise)
    handle_task("Checking accuracy", accuracyBP.check_for_accuracy, step_size, threads_amount, accepted_error)
    handle_task("Fetching tags", tagsBP.get_tags, amount_of_tags)
    handle_task("Generating timeline", timelineBP.generate_timeline)
    handle_task("Saveing results", favoritesBP.favorite_save_as, youtube_query)
    socketio.emit('finishedAll', namespace='/test')
    simple_lock.release()
