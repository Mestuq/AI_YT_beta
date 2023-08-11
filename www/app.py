from flask import Blueprint,Flask,render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO

from engineio.async_drivers import threading

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")

