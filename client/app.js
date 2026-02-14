// #############################################################################
//                           HTML Element References
// #############################################################################

const ELEMENT = {
  statusIcon: document.getElementById("status-icon"),
  statusText: document.getElementById("status-text"),
  fingerCount: document.getElementById("finger-count"),
  emoji: document.getElementById("emoji"),
  leftCount: document.getElementById("left-count"),
  rightCount: document.getElementById("right-count"),
  leftHand: document.getElementById("left-hand"),
  rightHand: document.getElementById("right-hand"),
  handsDetected: document.getElementById("hands-detected"),
  lastUpdate: document.getElementById("last-update"),
};

// #############################################################################
//                               Constants
// #############################################################################

const WS_URL = "ws://localhost:8765";

const EMOJIS = {
  0: "✊",
  1: "☝️",
  2: "✌️",
  3: "🤟",
  4: "🤘",
  5: "✋",
  6: "🙌",
  7: "👐",
  8: "🤲",
  9: "👏",
  10: "🙏",
};

// #############################################################################
//                               Render Logic
// #############################################################################

/**
 * Update the connection status display in the UI.
 * @param {string} status - The new connection status ("connected", "disconnected", "reconnecting").
 */
const updateConnectionStatus = (status) => {
  switch (status) {
    case "connected":
      ELEMENT.statusIcon.classList.remove("disconnected", "reconnecting");
      ELEMENT.statusIcon.classList.add("connected");
      ELEMENT.statusText.textContent = "Connected";
      break;
    case "disconnected":
      ELEMENT.statusIcon.classList.remove("connected", "reconnecting");
      ELEMENT.statusIcon.classList.add("disconnected");
      ELEMENT.statusText.textContent = "Disconnected";
      break;
    case "reconnecting":
      ELEMENT.statusIcon.classList.remove("connected", "disconnected");
      ELEMENT.statusIcon.classList.add("reconnecting");
      ELEMENT.statusText.textContent = "Reconnecting...";
      break;
  }
};

/**
 * Update the finger count display with animation and metadata.
 * @param {Object} data - The finger count data from the WebSocket.
 */
const updateFingerCount = (data) => {
  // Update total count with animation
  const total = data.total || 0;
  ELEMENT.fingerCount.textContent = total;
  ELEMENT.fingerCount.classList.add("pulse");
  setTimeout(() => ELEMENT.fingerCount.classList.remove("pulse"), 400);

  // Update emoji
  ELEMENT.emoji.textContent = EMOJIS[total] || "✋";

  // Update hands detected
  ELEMENT.handsDetected.textContent = data.hands_detected || 0;

  // Reset individual hands
  ELEMENT.leftCount.textContent = "-";
  ELEMENT.rightCount.textContent = "-";
  ELEMENT.leftHand.classList.remove("active");
  ELEMENT.rightHand.classList.remove("active");

  // Update individual hands if detected
  if (data.hands && data.hands.length > 0) {
    data.hands.forEach((hand) => {
      if (hand.handedness === "Left") {
        ELEMENT.leftCount.textContent = hand.fingers;
        ELEMENT.leftHand.classList.add("active");
      } else if (hand.handedness === "Right") {
        ELEMENT.rightCount.textContent = hand.fingers;
        ELEMENT.rightHand.classList.add("active");
      }
    });
  }

  // Update last update time
  const now = new Date();
  ELEMENT.lastUpdate.textContent = now.toLocaleTimeString();
};

// #############################################################################
//                               WebSocket Logic
// #############################################################################

/**
 * @type {WebSocket|null}
 */
let ws = null;

/**
 * @type {number|null}
 */
let reconnectInterval = null;

/**
 * Establish WebSocket connection to the server.
 */
const connect = () => {
  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    console.log("Connected to WebSocket server");
    updateConnectionStatus("connected");

    if (reconnectInterval) {
      clearInterval(reconnectInterval);
      reconnectInterval = null;
    }
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === "finger_count") {
        updateFingerCount(data);
      }
    } catch (error) {
      console.error("Error parsing message:", error);
    }
  };

  ws.onclose = () => {
    console.log("Disconnected from WebSocket server");
    updateConnectionStatus("disconnected");
    attemptReconnect();
  };

  ws.onerror = (error) => {
    console.error("WebSocket error:", error);
  };
};

/**
 * Attempt to reconnect to the WebSocket server.
 */
const attemptReconnect = () => {
  if (!reconnectInterval) {
    reconnectInterval = setInterval(() => {
      console.log("Attempting to reconnect...");
      updateConnectionStatus("reconnecting");
      connect();
    }, 3000);
  }
};

// #############################################################################
//                               Initialize
// #############################################################################

connect();
