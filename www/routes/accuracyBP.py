from flask import Blueprint,Flask,render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO
from app import app, socketio

from threading import Thread, Lock
import pandas as pd
import csv

from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import accuracy_score

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from imblearn.over_sampling import SMOTE

accuracy_bp = Blueprint('accuracy', __name__)
search_lock = Lock()

# SEARCH FOR ACCURACY MODEL
@app.route('/processCheckForAccuracy', methods=['POST'])
def processCheckForAccuracy():
    if not search_lock.acquire(blocking=False):
        return render_template('busy.html')
    else:
        AcceptError = request.form.get('AcceptError')
        socketio.start_background_task(CheckForAccuracy,AcceptError)
    return render_template('process.html')

def CheckForAccuracy(AcceptError):
    AcceptError = float(AcceptError)
    socketio.emit('Loading data...', namespace='/test')
    # LOAD DATA
    NewMerged_XY = pd.read_csv('TrainingData.csv')
    Xval = NewMerged_XY.iloc[:, :-1]
    yval = NewMerged_XY.iloc[:, -1].values.ravel()

    # Apply SMOTE for oversampling the minority class
    smote = SMOTE(random_state=42)
    Xval, yval = smote.fit_resample(Xval, yval)

    # LIST OF MODELS
    models = {LogisticRegression(),RandomForestClassifier()}
    with open('Accuracy.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        for modelNr,model in enumerate(models):

            # Initialize LOOCV
            loo = LeaveOneOut()

            # Counter for predictions within the acceptable error range
            within_range_count = 0

            # Perform LOOCV
            for train_index, test_index in loo.split(Xval):

                socketio.emit(str(modelNr)+" : "+str(test_index[0])+" / "+str(len(Xval)), namespace='/test')

                # print(str(test_index[0])+"/"+str(len(Xval)))

                X_train, X_test = Xval.values[train_index], Xval.values[test_index]
                y_train, y_test = yval[train_index], yval[test_index]

                # Train the model on the training data
                model.fit(X_train, y_train)

                # Make predictions on the test data
                y_pred = model.predict(X_test)[0]

                # Check if the prediction falls within the acceptable error range
                if abs(y_pred - y_test[0]) <= AcceptError:
                    within_range_count += 1

            # Calculate the percentage of predictions within the acceptable error range
            within_range_percentage = (within_range_count / len(yval)) * 100
            if modelNr == 0:
                result = ["Linear Regression",within_range_percentage]
            if modelNr == 1:
                result = ["Random Forest",within_range_percentage]
            writer.writerow(result)

    search_lock.release()
    socketio.emit('finished', namespace='/test')


#@socketio.on('downloadChannels', namespace='/test')
#def downloadChannels(query,number):
#    socketio.start_background_task(perform_task)

