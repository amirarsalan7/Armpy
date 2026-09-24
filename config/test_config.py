from robot_config import RobotConfig

config = RobotConfig(
    "config/robot_joints.json"
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