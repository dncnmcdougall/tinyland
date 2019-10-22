const dgram = require('dgram');
const udpServer = dgram.createSocket('udp4');
var app = require('express')();
var http = require('http').createServer(app);
var io = require('socket.io')(http);

const udpPort   = 20001

udpServer.on('error', (err) => {
  console.log(`server error:\n${err.stack}`);
  udpServer.close();
});

udpServer.on('listening', () => {
  const address = udpServer.address();
  console.log(`UDP server listening at ${address.address}:${address.port}`);
});

udpServer.bind(udpPort);

app.get('/', function(req, res){
  res.sendFile(__dirname + '/index.html');
});

io.on('connection', function(socket){
  console.log('a browser connected');
  udpServer.on('message', (msgBuffer, rinfo) => {
    const msg = msgBuffer.toString()
    const msgArray = msg.split('/')
    const [type, name, x, y] = msgArray
    // console.log(`${type} : ${name} : ${x} : ${y}`);
    if (type === 'rectangle') {
      io.emit('update-thing', {
        type: 'rectangle',
        name,
        x,
        y,
      });
    }
  });
});

http.listen(3000, function(){
  console.log('listening on *:3000');
});

