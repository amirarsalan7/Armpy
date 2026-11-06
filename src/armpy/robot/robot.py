import time
from armpy.robot.gripper import Gripper

class Robot:

    POSITION_TOLERANCE_DEG = 1.0

    JOINT_POSITION_TOLERANCE_DEG = {
        "joint1": 1.0,
        "joint2": 2.5,
        "joint3": 3.5,
        "joint4": 3.5,
        "joint5": 1.0,
    }

    POLL_INTERVAL_S = 0.05

    DEFAULT_JOINT_VELOCITY_DEG_S = 40.0
    MIN_JOINT_VELOCITY_DEG_S = 1.0
    MAX_JOINT_VELOCITY_DEG_S = 120.0

    MOTION_TIMEOUT_SCALE = 2.5
    MOTION_TIMEOUT_MARGIN_S = 2.0
    MIN_MOTION_TIMEOUT_S = 5.0
    MAX_COUPLED_ANGLE_ERROR_DEG = 3.0

    def __init__(self, name, motors, joints, gripper):

        self.name = name
        self.motors = motors
        self.joints = joints
        self.gripper = gripper

        self.default_joint_velocity_deg_s = (
            self.DEFAULT_JOINT_VELOCITY_DEG_S
        )

        self._validate_components()


    def _validate_components(self):

        if not isinstance(
            self.name,
            str
        ) or not self.name:

            raise ValueError(
                "Robot name must be "
                "a non-empty string."
            )

        if not self.motors:

            raise ValueError(
                f"{self.name} must "
                "contain motors."
            )

        if not self.joints:

            raise ValueError(
                f"{self.name} must "
                "contain joints."
            )

        for joint_key, joint in (
            self.joints.items()
        ):

            for motor_id, motor in (
                joint.motors.items()
            ):

                if motor_id not in self.motors:

                    raise ValueError(
                        f"{joint_key}: "
                        f"Motor {motor_id} "
                        "does not exist in "
                        "Robot motors."
                    )

                if (
                    self.motors[
                        motor_id
                    ]
                    is not motor
                ):

                    raise ValueError(
                        f"{joint_key}: "
                        f"Motor {motor_id} "
                        "object does not match "
                        "Robot motor object."
                    )

        if not isinstance(
            self.gripper,
            Gripper
        ):

            raise ValueError(
                "Robot gripper must be "
                "a Gripper object."
            )

        gripper_motor = (
            self.gripper.motor
        )

        gripper_motor_id = str(
            gripper_motor.motor_id
        )

        if (
            gripper_motor_id
            not in self.motors
        ):

            raise ValueError(
                f"Gripper Motor "
                f"{gripper_motor_id} "
                "does not exist in "
                "Robot motors."
            )

        if (
            self.motors[
                gripper_motor_id
            ]
            is not gripper_motor
        ):

            raise ValueError(
                "Gripper motor object "
                "does not match Robot "
                "motor object."
            )

        return True


    def get_joint(self, joint_key):

        if joint_key not in self.joints:
            raise ValueError(
                f"Joint {joint_key} does not exist."
            )

        return self.joints[joint_key]

    def _get_joint_position_tolerance(
        self,
        joint_key
    ):

        return (
            self.JOINT_POSITION_TOLERANCE_DEG.get(
                joint_key,
                self.POSITION_TOLERANCE_DEG
            )
        )

    def get_motor(self, motor_id):

        motor_id = str(motor_id)

        if motor_id not in self.motors:
            raise ValueError(
                f"Motor {motor_id} does not exist."
            )

        return self.motors[motor_id]

    def _validate_joint_velocity(self, velocity_deg_s):

        if callable(velocity_deg_s):

            raise TypeError(
                "Joint velocity must be a numeric value, "
                "not a method. Pass the method result "
                "instead of the method itself."
            )

        if isinstance(velocity_deg_s, bool) or not isinstance(
            velocity_deg_s,
            (int, float)
        ):

            raise TypeError(
                "Joint velocity must be an int or float. "
                f"Received: {type(velocity_deg_s).__name__}"
            )

        if not (
            self.MIN_JOINT_VELOCITY_DEG_S
            <= velocity_deg_s
            <= self.MAX_JOINT_VELOCITY_DEG_S
        ):

            raise ValueError(
                f"Joint velocity must be between "
                f"{self.MIN_JOINT_VELOCITY_DEG_S:.2f} "
                f"and "
                f"{self.MAX_JOINT_VELOCITY_DEG_S:.2f} deg/s."
            )

        return True

    def set_default_joint_velocity(
        self,
        velocity_deg_s
    ):

        velocity_deg_s = float(
            velocity_deg_s
        )

        self._validate_joint_velocity(
            velocity_deg_s
        )

        self.default_joint_velocity_deg_s = (
            velocity_deg_s
        )

        return (
            self.default_joint_velocity_deg_s
        )
    
    def _calculate_profile_velocity_raw(
        self,
        joint,
        motor,
        velocity_deg_s
    ):

        motor_rpm = (
            velocity_deg_s
            * joint.gear_ratio
            / 6.0
        )

        return motor.rpm_to_profile_velocity_raw(
            motor_rpm
        )

    def _validate_joint_alignment(
        self,
        joint,
        raw_positions
    ):

        if len(joint.motors) <= 1:
            return True

        motor_angles = []

        for motor_id, raw_position in raw_positions.items():

            angle = joint.motor_raw_to_joint_angle(
                motor_id,
                raw_position
            )

            motor_angles.append(
                angle
            )

        angle_error = (
            max(motor_angles)
            - min(motor_angles)
        )

        if angle_error > self.MAX_COUPLED_ANGLE_ERROR_DEG:
            raise RuntimeError(
                f"{joint.name}: coupled motors disagree by "
                f"{angle_error:.2f} deg."
            )

        return True

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

        return (
            self.gripper
            .read_raw_position()
        )
    

    def read_gripper_state(self):

        return (
            self.gripper
            .read_state()
        )


    def open_gripper(
        self,
        velocity_rpm=None,
        wait=True
    ):

        return (
            self.gripper.open(
                velocity_rpm=velocity_rpm,
                wait=wait
            )
        )


    def close_gripper(
        self,
        velocity_rpm=None,
        wait=True
    ):

        return (
            self.gripper.close(
                velocity_rpm=velocity_rpm,
                wait=wait
            )
        )


    def set_gripper_opening(
        self,
        opening_percent,
        velocity_rpm=None,
        wait=True
    ):

        return (
            self.gripper.set_opening(
                opening_percent,
                velocity_rpm=velocity_rpm,
                wait=wait
            )
        )


    def hold_gripper(self):

        return (
            self.gripper.hold()
        )


    def set_default_gripper_velocity(
        self,
        velocity_rpm
    ):

        return (
            self.gripper
            .set_default_velocity_rpm(
                velocity_rpm
            )
        )

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
            "gripper": (
                self.read_gripper_state()
            )
        }

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

    def preview_joint_move(
        self,
        joint_key,
        target_angle_deg,
        velocity_deg_s=None
    ):

        if velocity_deg_s is None:
            velocity_deg_s = (
                self.default_joint_velocity_deg_s
            )

        self._validate_joint_velocity(
            velocity_deg_s
        )

        joint = self.get_joint(
            joint_key
        )

        joint.check_angle_limits(
            target_angle_deg
        )

        raw_positions = self.read_joint_raw_positions(
            joint_key
        )

        self._validate_joint_alignment(
            joint,
            raw_positions
        )

        current_angle_deg = (
            joint.calculate_joint_angle(
                raw_positions
            )
        )

        movement_deg = (
            target_angle_deg
            - current_angle_deg
        )

        goals = joint.calculate_goal_positions(
            target_angle_deg
        )

        profile_velocities = {}

        torque_states = {}

        for motor_id, motor in joint.motors.items():

            goal_raw = goals[motor_id]

            self._preflight_motor_for_goal(
                motor,
                goal_raw
            )

            profile_velocities[motor_id] = (
                self._calculate_profile_velocity_raw(
                    joint,
                    motor,
                    velocity_deg_s
                )
            )

            torque = motor.read_torque_enabled()

            if torque is None:
                raise RuntimeError(
                    f"Motor {motor.motor_id}: "
                    "could not read torque state."
                )

            torque_states[motor_id] = torque

        unique_torque_states = set(
            torque_states.values()
        )

        if len(unique_torque_states) != 1:
            raise RuntimeError(
                f"{joint_key}: motors have mixed torque states."
            )

        return {
            "joint_key": joint_key,
            "current_angle_deg": current_angle_deg,
            "target_angle_deg": target_angle_deg,
            "movement_deg": movement_deg,
            "velocity_deg_s": velocity_deg_s,
            "current_raw": raw_positions,
            "goal_raw": goals,
            "profile_velocity_raw": profile_velocities,
            "torque_enabled": (
                next(iter(unique_torque_states))
                == 1
            )
        }

    def preview_multi_joint_move(
        self,
        targets,
        velocity_deg_s=None
    ):

        if not isinstance(targets, dict) or not targets:
            raise ValueError(
                "Multi-joint targets must be a non-empty dictionary."
            )

        if velocity_deg_s is None:
            velocity_deg_s = (
                self.default_joint_velocity_deg_s
            )

        self._validate_joint_velocity(
            velocity_deg_s
        )

        joint_plans = {}
        used_motor_ids = set()

        for joint_key, target_angle_deg in targets.items():

            plan = self.preview_joint_move(
                joint_key,
                target_angle_deg,
                velocity_deg_s
            )

            motor_ids = set(
                plan["goal_raw"]
            )

            duplicated = (
                used_motor_ids
                & motor_ids
            )

            if duplicated:
                raise RuntimeError(
                    f"Motors are used by multiple target joints: "
                    f"{sorted(duplicated)}."
                )

            used_motor_ids.update(
                motor_ids
            )

            joint_plans[joint_key] = plan

        return {
            "targets": dict(targets),
            "velocity_deg_s": velocity_deg_s,
            "joint_plans": joint_plans
        }

    def _collect_multi_joint_goals(self, joint_plans):

        goals = {}

        for plan in joint_plans.values():

            for motor_id, goal_raw in plan["goal_raw"].items():

                if motor_id in goals:
                    raise RuntimeError(
                        f"Motor {motor_id} received more than one goal."
                    )

                goals[motor_id] = goal_raw

        return goals

    def _set_multi_joint_profile_velocity(
        self,
        joint_plans
    ):

        for joint_key, plan in joint_plans.items():

            joint = self.get_joint(
                joint_key
            )

            self._set_joint_profile_velocity(
                joint,
                plan
            )
        return True
    
    def _set_joint_profile_velocity(
        self,
        joint,
        plan
    ):

        for motor_id, motor in joint.motors.items():

            profile_raw = (
                plan["profile_velocity_raw"][motor_id]
            )

            if not motor.set_profile_velocity_raw(
                profile_raw
            ):
                raise RuntimeError(
                    f"Motor {motor.motor_id}: "
                    "could not set Profile Velocity."
                )

        return True
    
    def _prepare_joint_torque(
        self,
        joint,
        plan
    ):

        torque_states = {
            motor_id: motor.read_torque_enabled()
            for motor_id, motor in joint.motors.items()
        }

        if any(
            state is None
            for state in torque_states.values()
        ):
            raise RuntimeError(
                f"{plan['joint_key']}: "
                "could not read all torque states."
            )

        unique_states = set(
            torque_states.values()
        )

        if len(unique_states) != 1:
            raise RuntimeError(
                f"{plan['joint_key']}: "
                "motors have mixed torque states."
            )

        if next(iter(unique_states)) == 1:
            return False

        for motor_id, motor in joint.motors.items():

            current_goal = (
                plan["current_raw"][motor_id]
                % motor.COUNTS_PER_REVOLUTION
            )

            if not motor.stage_goal_position_raw(
                current_goal
            ):
                raise RuntimeError(
                    f"Motor {motor.motor_id}: "
                    "could not stage current position."
                )

        first_motor = next(
            iter(joint.motors.values())
        )

        torque_values = {
            int(motor_id): motor.TORQUE_ON
            for motor_id, motor in joint.motors.items()
        }

        first_motor.connection.sync_write(
            address=first_motor.ADDR_TORQUE_ENABLE,
            data_length=1,
            values_by_id=torque_values
        )

        for motor in joint.motors.values():

            torque = motor.read_torque_enabled()

            if torque != motor.TORQUE_ON:
                raise RuntimeError(
                    f"Motor {motor.motor_id}: "
                    "torque enable verification failed."
                )

        return True

    def _prepare_multi_joint_torque(
        self,
        joint_plans
    ):

        enabled_by_command = {}

        for joint_key, plan in joint_plans.items():

            joint = self.get_joint(
                joint_key
            )

            enabled_by_command[joint_key] = (
                self._prepare_joint_torque(
                    joint,
                    plan
                )
            )

        return enabled_by_command
    
    def _write_joint_goal_positions(
        self,
        joint,
        goals
    ):

        if len(joint.motors) == 1:

            motor_id = next(
                iter(joint.motors)
            )

            motor = joint.motors[motor_id]

            if not motor.set_goal_position_raw(
                goals[motor_id]
            ):
                raise RuntimeError(
                    f"Motor {motor.motor_id}: "
                    "Goal Position write failed."
                )

            return True

        for motor_id, motor in joint.motors.items():

            motor.validate_goal_position_raw(
                goals[motor_id]
            )

            torque = motor.read_torque_enabled()

            if torque is None:
                raise RuntimeError(
                    f"Motor {motor.motor_id}: "
                    "could not read torque state."
                )

            if torque != motor.TORQUE_ON:
                raise RuntimeError(
                    f"Motor {motor.motor_id}: "
                    "torque is not enabled."
                )

        first_motor = next(
            iter(joint.motors.values())
        )

        first_motor.connection.sync_write(
            address=first_motor.ADDR_GOAL_POSITION,
            data_length=4,
            values_by_id={
                int(motor_id): goal
                for motor_id, goal in goals.items()
            }
        )

        return True

    def _write_multi_joint_goals(
        self,
        goals
    ):

        if not goals:
            raise ValueError(
                "No motor goals were provided."
            )

        first_motor_id = next(
            iter(goals)
        )

        first_motor = self.get_motor(
            first_motor_id
        )

        first_motor.connection.sync_write(
            address=first_motor.ADDR_GOAL_POSITION,
            data_length=4,
            values_by_id={
                int(motor_id): goal_raw
                for motor_id, goal_raw in goals.items()
            }
        )

        return True

    def _calculate_motion_timeout(
        self,
        movement_deg,
        velocity_deg_s
    ):

        expected_time = (
            abs(movement_deg)
            / velocity_deg_s
        )

        calculated_timeout = (
            expected_time
            * self.MOTION_TIMEOUT_SCALE
            + self.MOTION_TIMEOUT_MARGIN_S
        )

        return max(
            self.MIN_MOTION_TIMEOUT_S,
            calculated_timeout
        )

    def _calculate_multi_joint_timeout(
        self,
        joint_plans
    ):

        timeouts = []

        for plan in joint_plans.values():

            timeout = self._calculate_motion_timeout(
                plan["movement_deg"],
                plan["velocity_deg_s"]
            )

            timeouts.append(
                timeout
            )

        return max(timeouts)

    def _hold_joint_raw_positions(
        self,
        joint,
        raw_positions
    ):

        goals = {}

        for motor_id, motor in joint.motors.items():

            goal = (
                raw_positions[motor_id]
                % motor.COUNTS_PER_REVOLUTION
            )

            motor.validate_goal_position_raw(
                goal
            )

            goals[motor_id] = goal

        if len(joint.motors) == 1:

            motor_id = next(iter(joint.motors))

            if not joint.motors[motor_id].set_goal_position_raw(
                goals[motor_id]
            ):
                raise RuntimeError(
                    "Could not hold joint position."
                )

            return goals

        first_motor = next(
            iter(joint.motors.values())
        )

        first_motor.connection.sync_write(
            address=first_motor.ADDR_GOAL_POSITION,
            data_length=4,
            values_by_id={
                int(motor_id): goal
                for motor_id, goal in goals.items()
            }
        )

        return goals

    def _hold_multi_joint_raw_positions(
        self,
        raw_positions_by_joint
    ):

        goals = {}

        for joint_key, raw_positions in raw_positions_by_joint.items():

            joint = self.get_joint(
                joint_key
            )

            for motor_id, raw_position in raw_positions.items():

                motor = joint.motors[motor_id]

                goal = (
                    raw_position
                    % motor.COUNTS_PER_REVOLUTION
                )

                motor.validate_goal_position_raw(
                    goal
                )

                goals[motor_id] = goal

        self._write_multi_joint_goals(
            goals
        )

        return goals

    def _wait_for_joint_target(
        self,
        joint,
        plan
    ):

        timeout = self._calculate_motion_timeout(
            plan["movement_deg"],
            plan["velocity_deg_s"]
        )

        deadline = (
            time.monotonic()
            + timeout
        )

        last_angle = None
        last_positions = None

        while True:

            raw_positions = (
                self.read_joint_raw_positions(
                    plan["joint_key"]
                )
            )

            last_positions = raw_positions

            self._validate_joint_alignment(
                joint,
                raw_positions
            )

            current_angle = (
                joint.calculate_joint_angle(
                    raw_positions
                )
            )

            last_angle = current_angle

            angle_error = abs(
                plan["target_angle_deg"]
                - current_angle
            )

            tolerance_deg = (
                self._get_joint_position_tolerance(
                    plan["joint_key"]
                )
            )

            if angle_error <= tolerance_deg:
                return raw_positions

            if time.monotonic() >= deadline:

                self._hold_joint_raw_positions(
                    joint,
                    raw_positions
                )

                raise TimeoutError(
                    f"{plan['joint_key']}: "
                    f"motion timeout after "
                    f"{timeout:.2f} s. "
                    f"Target="
                    f"{plan['target_angle_deg']:.2f} deg, "
                    f"actual={last_angle:.2f} deg, "
                    f"error={angle_error:.2f} deg, "
                    f"raw={last_positions}. "
                    "Current position was held."
                )

            time.sleep(
                self.POLL_INTERVAL_S
            )

    def _wait_for_multi_joint_targets(
        self,
        joint_plans
    ):

        timeout = (
            self._calculate_multi_joint_timeout(
                joint_plans
            )
        )

        deadline = (
            time.monotonic()
            + timeout
        )

        while True:

            all_reached = True
            current_positions = {}
            last_joint_status = {}

            for joint_key, plan in (
                joint_plans.items()
            ):

                joint = self.get_joint(
                    joint_key
                )

                raw_positions = (
                    self.read_joint_raw_positions(
                        joint_key
                    )
                )

                current_positions[joint_key] = (
                    raw_positions
                )

                self._validate_joint_alignment(
                    joint,
                    raw_positions
                )

                current_angle = (
                    joint.calculate_joint_angle(
                        raw_positions
                    )
                )

                angle_error = abs(
                    plan["target_angle_deg"]
                    - current_angle
                )

                tolerance_deg = (
                    self._get_joint_position_tolerance(
                        joint_key
                    )
                )

                last_joint_status[joint_key] = {
                    "target": plan["target_angle_deg"],
                    "actual": current_angle,
                    "error": angle_error,
                    "tolerance": tolerance_deg,
                    "raw": raw_positions
                }

                if angle_error > tolerance_deg:
                    all_reached = False

            if all_reached:
                return current_positions

            if time.monotonic() >= deadline:

                self._hold_multi_joint_raw_positions(
                    current_positions
                )

                pending_details = []

                for joint_key, status in (
                    last_joint_status.items()
                ):

                    if (
                        status["error"]
                        <= status["tolerance"]
                    ):
                        continue

                    pending_details.append(
                        f"{joint_key}: "
                        f"target={status['target']:.2f}, "
                        f"actual={status['actual']:.2f}, "
                        f"error={status['error']:.2f}, "
                        f"tolerance={status['tolerance']:.2f}, "
                        f"raw={status['raw']}"
                    )

                details_text = " | ".join(
                    pending_details
                )

                raise TimeoutError(
                    f"Multi-joint motion timeout "
                    f"after {timeout:.2f} seconds. "
                    f"Pending joints: {details_text}. "
                    "Current positions were held."
                )

            time.sleep(
                self.POLL_INTERVAL_S
            )

    def move_joint(
        self,
        joint_key,
        target_angle_deg,
        velocity_deg_s=None,
        wait=True
    ):

        plan = self.preview_joint_move(
            joint_key,
            target_angle_deg,
            velocity_deg_s
        )

        joint = self.get_joint(
            joint_key
        )

        self._set_joint_profile_velocity(
            joint,
            plan
        )

        torque_enabled_by_command = (
            self._prepare_joint_torque(
                joint,
                plan
            )
        )

        self._write_joint_goal_positions(
            joint,
            plan["goal_raw"]
        )
        if wait:

            final_raw = self._wait_for_joint_target(
                joint,
                plan
            )

        else:
            final_raw = None


        return {
            "joint_key": joint_key,
            "target_angle_deg": target_angle_deg,
            "velocity_deg_s": plan["velocity_deg_s"],
            "goal_raw": plan["goal_raw"],
            "final_raw": final_raw,
            "torque_enabled_by_command": (
                torque_enabled_by_command
            )
        }

    def move_joints(
        self,
        targets,
        velocity_deg_s=None
    ):

        preview = self.preview_multi_joint_move(
            targets,
            velocity_deg_s
        )

        joint_plans = preview[
            "joint_plans"
        ]

        self._set_multi_joint_profile_velocity(
            joint_plans
        )

        torque_enabled_by_command = (
            self._prepare_multi_joint_torque(
                joint_plans
            )
        )

        goals = self._collect_multi_joint_goals(
            joint_plans
        )

        self._write_multi_joint_goals(
            goals
        )

        final_positions = (
            self._wait_for_multi_joint_targets(
                joint_plans
            )
        )

        return {
            "targets": dict(targets),
            "velocity_deg_s": preview["velocity_deg_s"],
            "goal_raw": goals,
            "final_raw": final_positions,
            "torque_enabled_by_command": (
                torque_enabled_by_command
            )
        }

    def hold_joint(self, joint_key):

        joint = self.get_joint(
            joint_key
        )

        for motor in joint.motors.values():

            torque = motor.read_torque_enabled()

            if torque is None:
                raise RuntimeError(
                    f"{joint_key}: could not read torque state "
                    f"from Motor {motor.motor_id}."
                )

            if torque != motor.TORQUE_ON:
                raise RuntimeError(
                    f"{joint_key}: "
                    "all motors must have torque enabled."
                )

        raw_positions = (
            self.read_joint_raw_positions(
                joint_key
            )
        )

        return self._hold_joint_raw_positions(
            joint,
            raw_positions
        )