from armpy.hardware.dynamixel_motor import DynamixelMotor
from armpy.robot.joint import Joint


class RobotBuilder:

    def __init__(self, connection, hardware_inventory, robot_config, calibration_data):

        self.connection = connection
        self.hardware_inventory = hardware_inventory
        self.robot_config = robot_config
        self.calibration_data = calibration_data

        self._validate_sources()


    def _validate_sources(self):

        robot_name = self.robot_config.get_robot_name()

        if self.calibration_data.get("robot_name") != robot_name:
            raise ValueError(
                "Calibration belongs to a different robot."
            )

        config_joints = self.robot_config.get_all_joints()
        calibration_joints = self.calibration_data.get("joints")

        if not isinstance(calibration_joints, dict):
            raise ValueError(
                "Calibration joints data is missing."
            )

        if set(config_joints) != set(calibration_joints):
            raise ValueError(
                "Calibration joint mapping does not match robot configuration."
            )

        available_motor_ids = set(
            self.hardware_inventory.get_motor_ids()
        )

        for joint_key, joint_config in config_joints.items():

            configured_motor_ids = joint_config["motor_ids"]
            calibration_joint = calibration_joints[joint_key]

            if calibration_joint.get("motor_ids") != configured_motor_ids:
                raise ValueError(
                    f"{joint_key}: calibration motor mapping does not match configuration."
                )

            missing_motor_ids = (
                set(configured_motor_ids)
                - available_motor_ids
            )

            if missing_motor_ids:
                raise ValueError(
                    f"{joint_key}: missing motors {sorted(missing_motor_ids)}."
                )

            if not calibration_joint["home"]["calibrated"]:
                raise ValueError(
                    f"{joint_key}: HOME is not calibrated."
                )

            if not calibration_joint["direction"]["calibrated"]:
                raise ValueError(
                    f"{joint_key}: direction is not calibrated."
                )

            if not calibration_joint["limits"]["calibrated"]:
                raise ValueError(
                    f"{joint_key}: limits are not calibrated."
                )

        gripper_config = self.robot_config.get_gripper_config()
        gripper_motor_id = gripper_config["motor_id"]

        if gripper_motor_id not in available_motor_ids:
            raise ValueError(
                f"Gripper motor {gripper_motor_id} does not exist in hardware inventory."
            )

        gripper_calibration = self.calibration_data.get("gripper")

        if not isinstance(gripper_calibration, dict):
            raise ValueError(
                "Gripper calibration data is missing."
            )

        if gripper_calibration.get("motor_id") != gripper_motor_id:
            raise ValueError(
                "Gripper calibration motor does not match robot configuration."
            )

        if not gripper_calibration["reference"]["calibrated"]:
            raise ValueError(
                "Gripper reference is not calibrated."
            )

        if not gripper_calibration["open_close"]["calibrated"]:
            raise ValueError(
                "Gripper open/close positions are not calibrated."
            )

        return True


    def _build_motor_objects(self):

        motors = {}

        for motor_id in self.hardware_inventory.get_motor_ids():

            motor_info = self.hardware_inventory.get_motor(motor_id)
            identity = motor_info["identity"]

            motor = DynamixelMotor(
                connection=self.connection,
                motor_id=motor_id,
                model_number=identity["model_number"],
                firmware_version=identity["firmware_version"]
            )

            motors[str(motor_id)] = motor

        return motors


    def _build_joint_object(self, joint_key, motors):

        joint_config = self.robot_config.get_joint_config(joint_key)
        calibration_joint = self.calibration_data["joints"][joint_key]

        joint_motors = {
            str(motor_id): motors[str(motor_id)]
            for motor_id in joint_config["motor_ids"]
        }

        joint = Joint(
            name=joint_config["name"],
            motors=joint_motors,
            home_raw=calibration_joint["home"]["raw"],
            motor_directions=calibration_joint["direction"]["motor_directions"],
            gear_ratio=joint_config["gear_ratio"],
            negative_limit_raw=calibration_joint["limits"]["negative_limit_raw"],
            middle_raw=calibration_joint["limits"]["middle_raw"],
            positive_limit_raw=calibration_joint["limits"]["positive_limit_raw"]
        )

        return joint


    def _build_joint_objects(self, motors):

        joints = {}

        for joint_key in self.robot_config.get_all_joints():

            joints[joint_key] = self._build_joint_object(
                joint_key,
                motors
            )

        return joints


    def _build_gripper(self, motors):

        gripper_config = self.robot_config.get_gripper_config()
        gripper_calibration = self.calibration_data["gripper"]

        motor_id = gripper_config["motor_id"]

        return {
            "motor": motors[str(motor_id)],
            "config": gripper_config,
            "calibration": gripper_calibration
        }


    def build(self):

        motors = self._build_motor_objects()
        joints = self._build_joint_objects(motors)
        gripper = self._build_gripper(motors)

        return {
            "robot_name": self.robot_config.get_robot_name(),
            "motors": motors,
            "joints": joints,
            "gripper": gripper
        }