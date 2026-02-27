// ===========================================================================
//                           Element References
// ===========================================================================

const ELEMENT = {
  statusIcon: document.getElementById('status-icon'),
  statusText: document.getElementById('status-text'),
  fingerCount: document.getElementById('finger-count'),
  emoji: document.getElementById('emoji'),
  leftCount: document.getElementById('left-count'),
  rightCount: document.getElementById('right-count'),
  leftHand: document.getElementById('left-hand'),
  rightHand: document.getElementById('right-hand'),
  handsDetected: document.getElementById('hands-detected'),
  lastUpdate: document.getElementById('last-update'),
  antennaCheckbox: document.getElementById('antenna-checkbox'),
  antennaStatus: document.getElementById('antenna-status'),
  cameraStatus: document.getElementById('camera-status'),
  soundBtn: document.getElementById('sound-btn'),
  btnUp: document.getElementById('btn-up'),
  btnDown: document.getElementById('btn-down'),
  btnLeft: document.getElementById('btn-left'),
  btnRight: document.getElementById('btn-right'),
};

// ===========================================================================
//                           Constants & State
// ===========================================================================

const EMOJIS = {
  0: '✊',
  1: '☝️',
  2: '✌️',
  3: '🤟',
  4: '🤘',
  5: '✋',
  6: '🙌',
  7: '👏',
  8: '🤲',
  9: '👐',
  10: '🙏',
};

// Keyboard to direction mapping (WASD and Arrow keys)
const KEY_MAP = {
  w: 'up',
  W: 'up',
  ArrowUp: 'up',
  s: 'down',
  S: 'down',
  ArrowDown: 'down',
  a: 'left',
  A: 'left',
  ArrowLeft: 'left',
  d: 'right',
  D: 'right',
  ArrowRight: 'right',
};

// Application state
let antennasEnabled = true;
let fingerCount = 0;
let ws = null;
let reconnectTimeout = null;
const pressedKeys = new Set();

// ===========================================================================
//                           WebSocket Management
// ===========================================================================

/**
 * Establish WebSocket connection to the server
 */
function connectWebSocket() {
  // Determine WebSocket URL based on current location
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('WebSocket connected');
    updateConnectionStatus('connected');
    updateCameraStatus('active');
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    } catch (e) {
      console.error('Error parsing WebSocket message:', e);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    updateCameraStatus('error');
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected');
    updateConnectionStatus('disconnected');
    updateCameraStatus('reconnecting');

    // Attempt to reconnect after 2 seconds
    reconnectTimeout = setTimeout(connectWebSocket, 2000);
  };
}

/**
 * Disconnect WebSocket and clear reconnect timeout
 */
function disconnectWebSocket() {
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout);
    reconnectTimeout = null;
  }

  if (ws) {
    ws.close();
    ws = null;
  }
}

/**
 * Handle incoming WebSocket messages
 */
function handleWebSocketMessage(data) {
  if (data.type === 'finger_count') {
    updateFingerCountDisplay(data);
  }
  // Add other message type handlers here if needed
}

// ===========================================================================
//                           UI Update Functions
// ===========================================================================

/**
 * Update the connection status indicator
 */
function updateConnectionStatus(status) {
  ELEMENT.statusIcon.classList.remove('connected', 'disconnected', 'reconnecting');
  
  switch (status) {
    case 'connected':
      ELEMENT.statusIcon.classList.add('connected');
      ELEMENT.statusText.textContent = 'Connected';
      break;
    case 'disconnected':
      ELEMENT.statusIcon.classList.add('disconnected');
      ELEMENT.statusText.textContent = 'Disconnected';
      break;
    case 'reconnecting':
      ELEMENT.statusIcon.classList.add('reconnecting');
      ELEMENT.statusText.textContent = 'Reconnecting...';
      break;
  }
}

/**
 * Update camera status display
 */
function updateCameraStatus(status) {
  ELEMENT.cameraStatus.className = 'info-value ' + status;
  
  switch (status) {
    case 'active':
      ELEMENT.cameraStatus.textContent = 'active';
      break;
    case 'error':
      ELEMENT.cameraStatus.textContent = 'error';
      break;
    case 'reconnecting':
      ELEMENT.cameraStatus.textContent = 'reconnecting...';
      break;
    default:
      ELEMENT.cameraStatus.textContent = status;
  }
}

/**
 * Update finger count display with animation
 */
function updateFingerCountDisplay(data) {
  const total = data.finger_count || 0;
  
  // Update total count with animation
  fingerCount = total;
  ELEMENT.fingerCount.textContent = total;
  ELEMENT.fingerCount.classList.add('pulse');
  setTimeout(() => ELEMENT.fingerCount.classList.remove('pulse'), 400);

  // Update emoji based on count
  ELEMENT.emoji.textContent = EMOJIS[total] || '✋';

  // Update hands detected count
  const handsDetected = data.hands_detected || 0;
  ELEMENT.handsDetected.textContent = handsDetected;

  // Reset individual hands display
  ELEMENT.leftCount.textContent = '-';
  ELEMENT.rightCount.textContent = '-';
  ELEMENT.leftHand.classList.remove('active');
  ELEMENT.rightHand.classList.remove('active');

  // Update individual hands if data available
  if (data.hands && data.hands.length > 0) {
    data.hands.forEach((hand) => {
      if (hand.handedness === 'Left') {
        ELEMENT.leftCount.textContent = hand.fingers;
        ELEMENT.leftHand.classList.add('active');
      } else if (hand.handedness === 'Right') {
        ELEMENT.rightCount.textContent = hand.fingers;
        ELEMENT.rightHand.classList.add('active');
      }
    });
  }

  // Update last update timestamp
  const now = new Date();
  ELEMENT.lastUpdate.textContent = now.toLocaleTimeString();
}

