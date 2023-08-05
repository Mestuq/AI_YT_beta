var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');

socket.on('connect', function() {
    console.log('Connected');
});

socket.on('error', function(error) {
    console.log('Socket error:', error);
});

socket.on('progress', function(msg) {
    console.log('Socket error:', msg.data);
    document.getElementById('progress').innerHTML = msg.data;
});

socket.on('finished', function() {
    window.history.back();
});

socket.on('disconnect', function() {
    console.log('Disconnected from the server');
});