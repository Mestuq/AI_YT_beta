from flask import Blueprint,Flask,render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO
from app import app, socketio
import pandas as pd
import scipy as sc
import numpy as np
from threading import Thread, Lock
import time
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from routes import videosBP

tags_bp = Blueprint('tags', __name__)
tags_lock = Lock()

@tags_bp.route('/processTags', methods=['POST'])
def process_get_tags():
    if not tags_lock.locked():
        return render_template('busy.html.j2')
    else:
        amount = request.form.get('Amount')
        socketio.start_background_task(get_tags,int(amount))
    return render_template('process.html.j2')

def get_tags(amount):
    time.sleep(1) # Waiting for client to load the website
    if not tags_lock.acquire(blocking=False):
        return
    data = pd.read_csv('TrainingData.csv')
    Xval = data.iloc[:, :-1]
    yval = data.iloc[:, -1].values.ravel()

    # Count the number of occurrences of each tag
    variable_counts = Xval.astype(bool).sum(axis=0).reset_index()
    variable_counts.columns = ['Variable', 'Count']

    # Logical regressions tags coefficients
    try:
        socketio.emit('progress', {'data':'Logistic Regression'}, namespace='/test')
        model = LogisticRegression(solver='lbfgs', max_iter=1000)
        model.fit(Xval, yval)
        coefficients = model.coef_[0]
        coefficients_df = pd.DataFrame({'Variable': Xval.columns, 'Coefficient': coefficients})
        coefficients_df = pd.merge(coefficients_df, variable_counts, on='Variable')
        coefficients_df = coefficients_df.sort_values(by='Coefficient', ascending=False)
        coefficients_df.head(amount).to_csv('LinearRegression.csv', encoding='utf-8', index=False)
    except Exception as e:
        print(f"Error occurred: {e}")
        socketio.emit('errorOccured',{'errorContent': str(e)}, namespace='/test')

    # Random forest tags importances
    try:
        socketio.emit('progress', {'data':'Random Forest Classifier'}, namespace='/test')
        model = RandomForestClassifier()
        model.fit(Xval, yval)
        feature_importances = model.feature_importances_
        feature_names = Xval.columns
        feature_df = pd.DataFrame({'Variable': feature_names, 'Importance': feature_importances})
        sorted_feature_df = feature_df.sort_values(by='Importance', ascending=False)
        top_k_feature_names = sorted_feature_df.head(amount)
        top_k_feature_names_pd = pd.DataFrame(top_k_feature_names)
        top_k_feature_names_pd = top_k_feature_names_pd.rename(columns={0: 'Variable'})
        top_k_feature_names_pd = pd.merge(top_k_feature_names_pd, variable_counts, on='Variable')
        top_k_feature_names_pd.to_csv('RandomForest.csv', encoding='utf-8', index=False)
    except Exception as e:
        print(f"Error occurred: {e}")
        socketio.emit('errorOccured',{'errorContent': str(e)}, namespace='/test')
    tags_lock.release()
    socketio.emit('finished', namespace='/test')
