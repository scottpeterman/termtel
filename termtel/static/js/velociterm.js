const fitAddon = FitAddon.fitAddon; // or new Xterm.FitAddon();

let terminalInstances = {};
let session = {};
let resizeDebounceTimers = 500;
let resizeMessageSenders = {};

function findTerminal(tabUUID) {
  // Assuming terminalInstances is a global object where you store terminals
  const terminal = terminalInstances[tabUUID];

  if (!terminal) {
    console.error("Terminal not found for UUID:", tabUUID);
    return null;
  }

  // Return the terminal instance
  return terminal;
}

function findTabContent(tabUUID) {
  // Construct the tab content's ID using the UUID
  const tabContentId = "tab-" + tabUUID;

  // Find the tab content by ID
  const tabContent = document.getElementById(tabContentId);

  if (!tabContent) {
    console.error("Tab content not found for UUID:", tabUUID);
    return null;
  }

  // Return the tab content element
  return tabContent;
}

function findTab(tabUUID) {
  // Use the data attribute selector to find the tab button with the matching UUID
  const tabButton = document.querySelector(
    `.tab-button[data-tab-uuid="${tabUUID}"]`
  );
  if (!tabButton) {
    console.error("Tab not found:", tabUUID);
    return null;
  }

  // Find the corresponding tab content
  const tabContent = document.getElementById("tab-" + tabUUID);
  if (!tabContent) {
    console.error("Tab content not found:", tabUUID);
    return null;
  }

  // Return both the button and content of the tab
  return {
    button: tabButton,
    content: tabContent,
  };
}

// Function to add a new tab with terminal
function addTab(tabUUID, host, port, username, password, displayName) {
  const tabId = "tab-" + tabUUID;
  const terminalId = "terminal-" + host + ":" + port;

  // Create tab button
  const newTabButton = document.createElement("span");
  newTabButton.className = "tab-button"; // Use the class name from your CSS
  newTabButton.textContent = displayName || host; // Use displayName if available, else fallback to host
  newTabButton.setAttribute("data-tab-uuid", tabUUID);

  newTabButton.addEventListener("click", () => switchTab(tabUUID));

  document.getElementById("tab-buttons").appendChild(newTabButton);
  if (document.querySelectorAll(".tab-button").length === 1) {
    // If it's the first tab, make it active
    newTabButton.classList.add("active-button");
    newTabButton.classList.add("text-white");
    newTabButton.classList.remove("text-tab-inactive");
  }

  // Create tab content
  const newTabContent = document.createElement("div");
  newTabContent.className = "tab-content"; // Use the class name from your CSS
  newTabContent.id = tabId;
  newTabContent.style.height = "100%";

  // Create terminal container within tab content
  const terminalContainer = document.createElement("div");
  terminalContainer.className = "xterm";
  terminalContainer.id = terminalId;
  newTabContent.appendChild(terminalContainer);

  document.getElementById("tab-contents").appendChild(newTabContent);
  switchTab(tabUUID);
  // initializeTerminal(terminalId, tabUUID, newTabContent);
  setTimeout(() => {
    initializeTerminal(terminalId, tabUUID, terminalContainer);
  }, 1);
  setupWebSocketForTab(tabUUID, host, port, username, password);
}

function storeWebSocketInstance(tabUUID, socket) {
  if (!window.webSockets) {
    window.webSockets = {};
  }
  window.webSockets[tabUUID] = socket;
}

function switchTab(tabUUID) {
  // Find and switch to the tab content using the UUID
  const tabContent = findTabContent(tabUUID);
  const tabs = document.querySelectorAll(".tab-content");
  const tabButtons = document.querySelectorAll(".tab-button");

  // Hide all tab contents
  tabs.forEach((tab) => {
    tab.style.display = "none";
  });

  // Remove 'active-button' class from all tab buttons and add 'inactive' class
  tabButtons.forEach((button) => {
    button.classList.remove("active-button", "text-white");
    button.classList.add("text-tab-inactive");
  });

  // Show the current tab content and set the tab button to active
  if (tabContent) {
    tabContent.style.display = "block";
    const tabButton = document.querySelector(
      `.tab-button[data-tab-uuid="${tabUUID}"]`
    );
    if (tabButton) {
      tabButton.classList.add("active-button", "text-white");
      tabButton.classList.remove("text-tab-inactive");
    }
  }

  // Focus on the terminal within the newly activated tab
  const terminalInstance = findTerminal(tabUUID);
  if (terminalInstance) {
    terminalInstance.focus();
    // Additionally, you might want to call a fit or resize function here if available
    terminalInstance.fit();
  }
}

