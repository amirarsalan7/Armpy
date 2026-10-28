import time

class Robot:

    MAX_SINGLE_MOVE_DEG = 50.0
    POSITION_TOLERANCE_DEG = 1.0
    MOTION_TIMEOUT_S = 5.0
    POLL_INTERVAL_S = 0.05

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


    def _require_single_motor_joint(self, joint_key):

        joint = self.get_joint(joint_key)

        if len(joint.motors) != 1:
            raise RuntimeError(
                f"{joint_key} uses multiple motors. "
                "Synchronized motion is required."
            )

        return joint

    def _preflight_motor_for_goal(self, motor, goal_raw):

        operating_mode = motor.read_operating_mode()

        if operating_mode is None:
            raise RuntimeError(
                f"Motor {motor.motor_id}: could not read Operating Mode."
            )

        if operating_mode != motor.MODE_POSITION:
            raise RuntimeError(
                f"Motor {motor.motor_id}: expected Position Control Mode."
            )

        drive_mode = motor.read_drive_mode()

        if drive_mode is None:
            raise RuntimeError(
                f"Motor {motor.motor_id}: could not read Drive Mode."
            )

        if drive_mode & motor.TORQUE_ON_BY_GOAL_MASK:
            raise RuntimeError(
                f"Motor {motor.motor_id}: Torque On by Goal Update is enabled."
            )

        hardware_error = motor.read_hardware_error()

        if hardware_error is None:
            raise RuntimeError(
                f"Motor {motor.motor_id}: could not read Hardware Error Status."
            )

        if hardware_error != 0:
            raise RuntimeError(
                f"Motor {motor.motor_id}: hardware error status = {hardware_error}."
            )

        motor.validate_goal_position_raw(
            goal_raw
        )

        torque = motor.read_torque_enabled()

        if torque is None:
            raise RuntimeError(
                f"Motor {motor.motor_id}: could not read torque state."
            )

        return torque

    def preview_joint_move(self, joint_key, target_angle_deg):

        joint = self._require_single_motor_joint(
            joint_key
        )

        joint.check_angle_limits(
            target_angle_deg
        )

        raw_positions = self.read_joint_raw_positions(
            joint_key
        )

        current_angle_deg = joint.calculate_joint_angle(
            raw_positions
        )

        movement_deg = (
            target_angle_deg
            - current_angle_deg
        )

        if abs(movement_deg) > self.MAX_SINGLE_MOVE_DEG:
            raise ValueError(
                f"{joint_key}: requested movement is "
                f"{movement_deg:.2f} deg. "
                f"Maximum allowed per command is "
                f"{self.MAX_SINGLE_MOVE_DEG:.2f} deg."
            )

        goals = joint.calculate_goal_positions(
            target_angle_deg
        )

        motor_id = next(iter(joint.motors))
        motor = joint.motors[motor_id]

        goal_raw = goals[motor_id]
        current_raw = raw_positions[motor_id]

        torque = self._preflight_motor_for_goal(
            motor,
            goal_raw
        )

        return {
            "joint_key": joint_key,
            "motor_id": motor_id,
            "current_angle_deg": current_angle_deg,
            "target_angle_deg": target_angle_deg,
            "movement_deg": movement_deg,
            "current_raw": current_raw,
            "goal_raw": goal_raw,
            "torque_enabled": torque == motor.TORQUE_ON
        }

    def _prepare_joint_torque(self, plan):

        motor = self.get_motor(
            plan["motor_id"]
        )

        torque = motor.read_torque_enabled()

        if torque is None:
            raise RuntimeError(
                f"Motor {motor.motor_id}: could not read torque state."
            )

        if torque == motor.TORQUE_ON:
            return False

        current_goal = (
            plan["current_raw"]
            % motor.COUNTS_PER_REVOLUTION
        )

        if not motor.stage_goal_position_raw(
            current_goal
        ):
            raise RuntimeError(
                f"Motor {motor.motor_id}: could not stage current Goal Position."
            )

        if not motor.enable_torque():
            raise RuntimeError(
                f"Motor {motor.motor_id}: could not enable torque."
            )

        return True

    def _wait_for_single_motor_target(self, joint, motor, goal_raw):

        tolerance_counts = max(
            1,
            round(
                self.POSITION_TOLERANCE_DEG
                * joint.counts_per_joint_degree()
            )
        )

        deadline = (
            time.monotonic()
            + self.MOTION_TIMEOUT_S
        )

        while True:

            present_raw = motor.read_present_position_raw()

            if present_raw is None:
                raise RuntimeError(
                    f"Motor {motor.motor_id}: "
                    "could not read Present Position."
                )

            error_counts = abs(
                goal_raw - present_raw
            )

            if error_counts <= tolerance_counts:
                return present_raw

            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Motor {motor.motor_id}: "
                    "motion timeout."
                )

            time.sleep(
                self.POLL_INTERVAL_S
            )

    def move_joint(self, joint_key, target_angle_deg):

        plan = self.preview_joint_move(
            joint_key,
            target_angle_deg
        )

        joint = self.get_joint(
            joint_key
        )

        motor = self.get_motor(
            plan["motor_id"]
        )

        torque_enabled_by_command = (
            self._prepare_joint_torque(
                plan
            )
        )

        if not motor.set_goal_position_raw(
            plan["goal_raw"]
        ):
            raise RuntimeError(
                f"Motor {motor.motor_id}: "
                "Goal Position write failed."
            )

        final_raw = self._wait_for_single_motor_target(
            joint,
            motor,
            plan["goal_raw"]
        )

        return {
            "joint_key": joint_key,
            "target_angle_deg": target_angle_deg,
            "goal_raw": plan["goal_raw"],
            "final_raw": final_raw,
            "torque_enabled_by_command": torque_enabled_by_command
        }

    def hold_joint(self, joint_key):

        joint = self._require_single_motor_joint(
            joint_key
        )

        motor_id = next(iter(joint.motors))
        motor = joint.motors[motor_id]

        torque = motor.read_torque_enabled()

        if torque != motor.TORQUE_ON:
            raise RuntimeError(
                f"{joint_key}: torque is not enabled."
            )

        present_raw = motor.read_present_position_raw()

        if present_raw is None:
            raise RuntimeError(
                f"Motor {motor.motor_id}: "
                "could not read Present Position."
            )

        motor.validate_goal_position_raw(
            present_raw
        )

        if not motor.set_goal_position_raw(
            present_raw
        ):
            raise RuntimeError(
                f"{joint_key}: could not hold current position."
            )

        return present_raw