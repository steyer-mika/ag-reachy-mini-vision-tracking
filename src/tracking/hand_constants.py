# ==============================================================================
# Finger Landmark Indices
# ==============================================================================

# Fingertip landmarks (used for "finger raised" detection)
# Order: thumb, index, middle, ring, pinky
FINGER_TIPS = [4, 8, 12, 16, 20]

# Proximal Interphalangeal (PIP) joint landmarks
# These are compared against tips to determine if a finger is raised
# For thumb, we use the IP joint (index 2) since thumb anatomy differs
FINGER_PIPS = [2, 6, 10, 14, 18]

# ==============================================================================
# Hand Skeleton Connections
# ==============================================================================

# Defines how landmarks connect to form the hand skeleton visualization
# Each tuple is (start_landmark_index, end_landmark_index)
HAND_CONNECTIONS = [
    # Thumb - from wrist through all thumb joints
    (0, 1),  # Wrist to CMC
    (1, 2),  # CMC to MCP
    (2, 3),  # MCP to IP
    (3, 4),  # IP to TIP
    # Index finger - from wrist through all index joints
    (0, 5),  # Wrist to MCP
    (5, 6),  # MCP to PIP
    (6, 7),  # PIP to DIP
    (7, 8),  # DIP to TIP
    # Middle finger - from wrist through all middle joints
    (0, 9),  # Wrist to MCP
    (9, 10),  # MCP to PIP
    (10, 11),  # PIP to DIP
    (11, 12),  # DIP to TIP
    # Ring finger - from wrist through all ring joints
    (0, 13),  # Wrist to MCP
    (13, 14),  # MCP to PIP
    (14, 15),  # PIP to DIP
    (15, 16),  # DIP to TIP
    # Pinky - from wrist through all pinky joints
    (0, 17),  # Wrist to MCP
    (17, 18),  # MCP to PIP
    (18, 19),  # PIP to DIP
    (19, 20),  # DIP to TIP
    # Palm connections - connect the base of each finger
    # Creates the "palm" structure in visualization
    (5, 9),  # Index MCP to Middle MCP
    (9, 13),  # Middle MCP to Ring MCP
    (13, 17),  # Ring MCP to Pinky MCP
]

# ==============================================================================
# Constants
# ==============================================================================

LANDMARK_COLOR = (0, 255, 0)  # Green - hand joint markers
CONNECTION_COLOR = (255, 255, 255)  # White - skeleton lines
TEXT_COLOR = (0, 255, 0)  # Green - per-hand finger count
TOTAL_TEXT_COLOR = (255, 0, 0)  # Blue (BGR) - total finger count

LANDMARK_RADIUS = 5
CONNECTION_THICKNESS = 2
TEXT_THICKNESS = 2