document
  .getElementById("tab-buttons")
  .addEventListener("click", function (event) {
    const tabUUID = event.target.getAttribute("data-tab-uuid");
    if (tabUUID) {
      switchTab(tabUUID);
    }
  });

// Accordion toggle
document.querySelectorAll(".accordion-header").forEach((button) => {
  button.addEventListener("click", () => {
    const accordionContent = button.nextElementSibling;
    accordionContent.classList.toggle("hidden");
  });
});

document.addEventListener("DOMContentLoaded", function () {
  const tabButtons = document.getElementById("tab-buttons");

  tabButtons.addEventListener("contextmenu", function (event) {
    event.preventDefault();
    const target = event.target.closest(".tab-button");
    const tabUUID = target.getAttribute("data-tab-uuid");

    if (tabUUID) {
      const contextMenu = document.getElementById("tabContextMenu");
      contextMenu.style.top = `${event.pageY}px`;
      contextMenu.style.left = `${event.pageX}px`;
      contextMenu.classList.remove("hidden");
      contextMenu.setAttribute("data-tab-uuid", tabUUID); // Set the UUID here
    }
  });

  // Hide context menu on clicking elsewhere
  document.addEventListener("click", function (event) {
    const contextMenu = document.getElementById("tabContextMenu");
    if (!contextMenu.contains(event.target)) {
      contextMenu.classList.add("hidden");
    }
  });
  document.getElementById("closeTab").addEventListener("click", function () {
    const contextMenu = document.getElementById("tabContextMenu");
    const tabUUID = contextMenu.getAttribute("data-tab-uuid");
    closeTabFunction(tabUUID); // Your function to close the tab
    contextMenu.classList.add("hidden");
  });

  // Prevent the default context menu on your custom menu
  document
    .getElementById("tabContextMenu")
    .addEventListener("contextmenu", function (event) {
      event.preventDefault();
    });
});

function closeTabFunction(tabUUID) {
  // Function to close the tab
  const tabButton = document.querySelector(
    `.tab-button[data-tab-uuid="${tabUUID}"]`
  );
  const tabContent = document.getElementById(`tab-${tabUUID}`);

  // Remove the elements from the document
  if (tabButton) {
    tabButton.remove();
  }
  if (tabContent) {
    tabContent.remove();
  }
  // Check if there are any tabs left and if so, switch to the first one
  const remainingTabs = document.querySelectorAll(".tab-button");
  if (remainingTabs.length > 0) {
    // Get the UUID of the first remaining tab
    const firstTabUUID = remainingTabs[0].getAttribute("data-tab-uuid");
    // Switch to the first tab
    switchTab(firstTabUUID);
  }
  // Hide the context menu after closing the tab
  const contextMenu = document.getElementById("tabContextMenu");
  if (contextMenu) {
    contextMenu.classList.add("hidden");
  }
}

// Bind event handler for the close tab context menu item
document.getElementById("closeTab").addEventListener("click", function (event) {
  // Stop event from bubbling up
  event.stopPropagation();

  const contextMenu = document.getElementById("tabContextMenu");
  const tabUUID = contextMenu.getAttribute("data-tab-uuid");
  console.log("Closing tab: " + tabUUID);
  if (tabUUID) {
    closeTabFunction(tabUUID); // Close the tab
  }

  // Hide the context menu
  contextMenu.classList.add("hidden");
});
//document
//  .querySelector(".search-input")
//  .addEventListener("input", function (event) {
//    const query = event.target.value;
//    if (query.length >= 3) {
//      fetch(`/search?query=${encodeURIComponent(query)}`)
//        .then((response) => response.json())
//        .then((data) => displaySearchResults(data))
//        .catch((error) => console.error("Error:", error));
//    }
//  });

