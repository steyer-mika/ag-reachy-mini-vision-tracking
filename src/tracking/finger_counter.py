from tracking.hand_constants import FINGER_TIPS, FINGER_PIPS


def is_thumb_raised(hand_landmarks, handedness: str) -> bool:
    # Check if thumb is extended.
    # Thumb logic is different from other fingers because it moves sideways.

    thumb_tip = hand_landmarks[FINGER_TIPS[0]]
    thumb_pip = hand_landmarks[FINGER_PIPS[0]]

    # Right hand: thumb extends to the left (tip.x < pip.x)
    # Left hand: thumb extends to the right (tip.x > pip.x)
    if handedness == "Right":
        return thumb_tip.x < thumb_pip.x
    else:
        return thumb_tip.x > thumb_pip.x


def is_finger_raised(hand_landmarks, finger_index: int) -> bool:
    # Check if a finger (not thumb) is extended.
    # A finger is raised when its tip is above its PIP joint.

    tip = hand_landmarks[FINGER_TIPS[finger_index]]
    pip = hand_landmarks[FINGER_PIPS[finger_index]]

    # In image coordinates, smaller y = higher up
    return tip.y < pip.y


def count_raised_fingers(hand_landmarks, handedness: str) -> int:
    # Count how many fingers are currently raised on a hand.

    count = 0

    # Check thumb separately (different logic)
    if is_thumb_raised(hand_landmarks, handedness):
        count += 1

    # Check the other four fingers (index, middle, ring, pinky)
    for i in range(1, 5):
        if is_finger_raised(hand_landmarks, i):
            count += 1

    return count
