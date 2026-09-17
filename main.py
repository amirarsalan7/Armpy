from robot import RobotArm
from joint import Joint


robot = RobotArm()


print("Number of joints:")
print(Joint.joint_count)


robot.show_status()


print("\nMoving robot...\n")


robot.move_shoulder(30)
robot.move_elbow(60)
robot.move_wrist(-20)


print("\nNew robot status:")

robot.show_status()