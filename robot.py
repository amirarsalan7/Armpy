from joint import Joint


class RobotArm:

    def __init__(self):

        self.shoulder = Joint(
            name="shoulder",
            min_angle=-90,
            max_angle=90
        )

        self.elbow = Joint(
            name="elbow",
            min_angle=0,
            max_angle=135
        )

        self.wrist = Joint(
            name="wrist",
            min_angle=-80,
            max_angle=80
        )

    def move_shoulder(self, angle):
        self.shoulder.move_to(angle)

    def move_elbow(self, angle):
        self.elbow.move_to(angle)

    def move_wrist(self, angle):
        self.wrist.move_to(angle)

    def show_status(self):
        print("Robot status:")

        self.shoulder.show_status()
        self.elbow.show_status()
        self.wrist.show_status()