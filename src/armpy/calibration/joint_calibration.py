import json

from datetime import datetime
from pathlib import Path

from src.armpy.hardware.dynamixel_motor import DynamixelMotor

class JointCalibration:

    POSITION_COUNTS_PER_REV = 4096
    HALF_POSITION_RANGE = 2048
    HOME_TOLERANCE_COUNTS = 500

    def __init__(self,connection,hardware_inventory,robot_config ):

        self.connection = connection

        self.hardware_inventory = hardware_inventory
        self.robot_config = robot_config


        self.motor_objects = {} #instance Variable

        self.calibration = None


        self._validate_mapping()
        self._build_motor_objects()


    def _validate_mapping(self):

        available_motor_ids = set(
            self.hardware_inventory.get_motor_ids() )

        joints = self.robot_config.get_all_joints()

        for joint_key, joint_data in joints.items():

            for motor_id in joint_data["motor_ids"]:

                if motor_id not in available_motor_ids:
                    
                    raise ValueError(
                        f"{joint_key} uses "
                        f"Motor {motor_id},"
                        "but that motor does not "
                        "exist in hardware inventory"
                    )
            
        gripper = ( self.robot_config.get_gripper_config())

        gripper_motor_id = ( gripper["motor_id"])

        if gripper_motor_id not in available_motor_ids:
                
            raise ValueError(
                f"gripper uses Motor "
                f"{gripper_motor_id},"
                "but that motor dose not "
                "exist in hardware inventory."
            ) 

        return True

    def _build_motor_objects(self):

        for motor_id in self.hardware_inventory.get_motor_ids():

            motor_info = self.hardware_inventory.get_motor(motor_id)

            identity = motor_info["identity"]

            motor = DynamixelMotor(
                connection=self.connection,

                motor_id = motor_id,

                model_number = identity["model_number"],

                firmware_version=identity["firmware_version"]
            )

            self.motor_objects[motor_id] = motor

    def _read_motor_position_raw(self,motor_id):

        motor = self.motor_objects[motor_id]


        position_raw = motor.read_present_position_raw()

        if position_raw is None:
            raise RuntimeError(
                f"Could not read position from motor {motor_id}."
            )
        return position_raw

    def _timestamp(self):

        return(
            datetime.now()
            .astimezone()
            .isoformat(timespec="seconds")
        )

    def _touch(self):

        if self.calibration is not None:
            self.calibration["calibrated_at"] = self._timestamp()


    def _require_calibration(self):
        if self.calibration is None:
            raise RuntimeError(
                "Create or load calibration data first."
            )

    def capture_home(self):

        self._require_calibration()
        self.check_all_torque_off()

        readings = {}

        for joint_key in self.robot_config.get_all_joints():
            readings[joint_key] = self.read_joint_positions(joint_key)

        gripper_raw = self.read_gripper_position()

        for joint_key, positions in readings.items():
            self.store_joint_home(joint_key, positions)

        self.store_gripper_reference(gripper_raw)

        return self.calibration

    def capture_joint_home(self, joint_key):

        self.check_joint_torque_off(joint_key)

        positions = self.read_joint_positions(joint_key)

        return self.store_joint_home(joint_key, positions)
    
    def capture_gripper_reference(self):

        self.check_gripper_torque_off()

        position = self.read_gripper_position()

        return self.store_gripper_reference(position)

    
    def store_gripper_reference(self, position):

        self._require_calibration()

        reference = self.calibration["gripper"]["reference"]

        reference["raw"] = position
        reference["calibrated"] = True

        self._touch()

        return position


    
    def check_joint_torque_off(self,joint_key):

        joint_data = self.robot_config.get_joint_config(joint_key)

        for motor_id in joint_data["motor_ids"]:

            motor = self.motor_objects[motor_id]
            torque_enabled = motor.read_torque_enabled()

            if torque_enabled is None:
                raise RuntimeError(
                    f"Could not read torque state of Motor {motor_id}."
                )
            if torque_enabled != 0:
                raise RuntimeError(
                    f"Motor {motor_id} torque is ON."
                    "Manual calibration requires torque OFF."
                )

        return True

    def check_gripper_torque_off(self):

        gripper = self.robot_config.get_gripper_config()
        motor_id = gripper["motor_id"]

        motor = self.motor_objects[motor_id]
        torque_enabled = motor.read_torque_enabled()

        if torque_enabled is None:
            raise RuntimeError(
                f"Could not read torque state of Motor {motor_id}."
            )

        if torque_enabled != 0:
            raise RuntimeError(
                f"Motor {motor_id} torque is ON. "
                "Manual calibration requires torque OFF."
            )

        return True

    def check_all_torque_off(self):

        joints = self.robot_config.get_all_joints()

        for joint_key in joints:
            self.check_joint_torque_off(joint_key)

        self.check_gripper_torque_off()

        return True



    def read_joint_positions(self,joint_key):

        joint = self.robot_config.get_joint_config(joint_key)

        positions = {}

        for motor_id in joint["motor_ids"]:

            position = self._read_motor_position_raw(motor_id)

            positions[str(motor_id)] = position

        return positions

    def read_gripper_position(self):

        gripper = self.robot_config.get_gripper_config()

        return self._read_motor_position_raw(
            gripper["motor_id"]
        )


    def _calculate_position_delta(self, before, after):


        return after - before


    def calculate_joint_directions(
            self,
            before_positions,
            after_positions,
            min_movement_counts=20
    ):
        directions = {}
        deltas = {}

        if set(before_positions) != set(after_positions):
            raise ValueError(
                "Before and after motor sets do not match."
            )

        for motor_id, before in before_positions.items():

            after = after_positions[motor_id]
            delta = self._calculate_position_delta(before, after)

            if abs(delta) < min_movement_counts:
                raise RuntimeError(
                    f"Motor {motor_id} moved only {delta} counts. "
                    "Move the joint a little more and try again."
                )

            if abs(delta) > 1024:
                raise RuntimeError(
                    f"Motor {motor_id} moved {delta} counts. "
                    "Direction calibration requires a smaller movement."
                )

            directions[motor_id] = 1 if delta > 0 else -1
            deltas[motor_id] = delta

        return directions, deltas

    def _calculate_single_turn_error(self, reference, position):

        delta = position - reference

        delta = (
            (delta + self.HALF_POSITION_RANGE)
            % self.POSITION_COUNTS_PER_REV
            - self.HALF_POSITION_RANGE
        )

        return delta
    
    def store_joint_direction(
            self,
            joint_key,
            before_positions,
            after_positions,
            deltas,
            directions
    ):
        
        self._require_calibration()

        joint = self.calibration["joints"][joint_key]

        if not joint["home"]["calibrated"]:
            raise RuntimeError(f"Calibrate {joint_key} HOME first.")

        expected_ids = {str(motor_id) for motor_id in joint["motor_ids"]}

        for data in (before_positions, after_positions, deltas, directions):
            if set(data) != expected_ids:
                raise ValueError("Direction motor IDs do not match the joint.")

        positive_motion = self.robot_config.get_joint_config(joint_key).get("positive_motion")

        if not positive_motion:
            raise ValueError(f"Define positive_motion for {joint_key} first.")

        if any(direction not in (-1, 1) for direction in directions.values()):
            raise ValueError("Invalid motor direction.")

        if joint_key == "joint2":

            motor_ids = [
                str(motor_id)
                for motor_id in joint["motor_ids"]
            ]

            if len(motor_ids) != 2:
                raise ValueError(
                    "joint2 must use exactly two motors."
                )

            if directions[motor_ids[0]] == directions[motor_ids[1]]:
                raise ValueError(
                    "Shoulder motors must have opposite directions."
                )

        # if joint_key == "joint2" and directions["2"] == directions["3"]:
            # raise ValueError("Shoulder Motors 2 and 3 must have opposite directions.")

        previous = joint["direction"]

        if (previous["motor_directions"] != directions
                or previous.get("positive_motion") != positive_motion):
            self._invalidate_limits(joint)

        joint["direction"] = {
            "calibrated": True,
            "positive_motion": positive_motion,

            "measurement": {
                "before_raw": before_positions,
                "after_raw": after_positions,
                "delta_raw": deltas
            },

            "motor_directions": dict(directions)
        }

        self._touch()

    def create_new(self):

        self.calibration = self._create_calibration_schema()

        return self.calibration

    def load(self, file_path):

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Calibration file not found: {path}")

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if data.get("schema_version") != 2:
            raise ValueError("Unsupported calibration schema version.")

        if data.get("robot_name") != self.robot_config.get_robot_name():
            raise ValueError("Calibration belongs to a different robot.")

        if not isinstance(data.get("joints"), dict) or "gripper" not in data:
            raise ValueError("Invalid calibration structure.")

        joints = self.robot_config.get_all_joints()

        if set(data["joints"]) != set(joints):
            raise ValueError("Calibration joint mapping does not match robot configuration.")

        for joint_key, joint_config in joints.items():
            if data["joints"][joint_key].get("motor_ids") != joint_config["motor_ids"]:
                raise ValueError(f"{joint_key}: motor mapping has changed.")


        gripper_config = self.robot_config.get_gripper_config()
        gripper_data = data["gripper"]

        if gripper_data.get("motor_id") != gripper_config["motor_id"]:
            raise ValueError(
                "Calibration gripper mapping does not match robot configuration."
            )

        
        self.calibration = data

        return self.calibration


    def save(self, file_path):

        self._require_calibration()

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = Path(str(path) + ".tmp")

        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(self.calibration, file, indent=4)

        temporary_path.replace(path)

        return path

    
    def _create_calibration_schema(self):

        joint_calibrations = {}

        for joint_key, joint_data in self.robot_config.get_all_joints().items():

            joint_calibrations[joint_key] = {
                "name": joint_data["name"],
                "motor_ids": joint_data["motor_ids"],

                "home": {
                    "calibrated": False,
                    "raw": {}
                },

                "direction": {
                    "calibrated": False,
                    "positive_motion": None,
                    "measurement": {
                        "before_raw": {},
                        "after_raw": {},
                        "delta_raw": {}
                    },
                    "motor_directions": {}
                },

                "limits": {
                    "calibrated": False,
                    "negative_limit_raw": {},
                    "middle_raw": {},
                    "positive_limit_raw": {}
                }
            }

        gripper = self.robot_config.get_gripper_config()

        return {
            "schema_version": 2,
            "robot_name": self.robot_config.get_robot_name(),
            "calibrated_at": None,
            "source_hardware_inventory": str(self.hardware_inventory.file_path),
            "joints": joint_calibrations,

            "gripper": {
                "name": gripper["name"],
                "motor_id": gripper["motor_id"],

                "reference": {
                    "calibrated": False,
                    "raw": None
                },

                "open_close": {
                    "calibrated": False,
                    "open_raw": None,
                    "close_raw": None
                }
            }
        }

    def store_joint_limits(self, joint_key, negative_positions, middle_positions, positive_positions, min_movement_counts=20):

        self._require_calibration()

        joint = self.calibration["joints"][joint_key]

        if not joint["home"]["calibrated"]:
            raise RuntimeError(
                f"{joint_key} HOME must be calibrated first."
            )

        if not joint["direction"]["calibrated"]:
            raise RuntimeError(
                f"{joint_key} direction must be calibrated first."
            )

        expected_ids = {
            str(motor_id)
            for motor_id in joint["motor_ids"]
        }

        if set(negative_positions) != expected_ids:
            raise ValueError(
                "Negative limit motor IDs are invalid."
            )

        if set(middle_positions) != expected_ids:
            raise ValueError(
                "Middle position motor IDs are invalid."
            )

        if set(positive_positions) != expected_ids:
            raise ValueError(
                "Positive limit motor IDs are invalid."
            )

        directions = joint["direction"]["motor_directions"]

        for motor_id in expected_ids:

            direction = directions[motor_id]
            home_raw = joint["home"]["raw"][motor_id]

            home_error = self._calculate_single_turn_error(
                home_raw,
                middle_positions[motor_id]
            )

            if abs(home_error) > self.HOME_TOLERANCE_COUNTS:
                raise RuntimeError(
                    f"Motor {motor_id} middle position is not close enough "
                    f"to calibrated HOME. Error: {home_error} counts."
                )

            negative_to_middle_delta = self._calculate_position_delta(
                negative_positions[motor_id],
                middle_positions[motor_id]
            )

            middle_to_positive_delta = self._calculate_position_delta(
                middle_positions[motor_id],
                positive_positions[motor_id]
            )

            if abs(negative_to_middle_delta) < min_movement_counts:
                raise RuntimeError(
                    f"Motor {motor_id} negative limit range is too small."
                )

            if abs(middle_to_positive_delta) < min_movement_counts:
                raise RuntimeError(
                    f"Motor {motor_id} positive limit range is too small."
                )

            if negative_to_middle_delta * direction <= 0:
                raise RuntimeError(
                    f"Motor {motor_id} negative limit direction is invalid."
                )

            if middle_to_positive_delta * direction <= 0:
                raise RuntimeError(
                    f"Motor {motor_id} positive limit direction is invalid."
                )

        joint["limits"]["negative_limit_raw"] = dict(negative_positions)
        joint["limits"]["middle_raw"] = dict(middle_positions)
        joint["limits"]["positive_limit_raw"] = dict(positive_positions)
        joint["limits"]["calibrated"] = True

        self._touch()

    def store_gripper_open(self, position, min_movement_counts=20):

        self._require_calibration()

        data = self.calibration["gripper"]["open_close"]
        close_position = data["close_raw"]

        if close_position is not None:
            if abs(position - close_position) < min_movement_counts:
                raise ValueError("Gripper OPEN and CLOSE are too close.")

        data["open_raw"] = position
        data["calibrated"] = close_position is not None

        self._touch()


    def store_gripper_close(self, position, min_movement_counts=20):

        self._require_calibration()

        data = self.calibration["gripper"]["open_close"]
        open_position = data["open_raw"]

        if open_position is not None:
            if abs(position - open_position) < min_movement_counts:
                raise ValueError("Gripper OPEN and CLOSE are too close.")

        data["close_raw"] = position
        data["calibrated"] = open_position is not None

        self._touch()


    def store_gripper_positions(self, open_position, close_position, min_movement_counts=20):

        self._require_calibration()

        if abs(close_position - open_position) < min_movement_counts:
            raise ValueError("Gripper OPEN and CLOSE are too close.")

        self.calibration["gripper"]["open_close"] = {
            "calibrated": True,
            "open_raw": open_position,
            "close_raw": close_position
        }

        self._touch()

    def get_status(self):

        self._require_calibration()

        status = {
            "joints":{},
            "gripper":{}
        }

        for joint_key,joint in self.calibration["joints"].items():

            status["joints"][joint_key] = {
                "home":joint["home"]["calibrated"],
                "direction":joint["direction"]["calibrated"],
                "limits":joint["limits"]["calibrated"]
            }

        gripper = self.calibration["gripper"]

        status["gripper"] = {
            "reference":gripper["reference"]["calibrated"],
            "open_close":gripper["open_close"]["calibrated"]
        }

        return status

    def _invalidate_limits(self, joint):

        joint["limits"] = {
            "calibrated": False,
            "negative_limit_raw": {},
            "middle_raw": {},
            "positive_limit_raw": {}
        }

    def store_joint_home(self, joint_key, positions):

        self._require_calibration()

        joint = self.calibration["joints"][joint_key]
        expected_ids = {str(motor_id) for motor_id in joint["motor_ids"]}

        if set(positions) != expected_ids:
            raise ValueError("HOME motor IDs do not match the joint.")

        if joint["home"]["calibrated"] and joint["home"]["raw"] != positions:
            self._invalidate_limits(joint)

        joint["home"]["raw"] = dict(positions)
        joint["home"]["calibrated"] = True

        self._touch()

        return positions

    def verify(self):

        self._require_calibration()

        issues = []
        joints = self.robot_config.get_all_joints()

        for joint_key, joint_config in joints.items():

            if joint_key not in self.calibration["joints"]:
                issues.append(
                    f"{joint_key}: missing calibration data."
                )
                continue

            joint = self.calibration["joints"][joint_key]

            expected_ids = {
                str(motor_id)
                for motor_id in joint_config["motor_ids"]
            }

            home = joint["home"]

            if not home["calibrated"]:
                issues.append(
                    f"{joint_key}: HOME is not calibrated."
                )

            elif set(home["raw"]) != expected_ids:
                issues.append(
                    f"{joint_key}: HOME motor IDs are invalid."
                )


            direction_data = joint["direction"]

            if not direction_data["calibrated"]:
                issues.append(
                    f"{joint_key}: direction is not calibrated."
                )

            else:

                directions = direction_data["motor_directions"]

                if set(directions) != expected_ids:
                    issues.append(
                        f"{joint_key}: direction motor IDs are invalid."
                    )

                else:

                    for motor_id, direction in directions.items():

                        if direction not in (-1, 1):
                            issues.append(
                                f"{joint_key}: Motor {motor_id} "
                                "direction must be +1 or -1."
                            )

                configured_motion = joint_config.get("positive_motion")
                stored_motion = direction_data.get("positive_motion")

                if configured_motion != stored_motion:
                    issues.append(
                        f"{joint_key}: positive_motion does not match robot configuration."
                    )


            if joint_key == "joint2" and direction_data["calibrated"]:

                motor_ids = [
                    str(motor_id)
                    for motor_id in joint_config["motor_ids"]
                ]

                if len(motor_ids) == 2:

                    motor1_direction = direction_data["motor_directions"].get(
                        motor_ids[0]
                    )

                    motor2_direction = direction_data["motor_directions"].get(
                        motor_ids[1]
                    )

                    if motor1_direction == motor2_direction:
                        issues.append(
                            "joint2: shoulder motors must have opposite directions."
                        )


            limits = joint["limits"]

            if not limits["calibrated"]:
                issues.append(
                    f"{joint_key}: limits are not calibrated."
                )

            else:

                negative = limits.get("negative_limit_raw", {})
                middle = limits.get("middle_raw", {})
                positive = limits.get("positive_limit_raw", {})

                if set(negative) != expected_ids:
                    issues.append(
                        f"{joint_key}: negative limit motor IDs are invalid."
                    )

                if set(middle) != expected_ids:
                    issues.append(
                        f"{joint_key}: middle position motor IDs are invalid."
                    )

                if set(positive) != expected_ids:
                    issues.append(
                        f"{joint_key}: positive limit motor IDs are invalid."
                    )

                limit_ids_valid = (
                    set(negative) == expected_ids
                    and set(middle) == expected_ids
                    and set(positive) == expected_ids
                )

                if limit_ids_valid and direction_data["calibrated"]:

                    directions = direction_data["motor_directions"]

                    for motor_id in expected_ids:

                        if motor_id not in directions:
                            continue

                        direction = directions[motor_id]

                        negative_to_middle_delta = self._calculate_position_delta(
                            negative[motor_id],
                            middle[motor_id]
                        )

                        middle_to_positive_delta = self._calculate_position_delta(
                            middle[motor_id],
                            positive[motor_id]
                        )

                        if negative_to_middle_delta * direction <= 0:
                            issues.append(
                                f"{joint_key}: Motor {motor_id} "
                                "negative limit direction is invalid."
                            )

                        if middle_to_positive_delta * direction <= 0:
                            issues.append(
                                f"{joint_key}: Motor {motor_id} "
                                "positive limit direction is invalid."
                            )

                        if home["calibrated"] and motor_id in home["raw"]:

                            home_error = self._calculate_single_turn_error(
                                home["raw"][motor_id],
                                middle[motor_id]
                            )

                            if abs(home_error) > self.HOME_TOLERANCE_COUNTS:
                                issues.append(
                                    f"{joint_key}: Motor {motor_id} middle position "
                                    f"is {home_error} counts away from HOME."
                                )


        gripper_config = self.robot_config.get_gripper_config()
        gripper = self.calibration["gripper"]

        if gripper.get("motor_id") != gripper_config["motor_id"]:
            issues.append(
                "Gripper motor mapping is invalid."
            )

        reference = gripper["reference"]

        if not reference["calibrated"]:
            issues.append(
                "Gripper reference is not calibrated."
            )

        elif reference["raw"] is None:
            issues.append(
                "Gripper reference position is missing."
            )


        open_close = gripper["open_close"]

        if not open_close["calibrated"]:
            issues.append(
                "Gripper open/close is not calibrated."
            )

        else:

            open_raw = open_close["open_raw"]
            close_raw = open_close["close_raw"]

            if open_raw is None or close_raw is None:
                issues.append(
                    "Gripper open/close positions are missing."
                )

            elif abs(close_raw - open_raw) < 20:
                issues.append(
                    "Gripper open and close positions are too close."
                )

        return issues