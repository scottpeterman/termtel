// Initialize terminal with specific options
var term = new Terminal({
    allowProposedApi: true,
    scrollback: 1000,
    fontSize: 14,
    fontFamily: 'monospace',
    theme: {
        background: '#141414',
        foreground: '#ffffff'
    },
    cursorBlink: true
});

// Open terminal in the DOM
term.open(document.getElementById('terminal'));

// Initialize and load the fit addon
const fitAddon = new FitAddon.FitAddon();
term.loadAddon(fitAddon);

// Initial fit with slight delay to ensure proper rendering
setTimeout(() => {
    fitAddon.fit();
}, 0);

// Enable fit on the terminal whenever the window is resized
window.addEventListener('resize', () => {
    fitAddon.fit();
    try {
        size_dim = 'cols:' + term.cols + '::rows:' + term.rows;
        console.log("front end window resize event: " + size_dim);
        backend.set_pty_size(size_dim);
    } catch (error) {
        console.error(error);
        console.log("Channel may not be up yet!");
    }
});

// When data is entered into the terminal, send it to the backend
term.onData(e => {
    backend.write_data(e);
});

// Function to handle incoming data from the backend
window.handle_output = function(data) {
    term.write(data);
};

// Initialize terminal themes
const terminal_themes = {
    "Cyberpunk": {
        foreground: '#0affff',
        background: '#121212',
        cursor: '#0a8993'
    },
    "Dark": {
        foreground: '#ffffff',
        background: '#1e1e1e',
        cursor: '#ffffff'
    },
    "Light": {
        foreground: '#000000',
        background: '#ffffff',
        cursor: '#000000'
    },
    "Green": {
        foreground: '#00ff00',
        background: '#000000',
        cursor: '#00ff00'
    },
    "Amber": {
        foreground: '#ffb000',
        background: '#000000',
        cursor: '#ffb000'
    },
    "Neon": {
        foreground: '#ff00ff',
        background: '#000000',
        cursor: '#ff00ff'
    }
};

// Function to change terminal theme
window.changeTheme = function(themeName) {
    const theme = terminal_themes[themeName];
    if (theme) {
        term.setOption('theme', theme);
        
        // Update scrollbar style
        let scrollbarStyle = document.getElementById('terminal-scrollbar-style');
        if (!scrollbarStyle) {
            scrollbarStyle = document.createElement('style');
            scrollbarStyle.id = 'terminal-scrollbar-style';
            document.head.appendChild(scrollbarStyle);
        }

        scrollbarStyle.innerHTML = `
            .xterm-viewport::-webkit-scrollbar {
                width: 12px;
            }
            .xterm-viewport::-webkit-scrollbar-track {
                background: ${theme.background};
            }
            .xterm-viewport::-webkit-scrollbar-thumb {
                background: ${theme.foreground};
                opacity: 0.5;
            }
            .xterm-viewport::-webkit-scrollbar-thumb:hover {
                background: ${theme.cursor};
            }
        `;

        // Update body background color
        document.body.style.backgroundColor = themeName === 'Light' ? '#ffffff' : '#000000';
        
        // Ensure terminal fits properly after theme change
        fitAddon.fit();
    }
};

// Establish a connection with the Qt backend
new QWebChannel(qt.webChannelTransport, function(channel) {
    window.backend = channel.objects.backend;
});

// Window load event handler
window.onload = function() {
    term.focus();

    // Force a final fit after everything is loaded
    setTimeout(() => {
        fitAddon.fit();
    }, 100);
};