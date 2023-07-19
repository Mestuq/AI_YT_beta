from flask import Blueprint,Flask,render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO
from app import app, socketio

import pandas as pd
import scipy as sc
import numpy as np
from threading import Thread, Lock

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from imblearn.over_sampling import SMOTE

from routes import videosBP

tags_bp = Blueprint('tags', __name__)
search_lock = Lock()

# SEARCH FOR ACCURACY MODEL
@tags_bp.route('/processTags', methods=['POST'])
def processGetTags():
    if not search_lock.acquire(blocking=False):
        return render_template('busy.html')
    else:
        Amount = request.form.get('Amount')
        socketio.start_background_task(GetTags,Amount)
    return render_template('process.html')

def GetTags(Amount):
    Amount = int(Amount)

    socketio.emit('Please wait...', namespace='/test')

    # LOAD DATA
    NewMerged_XY = pd.read_csv('TrainingData.csv')

    Xval = NewMerged_XY.iloc[:, :-1]
    yval = NewMerged_XY.iloc[:, -1].values.ravel()

    # ----- COUNTING APPERIANCES FOR BETTER PREVIEW
    # Count the number of occurrences of each variable in X
    variable_counts = Xval.astype(bool).sum(axis=0).reset_index()
    variable_counts.columns = ['Variable', 'Count']

    # Apply SMOTE for oversampling the minority class
    smote = SMOTE(random_state=42)
    Xval, yval = smote.fit_resample(Xval, yval)

    # LOGICAL REGRESSION -------------------------------------------------------------

    # LOGICAL REGRESSIONS TAGS COEFFICIENTS
    model = LogisticRegression()
    model.fit(Xval, yval)

    # Retrieve the coefficients from the trained model
    coefficients = model.coef_[0]

    # Create a DataFrame to store the variable names and coefficients
    coefficients_df = pd.DataFrame({'Variable': Xval.columns, 'Coefficient': coefficients})

    # Merge the variable counts with the coefficients DataFrame
    coefficients_df = pd.merge(coefficients_df, variable_counts, on='Variable')

    # Sort the coefficients by magnitude
    coefficients_df = coefficients_df.sort_values(by='Coefficient', ascending=False)

    # Save result
    coefficients_df.head(Amount).to_csv('LinearRegression.csv', encoding='utf-8', index=False)

    # RANDOM FOREST -------------------------------------------------------------

    # Create a random forest classifier
    model = RandomForestClassifier()
    model.fit(Xval, yval)

    # Get feature importances
    feature_importances = model.feature_importances_
    feature_names = Xval.columns
    top_k_indices = np.argsort(feature_importances)[-Amount:]
    top_k_feature_names = [feature_names[i] for i in top_k_indices]


    # ----- COUNTING APPERIANCES FOR BETTER PREVIEW
    top_k_feature_names_pd = pd.DataFrame(top_k_feature_names)
    top_k_feature_names_pd = top_k_feature_names_pd.rename(columns={0: 'Variable'})

    # CONNECT WITH COUNTING
    top_k_feature_names_pd = pd.merge(top_k_feature_names_pd, variable_counts, on='Variable')
    

    # Save results
    top_k_feature_names_pd.to_csv('RandomForest.csv', encoding='utf-8', index=False)

    # ------------------------------------------------------------------------------

    # FINISHING PROCESS
    search_lock.release()
    socketio.emit('finished', namespace='/test')
