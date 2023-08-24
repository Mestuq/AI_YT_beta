from flask import Blueprint,Flask,render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO
from app import app, socketio
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import accuracy_score, mean_squared_error
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from threading import Thread, Lock
from joblib import Parallel, delayed
import pandas as pd
import csv, time
import numpy as np

accuracy_bp = Blueprint('accuracy', __name__)
accuracy_lock = Lock()

def parallel_loocv(model, X, y, train_index, test_index, max_splits, accepted_error, step_size, model_nr):
    if test_index % step_size != 0:  # Consider only every second iteration
        return None, None
    socketio.emit('progress', {'data': "Progress: ("+str(model_nr+1)+"/2) "+str(test_index[0])+"/"+str(max_splits)}, namespace='/test')
    clf = model.__class__()
    X_train, X_test = X.values[train_index], X.values[test_index]
    y_train, y_test = y[train_index], y[test_index]
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    accuracy = mean_squared_error(y_test, y_pred)
    in_valid_error = 0.0
    if abs(y_test - y_pred) <= accepted_error: # Check if the prediction falls within the acceptable error range
        in_valid_error = 1.0
    return accuracy, in_valid_error

@accuracy_bp.route('/processCheckForAccuracy', methods=['POST'])
def process_check_for_accuracy():
    if accuracy_lock.locked():
        return render_template('busy.html.j2')
    else:
        step_size = request.form.get('StepSize')
        threads_amount = request.form.get('ThreadsAmount')
        accepted_error = request.form.get('AcceptedError')
        socketio.start_background_task(check_for_accuracy,int(step_size),int(threads_amount),int(accepted_error))
    return render_template('process.html.j2')

def check_for_accuracy(step_size, threads_amount, accepted_error):
    if not accuracy_lock.acquire(blocking=False):
        return
    time.sleep(1) # Waiting for client to load the website
    socketio.emit('progress', {'data': 'Loading data...'}, namespace='/test')
    # Loading data
    loo = LeaveOneOut()
    data = pd.read_csv('TrainingData.csv')
    data = data.sample(frac=1)  # Shuffles all rows
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
            writer.writerow([" ","MSE","Accuracy"])
            for model_nr,model in enumerate(models):

                max_splits = loo.get_n_splits(Xval)
                result = Parallel(n_jobs=threads_amount, pre_dispatch="all", backend="threading")(
                    delayed(parallel_loocv)(model, Xval,yval, train_index, test_index, max_splits, accepted_error, step_size, model_nr) for train_index, test_index in loo.split(Xval)
                )
                mse = [item[0] for item in result if item[0] is not None]
                average_mse = int(sum(mse)/len(mse))
                accuracy = [item[1] for item in result if item[1] is not None]
                average_accuracy = round(sum(accuracy)/len(accuracy) * 100,2)
                if model_nr == 0:
                    result = ["Linear Regression",average_mse, str(average_accuracy)+"%"]
                if model_nr == 1:
                    result = ["Random Forest",average_mse, str(average_accuracy)+"%"]
                writer.writerow(result)
        socketio.emit('finished', namespace='/test')
    except Exception as e:
        print(f"Error occurred: {e}")
        socketio.emit('errorOccured',{'errorContent': str(e)}, namespace='/test')
    accuracy_lock.release()
