from tracking.hand_constants import FINGER_TIPS, FINGER_PIPS


def is_thumb_raised(hand_landmarks, handedness: str) -> bool:
    thumb_tip = hand_landmarks[FINGER_TIPS[0]]  # Index 4: thumb tip
    thumb_pip = hand_landmarks[FINGER_PIPS[0]]  # Index 2: thumb IP joint

    # Compare x-coordinates (horizontal position)
    # Remember: image is mirrored, so handedness labels are swapped visually
    if handedness == "Right":
        # Right hand: thumb tip should be to the LEFT of the IP joint
        return thumb_tip.x < thumb_pip.x
    else:
        # Left hand: thumb tip should be to the RIGHT of the IP joint
        return thumb_tip.x > thumb_pip.x


def is_finger_raised(hand_landmarks, finger_index: int) -> bool:
    tip = hand_landmarks[FINGER_TIPS[finger_index]]
    pip = hand_landmarks[FINGER_PIPS[finger_index]]

    # Smaller y value = higher position in image coordinates
    return tip.y < pip.y


def count_raised_fingers(hand_landmarks, handedness: str) -> int:
    count = 0

    # Check thumb separately (uses different detection logic)
    if is_thumb_raised(hand_landmarks, handedness):
        count += 1

    # Check the remaining four fingers (index=1, middle=2, ring=3, pinky=4)
    for i in range(1, 5):
        if is_finger_raised(hand_landmarks, i):
            count += 1

    return count