function displaySearchResults(results) {
  const tableBody = document.querySelector("#search-results-table tbody");
  tableBody.innerHTML = ""; // Clear existing results

  results.forEach((session) => {
    const row = tableBody.insertRow();

    // Add a cell for session details
    const detailsCell = row.insertCell(0);
    detailsCell.textContent = `${session.display_name} - ${session.host} - ${session.Model}`;

    // Add a cell for the connect button
    const connectCell = row.insertCell(1);
    const connectButton = document.createElement("button");
    connectButton.textContent = "Connect";
    connectButton.className = "connect-btn";
    connectButton.onclick = () => {
      hideSearchModal();
      showCredentialsModal(session);
    };
    connectCell.appendChild(connectButton);
  });

  showSearchModal();
}

function showSearchModal() {
  document.getElementById("searchModal").style.display = "block";
}

function hideSearchModal() {
  const searchModal = document.getElementById("searchModal");
  if (searchModal) {
    searchModal.style.display = "none";
  }
}

const credentialsForm = document.getElementById("credentials-form");
credentialsForm.onsubmit = function (e) {
  e.preventDefault(); // Prevent the default form submission

  // Retrieve the credentials from the form
  const username = document.getElementById("ssh-username").value;
  const password = document.getElementById("ssh-password").value;
  const tabUUID = document.getElementById("ssh-tab-uuid").value;
  const host = document.getElementById("ssh-host").value;
  const port = document.getElementById("ssh-port").value;
  const displayName = document.getElementById("ssh-display-name").value; // Retrieve the display name
  // alert(displayName);

  // Call addTab with all necessary information
  addTab(tabUUID, host, port, username, password, displayName);

  // Find and switch to the new tab content after it's created
  const tabContent = findTabContent(tabUUID);
  if (tabContent) {
    switchTab(tabUUID);
  }

  hideCredentialsModal();
};

function showCredentialsModal(session) {
  const newTabUUID = generateUUID(); // Generate a new UUID for the new tab

  // Populate the credentials form with the session data
  document.getElementById("ssh-host").value = session.host;
  document.getElementById("ssh-port").value = session.port;
  document.getElementById("ssh-tab-uuid").value = newTabUUID;
  document.getElementById("credentialsModal").style.display = "block";
}

document.getElementById("hamburger").addEventListener("click", function () {
  var sidebar = document.querySelector(".sidebar");
  var mainContent = document.querySelector(".main-content");

  // Toggle the 'closed' class on the sidebar
  sidebar.classList.toggle("closed");

  if (sidebar.classList.contains("closed")) {
    // If the sidebar is closed, let main content take all available space
    mainContent.style.flex = "1 1 100%";
    sidebar.style.width = "0";
  } else {
    // When the sidebar is open, reset the flex property
    mainContent.style.flex = "";
    sidebar.style.width = "";
  }
});

// Debounce function to limit the frequency of resize calls
function debounce(func, wait) {
  let timeout;

  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };

    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}


function generateUUID() {
  return crypto.randomUUID();
}



