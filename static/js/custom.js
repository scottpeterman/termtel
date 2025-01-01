// Initialize xterm.js
const term = new Terminal();
const fitAddon = new FitAddon.FitAddon();
term.loadAddon(fitAddon);
term.open(document.getElementById('terminal'));
fitAddon.fit();

// Initialize WebSocket connection
const socket = new WebSocket(
  `ws://${window.location.hostname}:${window.location.port}/terminal`
);

socket.addEventListener('open', function() {
  console.log('WebSocket connection opened.');

  // Send "sshconnect" message with SSH connection details
  socket.send(JSON.stringify({
    type: 'sshconnect',  // Changed from event to type
    hostname,
    port,
    username,
    password
  }));



    term.onData(data => {
     if (!initialResize) {
        initialResize = true;
        fitAddon.fit();
  const { cols, rows } = term;
  socket.send(JSON.stringify({ type: 'resize', cols, rows }));
    }
      socket.send(JSON.stringify({ type: 'input', data: btoa(data) }));  // Encoding to base64 if you're sending non-ASCII characters
    });

  term.onResize(({ cols, rows }) => {
    socket.send(JSON.stringify({ type: 'resize', cols, rows }));  // Changed from event to type
  });
});

socket.addEventListener('message', function(event) {
  const message = JSON.parse(event.data);

  if(message.type === 'ssh_output') {  // This should match the backend's output message type
  let decodedData = atob(message.data);
        term.write(decodedData);

  }

});

socket.onmessage = function(event) {
  const message = JSON.parse(event.data);

  if (message.type === 'ssh_connected') {
    // When the backend indicates the SSH session is ready,
    // send the current terminal size.
    const cols = terminal.cols;
    const rows = terminal.rows;
    socket.send(JSON.stringify({ type: 'resize', cols: cols, rows: rows }));
  }

  // Handle other message types...
};

socket.addEventListener('close', function() {
  console.log('WebSocket connection closed.');
});

socket.addEventListener('error', function(error) {
  console.log('WebSocket Error: ', error);
});

window.addEventListener('resize', () => {
  fitAddon.fit();
  const { cols, rows } = term;
  socket.send(JSON.stringify({ type: 'resize', cols, rows }));  // Changed from event to type
});
