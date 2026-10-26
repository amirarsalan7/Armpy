class Robot:

    def __init__(self, name, motors, joints, gripper):

        self.name = name
        self.motors = motors
        self.joints = joints
        self.gripper = gripper

        self._validate_components()


    def _validate_components(self):

        if not isinstance(self.name, str) or not self.name:
            raise ValueError(
                "Robot name must be a non-empty string."
            )

        if not self.motors:
            raise ValueError(
                f"{self.name} must contain motors."
            )

        if not self.joints:
            raise ValueError(
                f"{self.name} must contain joints."
            )

        for joint_key, joint in self.joints.items():

            for motor_id, motor in joint.motors.items():

                if motor_id not in self.motors:
                    raise ValueError(
                        f"{joint_key}: Motor {motor_id} "
                        "does not exist in Robot motors."
                    )

                if self.motors[motor_id] is not motor:
                    raise ValueError(
                        f"{joint_key}: Motor {motor_id} "
                        "object does not match Robot motor object."
                    )

        if not isinstance(self.gripper, dict):
            raise ValueError(
                "Gripper components are invalid."
            )

        gripper_motor = self.gripper.get("motor")

        if gripper_motor is None:
            raise ValueError(
                "Gripper motor is missing."
            )

        gripper_motor_id = str(
            gripper_motor.motor_id
        )

        if gripper_motor_id not in self.motors:
            raise ValueError(
                f"Gripper Motor {gripper_motor_id} "
                "does not exist in Robot motors."
            )

        if self.motors[gripper_motor_id] is not gripper_motor:
            raise ValueError(
                "Gripper motor object does not match Robot motor object."
            )

        return True


    def get_joint(self, joint_key):

        if joint_key not in self.joints:
            raise ValueError(
                f"Joint {joint_key} does not exist."
            )

        return self.joints[joint_key]


    def get_motor(self, motor_id):

        motor_id = str(motor_id)

        if motor_id not in self.motors:
            raise ValueError(
                f"Motor {motor_id} does not exist."
            )

        return self.motors[motor_id]


    def get_joint_names(self):

        return list(self.joints)


    def read_joint_raw_positions(self, joint_key):

        joint = self.get_joint(joint_key)

        positions = {}

        for motor_id, motor in joint.motors.items():

            position = motor.read_present_position_raw()

            if position is None:
                raise RuntimeError(
                    f"Could not read position from Motor {motor_id}."
                )

            positions[motor_id] = position

        return positions


    def read_joint_angle(self, joint_key):

        joint = self.get_joint(joint_key)

        raw_positions = self.read_joint_raw_positions(
            joint_key
        )

        return joint.calculate_joint_angle(
            raw_positions
        )


    def read_all_joint_angles(self):

        angles = {}

        for joint_key in self.joints:

            angles[joint_key] = self.read_joint_angle(
                joint_key
            )

        return angles


    def read_gripper_raw_position(self):

        motor = self.gripper["motor"]

        position = motor.read_present_position_raw()

        if position is None:
            raise RuntimeError(
                "Could not read gripper position."
            )

        return position


    def read_state(self):

        joint_states = {}

        for joint_key, joint in self.joints.items():

            raw_positions = self.read_joint_raw_positions(
                joint_key
            )

            angle_deg = joint.calculate_joint_angle(
                raw_positions
            )

            joint_states[joint_key] = {
                "raw_positions": raw_positions,
                "angle_deg": angle_deg
            }

        return {
            "robot_name": self.name,
            "joints": joint_states,
            "gripper": {
                "raw_position": self.read_gripper_raw_position()
            }
        }