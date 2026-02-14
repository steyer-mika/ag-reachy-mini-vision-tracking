# Finger tip landmark indices (MediaPipe hand model)
FINGER_TIPS = [4, 8, 12, 16, 20]  # thumb, index, middle, ring, pinky

# Finger PIP joint indices (used to determine if finger is raised)
FINGER_PIPS = [2, 6, 10, 14, 18]

# Hand skeleton connections for drawing
# Each tuple is (start_landmark, end_landmark)
HAND_CONNECTIONS = [
    # Thumb
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    # Index finger
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    # Middle finger
    (0, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    # Ring finger
    (0, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    # Pinky
    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),
    # Palm connections
    (5, 9),
    (9, 13),
    (13, 17),
]

# Visual styling
LANDMARK_COLOR = (0, 255, 0)  # Green dots for joints
CONNECTION_COLOR = (255, 255, 255)  # White lines between joints
TEXT_COLOR = (0, 255, 0)  # Green text for per-hand count
TOTAL_TEXT_COLOR = (255, 0, 0)  # Blue text for total count

LANDMARK_RADIUS = 5
CONNECTION_THICKNESS = 2
TEXT_THICKNESS = 2
