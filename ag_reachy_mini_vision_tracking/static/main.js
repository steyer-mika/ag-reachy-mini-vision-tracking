let antennasEnabled = true;
let fingerCount = 0;
let pollInterval = null;

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

async function fetchFingerCount() {
  try {
    const resp = await fetch('/finger_count');
    const data = await resp.json();
    fingerCount = data.finger_count;
    updateFingerDisplay();

    // Update camera status
    const cameraStatus = document.getElementById('camera-status');
    if (cameraStatus.textContent === 'initializing...') {
      cameraStatus.textContent = 'active';
      cameraStatus.style.color = '#22c55e';
    }
  } catch (e) {
    console.error('Error fetching finger count:', e);
    const cameraStatus = document.getElementById('camera-status');
    cameraStatus.textContent = 'error';
    cameraStatus.style.color = '#ef4444';
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

// Start polling for finger count
function startPolling() {
  // Initial fetch
  fetchFingerCount();

  // Poll every 100ms for smooth updates
  pollInterval = setInterval(fetchFingerCount, 100);
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
}

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    stopPolling();
  } else {
    startPolling();
  }
});

// Initialize
updateUI();
startPolling();

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  stopPolling();
});
