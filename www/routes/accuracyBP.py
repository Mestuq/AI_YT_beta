from flask import Blueprint,Flask,render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO
from app import app, socketio
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from threading import Thread, Lock
import pandas as pd
import csv, time

accuracy_bp = Blueprint('accuracy', __name__)
search_lock = Lock()

@accuracy_bp.route('/processCheckForAccuracy', methods=['POST'])
def process_check_for_accuracy():
    if not search_lock.acquire(blocking=False):
        return render_template('busy.html.j2')
    else:
        accept_error = request.form.get('AcceptError')
        socketio.start_background_task(check_for_accuracy,float(accept_error))
    return render_template('process.html.j2')

def check_for_accuracy(acceptError):
    time.sleep(1) # Waiting for client to load the website
    socketio.emit('progress', {'data': 'Loading data...'}, namespace='/test')
    # Loading data
    data = pd.read_csv('TrainingData.csv')
    Xval = data.iloc[:, :-1]
    yval = data.iloc[:, -1].values.ravel()
    try:
        # List of models
        models = {
            LogisticRegression(solver='lbfgs', max_iter=1000),
            RandomForestClassifier()
            }
        with open('Accuracy.csv', 'w', newline='') as csvFile:
            writer = csv.writer(csvFile)
            for modelNr,model in enumerate(models):
                loo = LeaveOneOut()
                within_range_count = 0
                try:
                    for trainIndex, testIndex in loo.split(Xval):
                        socketio.emit('progress', {'data': "Model "+str(modelNr+1)+" in 2 : element "+str(testIndex[0])+" / "+str(len(Xval))}, namespace='/test')
                        XTrain, XTest = Xval.values[trainIndex], Xval.values[testIndex]
                        yTrain, yTest = yval[trainIndex], yval[testIndex]
                        model.fit(XTrain, yTrain)
                        yPred = model.predict(XTest)[0]
                        if abs(yPred - yTest[0]) <= acceptError: # Check if the prediction falls within the acceptable error range
                            within_range_count += 1
                    within_range_percentage = (within_range_count / len(yval)) * 100
                    if modelNr == 0:
                        result = ["Linear Regression",within_range_percentage]
                    if modelNr == 1:
                        result = ["Random Forest",within_range_percentage]
                    writer.writerow(result)
                except Exception as e:
                    print(f"Error occurred: {e}")
                    socketio.emit('errorOccured',{'errorContent': str(e)}, namespace='/test')
        socketio.emit('finished', namespace='/test')
    except Exception as e:
        print(f"Error occurred: {e}")
        socketio.emit('errorOccured',{'errorContent': str(e)}, namespace='/test')
    search_lock.release()

