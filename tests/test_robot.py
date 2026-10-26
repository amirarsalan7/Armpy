import json
import unittest

from pathlib import Path

from armpy.robot.joint import Joint
from armpy.robot.robot import Robot


PROJECT_ROOT = Path(__file__).resolve().parents[1]

ROBOT_CONFIG_FILE = PROJECT_ROOT / "src" / "armpy" / "config" / "robot_joints.json"
CALIBRATION_FILE = PROJECT_ROOT / "data" / "joint_calibration.json"


class FakeMotor:

    def __init__(self, motor_id, position_raw):

        self.motor_id = motor_id
        self.position_raw = position_raw


    def read_present_position_raw(self):

        return self.position_raw


class TestRobot(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        with ROBOT_CONFIG_FILE.open("r", encoding="utf-8") as file:
            cls.robot_config = json.load(file)

        with CALIBRATION_FILE.open("r", encoding="utf-8") as file:
            cls.calibration = json.load(file)


    def setUp(self):

        positions = {}

        for joint_data in self.calibration["joints"].values():
            positions.update(
                joint_data["home"]["raw"]
            )

        gripper_data = self.calibration["gripper"]

        positions[str(gripper_data["motor_id"])] = (
            gripper_data["reference"]["raw"]
        )

        self.motors = {
            motor_id: FakeMotor(
                int(motor_id),
                position
            )
            for motor_id, position in positions.items()
        }

        self.joints = {}

        for joint_key, joint_config in self.robot_config["joints"].items():

            calibration_joint = self.calibration["joints"][joint_key]

            joint_motors = {
                str(motor_id): self.motors[str(motor_id)]
                for motor_id in joint_config["motor_ids"]
            }

            self.joints[joint_key] = Joint(
                name=joint_config["name"],
                motors=joint_motors,
                home_raw=calibration_joint["home"]["raw"],
                motor_directions=calibration_joint["direction"]["motor_directions"],
                gear_ratio=joint_config["gear_ratio"],
                negative_limit_raw=calibration_joint["limits"]["negative_limit_raw"],
                middle_raw=calibration_joint["limits"]["middle_raw"],
                positive_limit_raw=calibration_joint["limits"]["positive_limit_raw"]
            )

        gripper_config = self.robot_config["gripper"]

        self.gripper = {
            "motor": self.motors[str(gripper_config["motor_id"])],
            "config": gripper_config,
            "calibration": self.calibration["gripper"]
        }

        self.robot = Robot(
            name=self.robot_config["robot_name"],
            motors=self.motors,
            joints=self.joints,
            gripper=self.gripper
        )


    def test_robot_name(self):

        self.assertEqual(
            self.robot.name,
            self.robot_config["robot_name"]
        )


    def test_get_joint(self):

        joint1 = self.robot.get_joint("joint1")
        joint2 = self.robot.get_joint("joint2")

        self.assertIs(
            joint1,
            self.joints["joint1"]
        )

        self.assertIs(
            joint2,
            self.joints["joint2"]
        )


    def test_invalid_joint_is_rejected(self):

        with self.assertRaises(ValueError):
            self.robot.get_joint("joint99")


    def test_get_motor(self):

        self.assertIs(
            self.robot.get_motor(1),
            self.motors["1"]
        )

        self.assertIs(
            self.robot.get_motor("4"),
            self.motors["4"]
        )


    def test_invalid_motor_is_rejected(self):

        with self.assertRaises(ValueError):
            self.robot.get_motor(99)


    def test_joint_names(self):

        self.assertEqual(
            set(self.robot.get_joint_names()),
            set(self.robot_config["joints"])
        )


    def test_read_joint_raw_positions(self):

        positions = self.robot.read_joint_raw_positions(
            "joint2"
        )

        expected = self.calibration["joints"]["joint2"]["home"]["raw"]

        self.assertEqual(
            positions,
            expected
        )


    def test_home_angles_are_zero(self):

        for joint_key in self.joints:

            angle = self.robot.read_joint_angle(
                joint_key
            )

            self.assertAlmostEqual(
                angle,
                0.0,
                places=6
            )


    def test_read_nonzero_joint_angle(self):

        joint = self.joints["joint1"]

        target_angle = joint.max_angle_deg / 2.0

        goals = joint.calculate_goal_positions(
            target_angle
        )

        for motor_id, raw_goal in goals.items():
            self.motors[motor_id].position_raw = raw_goal

        angle = self.robot.read_joint_angle(
            "joint1"
        )

        self.assertAlmostEqual(
            angle,
            target_angle,
            delta=0.1
        )


    def test_read_all_joint_angles(self):

        angles = self.robot.read_all_joint_angles()

        self.assertEqual(
            set(angles),
            set(self.joints)
        )

        for angle in angles.values():

            self.assertAlmostEqual(
                angle,
                0.0,
                places=6
            )


    def test_gripper_raw_position(self):

        position = self.robot.read_gripper_raw_position()

        self.assertEqual(
            position,
            self.calibration["gripper"]["reference"]["raw"]
        )


    def test_read_state(self):

        state = self.robot.read_state()

        self.assertEqual(
            state["robot_name"],
            self.robot_config["robot_name"]
        )

        self.assertEqual(
            set(state["joints"]),
            set(self.joints)
        )

        self.assertIn(
            "raw_position",
            state["gripper"]
        )

        for joint_state in state["joints"].values():

            self.assertIn(
                "raw_positions",
                joint_state
            )

            self.assertIn(
                "angle_deg",
                joint_state
            )


    def test_broken_motor_object_graph_is_rejected(self):

        bad_joints = dict(self.joints)

        joint1 = bad_joints["joint1"]

        original_motor = joint1.motors["1"]

        joint1.motors["1"] = FakeMotor(
            1,
            original_motor.position_raw
        )

        with self.assertRaises(ValueError):

            Robot(
                name=self.robot_config["robot_name"],
                motors=self.motors,
                joints=bad_joints,
                gripper=self.gripper
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)