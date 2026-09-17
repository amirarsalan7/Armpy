
class Joint:

    joint_count = 0

    def __init__(self, name, min_angle,max_angle):
        self.name = name
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.position = 0

        Joint.joint_count += 1


    def move_to(self, angle):

        if angle <self.min_angle or angle > self.max_angle:
            print("Angle is outside of range")
            return

        self.position = angle

        print(f"{self.name} joint moved to "
              f"{self.position} degrees."
              )

    def show_status(self):
        print(
            f"{self.name}:"
            f"position={self.position},"
            f"limits=[{self.min_angle},{self.max_angle}]"
        )