function debounceSocket(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

// Terminal Initialization Function
function initializeTerminal(terminalContainerId, tabUUID, dump) {
  let terminalContainer = document.getElementById(terminalContainerId);
  terminalContainer = dump;
  terminalContainer.style.height = "100%"; // Ensure the terminal fills its container

  if (!terminalContainer) return;

  // Create a new Terminal instance
  let term = new Terminal();
  let fitAddon = new FitAddon.FitAddon();
  terminalInstances[tabUUID] = term;

  term.loadAddon(fitAddon);
  fitAddon.fit();
  term.terminalContainer = terminalContainer;
  term.open(terminalContainer);

  // Create a debounced function for sending the resize message
  resizeMessageSenders[tabUUID] = debounceSocket((cols, rows) => {
    console.log("Resizing terminal for tabUUID:", tabUUID, "cols:", cols, "rows:", rows);
    const socket = window.webSockets[tabUUID];
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "resize", cols, rows }));
    }
  }, 500); // Debounce delay in milliseconds

  term.onResize(({ cols, rows }) => {
    // Use the debounced function to send the resize message
    resizeMessageSenders[tabUUID](cols, rows);
  });

  term.onData((data) => {
    // Retrieve the WebSocket instance for this tabUUID
    const socket = window.webSockets[tabUUID];
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "input", data: data }));
    }
  });

  const observer = new ResizeObserver(() => {
    if (terminalContainer.offsetWidth > 0 && terminalContainer.offsetHeight > 0) {
      fitAddon.fit();
    }
  });
  observer.observe(terminalContainer);
}

function setupWebSocketForTab(tabUUID, host, port, username, password) {
  console.log("Setting up websocket for tab...");
  const socket = new WebSocket(
    `ws://${window.location.hostname}:${window.location.port}/ws/terminal/${tabUUID}`
  );
  console.log(
    "socket info:\n" + tabUUID + "\n",
    host + "\n",
    port + "\n",
    username + "\n",
    password + "\n"
  );
  setupWebSocketListeners(socket, tabUUID);

  socket.onopen = () => {
    // Send the connect message when the WebSocket connection is established
    socket.send(
      JSON.stringify({
        type: "connect",
        hostname: host,
        port: port,
        username: username,
        password: password,
      })
    );
  };

  // Store the WebSocket instance
  storeWebSocketInstance(tabUUID, socket);
}

function setupWebSocketListeners(socket, tabUUID) {
  socket.addEventListener("message", function (event) {
    try {
      let terminal = terminalInstances[tabUUID];
      if (!terminal) {
        console.error("Terminal instance not found for UUID:", tabUUID);
        return;
      }
      const message = JSON.parse(event.data);
      if (message.type === "ssh_output" && message.tabId === tabUUID) {
        terminal.write(atob(message.data));
      }
    } catch (e) {
      console.error("Error in WebSocket message event: ", e);
    }
  });

  // Add other event listeners for 'open', 'close', 'error', etc. as needed

  // ... other event listeners ...
}

//     function storeWebSocketInstance(tabUUID, socket) {
//     // Example: Storing the WebSocket instance in a global object
//     if (!window.webSockets) {
//     window.webSockets = {};
// }
//     window.webSockets[tabUUID] = socket;
// }

document
  .getElementById("quick-connect-form")
  .addEventListener("submit", function (event) {
    event.preventDefault();

    // Generate a unique ID for the new tab
    const tabUUID = generateUUID();

    // Get form values
    const host = document.getElementById("host").value;
    const port = document.getElementById("port").value;
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const display_name = document.getElementById("ssh-display-name").value;

    // Create a new tab with the unique ID and SSH connection details
    addTab(tabUUID, host, port, username, password, host);
  });

let resizeTimeout = 1;

const debouncedResizeTerminal = debounce((activeTabUUID) => {
  let activeTerminal = terminalInstances[activeTabUUID];
  if (activeTerminal) {
    let terminalContainer = activeTerminal.terminalContainer;
    terminalContainer.style.height = "100%";

    const fitAddon = new FitAddon.FitAddon();
    activeTerminal.loadAddon(fitAddon);
    fitAddon.fit();
  }
}, 500); // Debounce for 500 milliseconds
function handleWindowResize(activeTabUUID) {
  const activeTerminal = terminalInstances[activeTabUUID];
  if (activeTerminal) {
    let terminalContainer = activeTerminal.terminalContainer;

    // // Force a reflow/repaint
    // terminalContainer.style.height = 'auto'; // Temporarily reset to auto
    // terminalContainer.offsetHeight; // Read offsetHeight to force reflow
    // terminalContainer.style.height = '100%'; // Set back to 100%
  }
  debouncedResizeTerminal(activeTabUUID);
}

