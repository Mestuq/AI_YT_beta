var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');

socket.on('connect', function() {
    console.log('Connected');
});

socket.on('error', function(error) {
    console.log('Socket error:', error);
});

socket.on('progress', function(msg) {
    document.getElementById('progress').innerHTML = msg.data;
});

socket.on('errorOccured', function(msg) {
    document.getElementById('errorContent').style.display = "block";
    document.getElementById('errorContent').innerHTML += msg.errorContent + "<br />";
});

socket.on('status', function(msg) {
    document.getElementById('status').innerHTML = msg.status;
    document.getElementById('progress').innerHTML = "";
});

const url = new URL(window.location.href);
const searchParams = url.searchParams;
const YoutubeQuery = searchParams.get('YoutubeQuery');

socket.on('finishedAll', function() {
    window.location.href = '/favorites?name='+encodeURIComponent(YoutubeQuery);
});

socket.on('disconnect', function() {
    console.log('Disconnected from the server');
});