/**
 * Update antenna status display
 */
function updateAntennaStatusDisplay() {
  ELEMENT.antennaCheckbox.checked = antennasEnabled;
  ELEMENT.antennaStatus.className = 'info-value ' + (antennasEnabled ? 'running' : 'stopped');
  ELEMENT.antennaStatus.textContent = antennasEnabled ? 'running' : 'stopped';
}

// ===========================================================================
//                           API Interactions (POST)
// ===========================================================================

/**
 * Update antennas state via POST request
 */
async function updateAntennasState(enabled) {
  try {
    const resp = await fetch('/antennas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled }),
    });
    const data = await resp.json();
    antennasEnabled = data.antennas_enabled;
    updateAntennaStatusDisplay();
  } catch (e) {
    console.error('Error updating antennas:', e);
    ELEMENT.antennaStatus.textContent = 'error';
  }
}

/**
 * Request sound playback via POST request
 */
async function playSound() {
  try {
    await fetch('/play_sound', { method: 'POST' });
    console.log('Sound playback requested');
  } catch (e) {
    console.error('Error requesting sound:', e);
  }
}

/**
 * Send robot control command via POST request
 */
async function sendRobotControl(direction) {
  try {
    const resp = await fetch('/robot_control', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ direction }),
    });
    
    if (resp.ok) {
      console.log(`Robot control: ${direction}`);
    } else {
      console.warn(`Robot control failed: ${resp.status}`);
    }
  } catch (e) {
    console.error('Error sending robot control:', e);
  }
}

// ===========================================================================
//                           Robot Control Logic
// ===========================================================================

/**
 * Activate a control button visually
 */
function activateButton(direction) {
  const btn = ELEMENT[`btn${direction.charAt(0).toUpperCase() + direction.slice(1)}`];
  if (btn) {
    btn.classList.add('active');
  }
}

/**
 * Deactivate a control button visually
 */
function deactivateButton(direction) {
  const btn = ELEMENT[`btn${direction.charAt(0).toUpperCase() + direction.slice(1)}`];
  if (btn) {
    btn.classList.remove('active');
  }
}

// ===========================================================================
//                           Event Handlers
// ===========================================================================

/**
 * Setup all event listeners
 */
function setupEventListeners() {
  // Antenna checkbox
  ELEMENT.antennaCheckbox.addEventListener('change', (e) => {
    updateAntennasState(e.target.checked);
  });

  // Sound button
  ELEMENT.soundBtn.addEventListener('click', () => {
    playSound();
  });

  // Control button handlers
  const buttons = [ELEMENT.btnUp, ELEMENT.btnDown, ELEMENT.btnLeft, ELEMENT.btnRight];
  
  buttons.forEach((btn) => {
    if (btn) {
      const direction = btn.dataset.direction;
      
      // Mouse events
      btn.addEventListener('mousedown', () => {
        sendRobotControl(direction);
        btn.classList.add('active');
      });
      
      btn.addEventListener('mouseup', () => {
        btn.classList.remove('active');
      });
      
      btn.addEventListener('mouseleave', () => {
        btn.classList.remove('active');
      });
      
      // Touch events for mobile
      btn.addEventListener('touchstart', (e) => {
        e.preventDefault();
        sendRobotControl(direction);
        btn.classList.add('active');
      });
      
      btn.addEventListener('touchend', (e) => {
        e.preventDefault();
        btn.classList.remove('active');
      });
    }
  });

  // Keyboard events for robot control
  document.addEventListener('keydown', (event) => {
    const direction = KEY_MAP[event.key];
    if (direction && !pressedKeys.has(event.key)) {
      pressedKeys.add(event.key);
      event.preventDefault();
      sendRobotControl(direction);
      activateButton(direction);
    }
  });

  document.addEventListener('keyup', (event) => {
    const direction = KEY_MAP[event.key];
    if (direction) {
      pressedKeys.delete(event.key);
      deactivateButton(direction);
    }
  });

  // Handle page visibility changes
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      disconnectWebSocket();
    } else {
      connectWebSocket();
    }
  });

  // Cleanup on page unload
  window.addEventListener('beforeunload', () => {
    disconnectWebSocket();
  });
}

// ===========================================================================
//                           Initialization
// ===========================================================================

/**
 * Initialize the application
 */
function init() {
  console.log('Initializing Reachy Mini Vision Tracking...');
  
  // Setup all event listeners
  setupEventListeners();
  
  // Update initial UI state
  updateAntennaStatusDisplay();
  
  // Connect to WebSocket
  connectWebSocket();
  
  console.log('Initialization complete');
}

// Start the application when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
