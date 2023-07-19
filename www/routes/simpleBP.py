from flask import Blueprint,Flask,render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO
from app import app, socketio

import pandas as pd
import scipy as sc
import numpy as np
from threading import Thread, Lock

from routes import accuracyBP,channelsBP,cleanBP,tagsBP,videosBP

simple_bp = Blueprint('simple', __name__)
search_lock = Lock()

# SEARCH FOR ACCURACY MODEL
@simple_bp.route('/processAll', methods=['POST'])
def processClean():
    if not search_lock.acquire(blocking=False):
        return render_template('busy.html')
    else:
        YoutubeQuery = request.form.get('YoutubeQuery')
        YourChannel = request.form.get('YourChannel')
        PagesNumberForQuerry = request.form.get('PagesNumberForQuerry')
        VideosNumberPerChannel = request.form.get('VideosNumberPerChannel')
        DeleteColumnsWithOnly = request.form.get('DeleteColumnsWithOnly')
        DeleteRowsWithOnly = request.form.get('DeleteRowsWithOnly')
        OutlinerPrecise = request.form.get('OutlinerPrecise')
        AcceptError = request.form.get('AcceptError')
        PrintAmountOfTags = request.form.get('PrintAmountOfTags')

        socketio.start_background_task(doAllTasks,YoutubeQuery,YourChannel,PagesNumberForQuerry,VideosNumberPerChannel,DeleteColumnsWithOnly,DeleteRowsWithOnly,OutlinerPrecise,AcceptError,PrintAmountOfTags)
    return render_template('process.html')

def doAllTasks(YoutubeQuery,YourChannel,PagesNumberForQuerry,VideosNumberPerChannel,DeleteColumnsWithOnly,DeleteRowsWithOnly,OutlinerPrecise,AcceptError,PrintAmountOfTags):
    channelsBP.searchForYoutubeChannels(YoutubeQuery,PagesNumberForQuerry)
    channelsBP.add(YourChannel)
    videosBP.searchForYoutubeVideos(VideosNumberPerChannel)
    cleanBP.Clean(DeleteColumnsWithOnly,DeleteRowsWithOnly,OutlinerPrecise)
    accuracyBP.CheckForAccuracy(AcceptError)
    tagsBP.GetTags(PrintAmountOfTags)