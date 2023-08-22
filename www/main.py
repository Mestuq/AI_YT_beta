from app import app, socketio
from routes import indexBP, videosBP, channelsBP, cleanBP, tagsBP, accuracyBP, favoritesBP, simpleBP

app.register_blueprint(indexBP.index_bp)
app.register_blueprint(videosBP.videos_bp)
app.register_blueprint(channelsBP.channels_bp)
app.register_blueprint(cleanBP.clean_bp)
app.register_blueprint(tagsBP.tags_bp)
app.register_blueprint(accuracyBP.accuracy_bp)
app.register_blueprint(favoritesBP.favorites_bp)
app.register_blueprint(simpleBP.simple_bp)

if __name__ == '__main__':
    app.debug = True
    socketio.run(app, port=5000, debug=True, allow_unsafe_werkzeug=True, host='0.0.0.0')