function hideCredentialsModal() {
  const modal = document.getElementById("credentialsModal");
  if (modal) {
    modal.style.display = "none"; // Hides the modal by changing its display style
  }
}


// Attach the handleWindowResize function to the window resize event
window.addEventListener("resize", () => {
  const activeTabButton = document.querySelector('.tab-button.active-button');
  const activeTabUUID = activeTabButton.getAttribute('data-tab-uuid');
  handleWindowResize(activeTabUUID);
});
document.addEventListener("DOMContentLoaded", function () {
  // Attach click event listeners to session items
  document.querySelectorAll(".session-item").forEach((item) => {
    item.addEventListener("click", function () {
      // Retrieve and parse the session data
      console.log("button session info: " + this.dataset.session);
      const sessionData = JSON.parse(this.dataset.session);
      // Use the session data to open a new SSH tab
      openNewSshTab(sessionData);
    });
  });
  let closeButton = document.querySelector(".close-button");
  if (closeButton) {
    closeButton.addEventListener("click", function () {
      // Clear the form
      // document.getElementById('ssh-username').value = '';
      // document.getElementById('ssh-password').value = '';
      // document.getElementById('ssh-host').value = '';
      // document.getElementById('ssh-port').value = '';
      // document.getElementById('ssh-tab-uuid').value = '';  // Corrected ID

      let modal = document.getElementById("credentialsModal");
      modal.style.display = "none";
    });
  }
});

function openNewSshTab(sessionData) {
  // Store session data for later use
  const tabUUID = generateUUID();
  document.getElementById("ssh-host").value = sessionData.host;
  document.getElementById("ssh-display-name").value = sessionData.displayName;
  document.getElementById("ssh-port").value = sessionData.port;
  document.getElementById("ssh-tab-uuid").value = tabUUID; // Store tab UUID
  session[tabUUID] = sessionData;
  console.log(session);
  // alert("openNewSshTab: " + sessionData.display_name);
  // Show the modal for credential input
  showModal(sessionData, tabUUID);
}

function showModal(sessionData, tabUUID) {
  document.getElementById("credentialsModal").style.display = "block";
  // alert(JSON.stringify(sessionData));
  console.log("tabUUID: " + tabUUID);
  sshFormElementUUID = document.getElementById("ssh-tab-uuid");
  document.getElementById("ssh-display-name").value = sessionData.display_name;
  sshFormElementUUID.value = tabUUID;
  console.log(document.getElementById("ssh-tab-uuid").value);
}

function hideModal() {
  document.getElementById("credentialsModal").style.display = "";
}

document
  .getElementById("credentials-form")
  .addEventListener("submit", function (event) {
    event.preventDefault();

    // Retrieve credentials and session details from the form
    const username = document.getElementById("ssh-username").value;
    const password = document.getElementById("ssh-password").value;
    const host = document.getElementById("ssh-host").value;
    const port = document.getElementById("ssh-port").value;
    const tabUUID = document.getElementById("ssh-tab-uuid").value;

    // Clear the password field for security reasons
    // document.getElementById('ssh-password').value = '';

    // Add a new tab for the SSH connection
    // addTab(tabUUID, host, port, username, password);

    // Set up the WebSocket for the SSH connection
    setupWebSocketForTab(tabUUID, host, port, username, password);

    // Close the modal after the form is submitted
    hideModal();
  });

document.getElementById('search-button').addEventListener('click', function(event) {
    event.preventDefault();

    const query = document.getElementById('search-query').value;
    const useNetBox = document.getElementById('netbox-search').checked;

    let searchUrl = '/search?query=' + encodeURIComponent(query);

    if (useNetBox) {
        searchUrl = '/search-netbox?query=' + encodeURIComponent(query);
    }

    // Perform the search using the selected endpoint
    fetch(searchUrl)
        .then(response => response.json())
        .then(data => {
            console.log("Received JSON response:", data);  // Log the JSON response to the console
            displaySearchResults(data);  // Display the results
        })
        .catch(error => console.error('Error:', error));
});
