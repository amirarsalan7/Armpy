import copy
import json
import unittest

from pathlib import Path

from armpy.config.robot_config import RobotConfig
from armpy.hardware.dynamixel_motor import DynamixelMotor
from armpy.hardware.hardware_inventory import HardwareInventory
from armpy.robot.joint import Joint
from armpy.robot.robot_builder import RobotBuilder


PROJECT_ROOT = Path(__file__).resolve().parents[1]

ROBOT_CONFIG_FILE = PROJECT_ROOT / "src" / "armpy" / "config" / "robot_joints.json"
HARDWARE_INVENTORY_FILE = PROJECT_ROOT / "data" / "hardware_inventory.json"
CALIBRATION_FILE = PROJECT_ROOT / "data" / "joint_calibration.json"


class TestRobotBuilder(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.connection = object()

        cls.hardware_inventory = HardwareInventory(
            HARDWARE_INVENTORY_FILE
        )

        cls.robot_config = RobotConfig(
            ROBOT_CONFIG_FILE
        )

        with CALIBRATION_FILE.open("r", encoding="utf-8") as file:
            cls.calibration_data = json.load(file)

        cls.builder = RobotBuilder(
            connection=cls.connection,
            hardware_inventory=cls.hardware_inventory,
            robot_config=cls.robot_config,
            calibration_data=cls.calibration_data
        )

        cls.components = cls.builder.build()


    def test_robot_name(self):

        self.assertEqual(
            self.components["robot_name"],
            self.robot_config.get_robot_name()
        )


    def test_all_motors_created(self):

        expected_ids = {
            str(motor_id)
            for motor_id in self.hardware_inventory.get_motor_ids()
        }

        self.assertEqual(
            set(self.components["motors"]),
            expected_ids
        )

        self.assertEqual(
            len(self.components["motors"]),
            7
        )


    def test_motor_object_types(self):

        for motor in self.components["motors"].values():
            self.assertIsInstance(
                motor,
                DynamixelMotor
            )


    def test_all_joints_created(self):

        expected_joints = set(
            self.robot_config.get_all_joints()
        )

        self.assertEqual(
            set(self.components["joints"]),
            expected_joints
        )

        self.assertEqual(
            len(self.components["joints"]),
            5
        )


    def test_joint_object_types(self):

        for joint in self.components["joints"].values():
            self.assertIsInstance(
                joint,
                Joint
            )


    def test_joint_motor_mapping(self):

        for joint_key, joint_config in self.robot_config.get_all_joints().items():

            joint = self.components["joints"][joint_key]

            expected_motor_ids = {
                str(motor_id)
                for motor_id in joint_config["motor_ids"]
            }

            self.assertEqual(
                set(joint.motors),
                expected_motor_ids
            )


    def test_joint2_uses_motor2_and_motor3(self):

        joint2 = self.components["joints"]["joint2"]

        self.assertEqual(
            set(joint2.motors),
            {"2", "3"}
        )


    def test_joint_reuses_motor_objects(self):

        for joint in self.components["joints"].values():

            for motor_id, motor in joint.motors.items():

                self.assertIs(
                    motor,
                    self.components["motors"][motor_id]
                )


    def test_joint_calibration_is_attached(self):

        for joint_key, joint in self.components["joints"].items():

            calibration_joint = self.calibration_data["joints"][joint_key]

            self.assertEqual(
                joint.home_raw,
                calibration_joint["home"]["raw"]
            )

            self.assertEqual(
                joint.motor_directions,
                calibration_joint["direction"]["motor_directions"]
            )

            self.assertEqual(
                joint.negative_limit_raw,
                calibration_joint["limits"]["negative_limit_raw"]
            )

            self.assertEqual(
                joint.positive_limit_raw,
                calibration_joint["limits"]["positive_limit_raw"]
            )


    def test_gripper_motor(self):

        gripper = self.components["gripper"]

        self.assertEqual(
            gripper["motor"].motor_id,
            7
        )

        self.assertIs(
            gripper["motor"],
            self.components["motors"]["7"]
        )


    def test_gripper_calibration(self):

        gripper = self.components["gripper"]

        self.assertTrue(
            gripper["calibration"]["reference"]["calibrated"]
        )

        self.assertTrue(
            gripper["calibration"]["open_close"]["calibrated"]
        )


    def test_invalid_robot_name_is_rejected(self):

        bad_calibration = copy.deepcopy(
            self.calibration_data
        )

        bad_calibration["robot_name"] = "WRONG_ROBOT"

        with self.assertRaises(ValueError):

            RobotBuilder(
                connection=self.connection,
                hardware_inventory=self.hardware_inventory,
                robot_config=self.robot_config,
                calibration_data=bad_calibration
            )


    def test_invalid_joint_mapping_is_rejected(self):

        bad_calibration = copy.deepcopy(
            self.calibration_data
        )

        bad_calibration["joints"]["joint2"]["motor_ids"] = [2]

        with self.assertRaises(ValueError):

            RobotBuilder(
                connection=self.connection,
                hardware_inventory=self.hardware_inventory,
                robot_config=self.robot_config,
                calibration_data=bad_calibration
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)