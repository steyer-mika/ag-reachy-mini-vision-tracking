from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

with ReachyMini() as mini:
    print("Connected!")

    mini.goto_target(
        head=create_head_pose(z=20, roll=10, mm=True, degrees=True), duration=1.0
    )

    mini.goto_target(
        head=create_head_pose(z=20, roll=-10, mm=True, degrees=True),
        duration=1.0,
    )
