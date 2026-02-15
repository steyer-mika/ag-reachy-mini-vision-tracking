let antennasEnabled = true;
let fingerCount = 0;
let ws = null;
let reconnectTimeout = null;

function connectWebSocket() {
  // Determine WebSocket URL based on current location
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('WebSocket connected');
    const cameraStatus = document.getElementById('camera-status');
    cameraStatus.textContent = 'active';
    cameraStatus.style.color = '#22c55e';
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);

      if (data.type === 'finger_count') {
        fingerCount = data.finger_count;
        updateFingerDisplay();
      }
    } catch (e) {
      console.error('Error parsing WebSocket message:', e);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    const cameraStatus = document.getElementById('camera-status');
    cameraStatus.textContent = 'error';
    cameraStatus.style.color = '#ef4444';
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected');
    const cameraStatus = document.getElementById('camera-status');
    cameraStatus.textContent = 'reconnecting...';
    cameraStatus.style.color = '#f59e0b';

    // Attempt to reconnect after 2 seconds
    reconnectTimeout = setTimeout(connectWebSocket, 2000);
  };
}

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

async function updateAntennasState(enabled) {
  try {
    const resp = await fetch('/antennas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled }),
    });
    const data = await resp.json();
    antennasEnabled = data.antennas_enabled;
    updateUI();
  } catch (e) {
    console.error('Backend error:', e);
    document.getElementById('antenna-status').textContent = 'error';
  }
}

async function playSound() {
  try {
    await fetch('/play_sound', { method: 'POST' });
  } catch (e) {
    console.error('Error triggering sound:', e);
  }
}

function updateFingerDisplay() {
  const fingerCountElement = document.querySelector('.finger-count');
  const fingerEmoji = document.querySelector('.finger-emoji');

  fingerCountElement.textContent = fingerCount;

  // Change emoji based on finger count
  const emojis = [
    '👊',
    '☝️',
    '✌️',
    '🤟',
    '🖖',
    '✋',
    '👐',
    '🙌',
    '👏',
    '🙏',
    '💪',
  ];
  if (fingerCount >= 0 && fingerCount < emojis.length) {
    fingerEmoji.textContent = emojis[fingerCount];
  }

  // Animate on change
  fingerCountElement.style.transform = 'scale(1.2)';
  setTimeout(() => {
    fingerCountElement.style.transform = 'scale(1)';
  }, 200);
}

function updateUI() {
  const checkbox = document.getElementById('antenna-checkbox');
  const antennaStatus = document.getElementById('antenna-status');

  checkbox.checked = antennasEnabled;

  if (antennasEnabled) {
    antennaStatus.textContent = 'running';
    antennaStatus.style.color = '#22c55e';
  } else {
    antennaStatus.textContent = 'stopped';
    antennaStatus.style.color = '#64748b';
  }
}

// Event listeners
document.getElementById('antenna-checkbox').addEventListener('change', (e) => {
  updateAntennasState(e.target.checked);
});

document.getElementById('sound-btn').addEventListener('click', () => {
  playSound();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    disconnectWebSocket();
  } else {
    connectWebSocket();
  }
});

// Initialize
updateUI();
connectWebSocket();

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  disconnectWebSocket();
});
