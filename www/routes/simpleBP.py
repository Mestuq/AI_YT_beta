
from flask import Blueprint,Flask,render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO
from app import app, socketio
from threading import Thread, Lock
import time

simple_bp = Blueprint('simple', __name__)
search_lock = Lock()

@simple_bp.route('/processAll')
def process_all():
    return render_template('./processAll.html.j2')