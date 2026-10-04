class Joint:

    def __init__(
        self,
        name,
        motors,
        zero_offset_deg=0.0,
        direction=1,
        gear_ratio=1.0,
        min_angle_deg=None,
        max_angle_deg=None
    ):
        self.name = name
        self.motors = motors

        self.zero_offset_deg = zero_offset_deg
        self.direction = direction
        self.gear_ratio = gear_ratio

        self.min_angle_deg = min_angle_deg
        self.max_angle_deg = max_angle_deg

        if len(self.motors)==0:

            raise ValueError(
                "Joint must have at least one motor."
            )

        if self.direction not in (-1, 1):
            raise ValueError(
                "Joint direction must be +1 or -1."
            )

        if self.gear_ratio <= 0:
            raise ValueError(
                "Gear ratio must be greater than zero."
            )

        if (
            self.min_angle_deg is not None
            and self.max_angle_deg is not None
            and self.min_angle_deg
            >= self.max_angle_deg
        ):
            raise ValueError(
                "Joint minimum angle must be "
                "smaller than maximum angle."
            )

    def motor_degrees_to_joint_angle(
        self,
        motor_angle_deg
    ):

        joint_angle_deg = (
            self.direction
            * (
                motor_angle_deg
                - self.zero_offset_deg
            )
            / self.gear_ratio
        )

        return joint_angle_deg

    def joint_angle_to_motor_degrees(
        self,
        joint_angle_deg
    ):

        motor_angle_deg = (
            self.zero_offset_deg
            + (
                self.direction
                * joint_angle_deg
                * self.gear_ratio
            )
        )

        return motor_angle_deg

    def read_angle_degrees(self):

        motor_angle_deg = (
            self.motor.read_present_position_degrees()
        )

        if motor_angle_deg is None:
            return None

        return self.motor_degrees_to_joint_angle(
            motor_angle_deg
        )

    def validate_joint_angle(
        self,
        joint_angle_deg
    ):

        if (
            self.min_angle_deg is not None
            and joint_angle_deg
            < self.min_angle_deg
        ):
            raise ValueError(
                f"Joint {self.name}: "
                f"angle {joint_angle_deg} "
                f"is below minimum "
                f"{self.min_angle_deg}."
            )

        if (
            self.max_angle_deg is not None
            and joint_angle_deg
            > self.max_angle_deg
        ):
            raise ValueError(
                f"Joint {self.name}: "
                f"angle {joint_angle_deg} "
                f"is above maximum "
                f"{self.max_angle_deg}."
            )

        return True

    def read_motor_angle(self):

        angles=[]

        for motor in self.motors:
            angle = (
                motor.read_present_position_degrees()
            )

            if angle is None:
                return None

            angle.append(angle)

        average_angle =(
            sum(angles)
            /
            len(angles)
        )
        return average_angle

    def read_state(self):

        motor_angle_deg = (
            self.motor.read_present_position_degrees()
        )

        if motor_angle_deg is None:
            joint_angle_deg = None

        else:
            joint_angle_deg = (
                self.motor_degrees_to_joint_angle(
                    motor_angle_deg
                )
            )

        return {
            "name": self.name,
            "motor_id": self.motor.motor_id,
            "motor_angle_deg": motor_angle_deg,
            "joint_angle_deg": joint_angle_deg,
            "min_angle_deg": self.min_angle_deg,
            "max_angle_deg": self.max_angle_deg,
        }