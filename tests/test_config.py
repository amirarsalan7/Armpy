from pathlib import Path

from armpy.config.robot_config import RobotConfig


PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

ROBOT_CONFIG_FILE = (
    PROJECT_ROOT
    / "src"
    / "armpy"
    / "config"
    / "robot_joints.json"
)

config = RobotConfig(
    ROBOT_CONFIG_FILE
)

print(
    "Robot:",
    config.get_all_joints()
)

joints = config.get_all_joints()

for joint_name,data in joints.items():
    print()

    print(
        joint_name
        )

    print(
        data
    )    