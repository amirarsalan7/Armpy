import json
import unittest

from pathlib import Path

from armpy.robot.joint import Joint


PROJECT_ROOT = Path(__file__).resolve().parents[1]

ROBOT_CONFIG_FILE = PROJECT_ROOT / "src" / "armpy" / "config" / "robot_joints.json"
CALIBRATION_FILE = PROJECT_ROOT / "data" / "joint_calibration.json"

class TestJoint(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        with ROBOT_CONFIG_FILE.open("r", encoding="utf-8") as file:
            cls.robot_config = json.load(file)

        with CALIBRATION_FILE.open("r", encoding="utf-8") as file:
            cls.calibration = json.load(file)


    def build_joint(self, joint_key):

        joint_config = self.robot_config["joints"][joint_key]
        joint_calibration = self.calibration["joints"][joint_key]

        motors = {
            str(motor_id): object()
            for motor_id in joint_config["motor_ids"]
        }

        return Joint(
            name=joint_config["name"],
            motors=motors,
            home_raw=joint_calibration["home"]["raw"],
            motor_directions=joint_calibration["direction"]["motor_directions"],
            gear_ratio=joint_config["gear_ratio"],
            negative_limit_raw=joint_calibration["limits"]["negative_limit_raw"],
            middle_raw=joint_calibration["limits"]["middle_raw"],
            positive_limit_raw=joint_calibration["limits"]["positive_limit_raw"]
        )


    def get_test_angles(self, joint):

        self.assertLess(joint.min_angle_deg, 0.0)
        self.assertGreater(joint.max_angle_deg, 0.0)

        negative_angle = joint.min_angle_deg / 2.0
        positive_angle = joint.max_angle_deg / 2.0

        return negative_angle, positive_angle


    def test_joint_attributes(self):

        for joint_key in ("joint1", "joint2"):

            joint = self.build_joint(joint_key)

            joint_config = self.robot_config["joints"][joint_key]
            joint_calibration = self.calibration["joints"][joint_key]

            expected_motor_ids = {
                str(motor_id)
                for motor_id in joint_config["motor_ids"]
            }

            self.assertEqual(joint.name, joint_config["name"])
            self.assertEqual(set(joint.motors), expected_motor_ids)

            self.assertEqual(
                joint.home_raw,
                joint_calibration["home"]["raw"]
            )

            self.assertEqual(
                joint.motor_directions,
                joint_calibration["direction"]["motor_directions"]
            )

            self.assertEqual(
                joint.gear_ratio,
                joint_config["gear_ratio"]
            )

            self.assertEqual(
                joint.negative_limit_raw,
                joint_calibration["limits"]["negative_limit_raw"]
            )

            self.assertEqual(
                joint.middle_raw,
                joint_calibration["limits"]["middle_raw"]
            )

            self.assertEqual(
                joint.positive_limit_raw,
                joint_calibration["limits"]["positive_limit_raw"]
            )

            self.assertLess(
                joint.min_angle_deg,
                joint.max_angle_deg
            )


    def test_counts_per_joint_degree(self):

        for joint_key in ("joint1", "joint2"):

            joint = self.build_joint(joint_key)

            expected = (
                Joint.POSITION_COUNTS_PER_REV
                * joint.gear_ratio
                / 360.0
            )

            self.assertAlmostEqual(
                joint._counts_per_joint_degree(),
                expected,
                places=6
            )


    def test_home_is_zero_angle(self):

        for joint_key in ("joint1", "joint2"):

            joint = self.build_joint(joint_key)

            for motor_id in joint.motors:

                angle = joint.motor_raw_to_joint_angle(
                    motor_id,
                    joint.home_raw[motor_id]
                )

                self.assertAlmostEqual(
                    angle,
                    0.0,
                    places=6
                )


    def test_angle_to_raw_and_back(self):

        for joint_key in ("joint1", "joint2"):

            joint = self.build_joint(joint_key)

            negative_angle, positive_angle = self.get_test_angles(joint)

            for requested_angle in (
                negative_angle,
                positive_angle
            ):

                for motor_id in joint.motors:

                    raw_position = joint.joint_angle_to_motor_raw(
                        motor_id,
                        requested_angle
                    )

                    calculated_angle = joint.motor_raw_to_joint_angle(
                        motor_id,
                        raw_position
                    )

                    self.assertAlmostEqual(
                        calculated_angle,
                        requested_angle,
                        delta=0.1
                    )


    def test_calculate_goal_positions(self):

        for joint_key in ("joint1", "joint2"):

            joint = self.build_joint(joint_key)

            negative_angle, positive_angle = self.get_test_angles(joint)

            for requested_angle in (
                negative_angle,
                positive_angle
            ):

                goals = joint.calculate_goal_positions(
                    requested_angle
                )

                self.assertEqual(
                    set(goals),
                    set(joint.motors)
                )

                for motor_id in joint.motors:

                    expected_raw = joint.joint_angle_to_motor_raw(
                        motor_id,
                        requested_angle
                    )

                    self.assertEqual(
                        goals[motor_id],
                        expected_raw
                    )


    def test_calculate_joint_angle(self):

        for joint_key in ("joint1", "joint2"):

            joint = self.build_joint(joint_key)

            negative_angle, positive_angle = self.get_test_angles(joint)

            for requested_angle in (
                negative_angle,
                positive_angle
            ):

                raw_positions = joint.calculate_goal_positions(
                    requested_angle
                )

                calculated_angle = joint.calculate_joint_angle(
                    raw_positions
                )

                self.assertAlmostEqual(
                    calculated_angle,
                    requested_angle,
                    delta=0.1
                )


    def test_angles_inside_limits(self):

        for joint_key in ("joint1", "joint2"):

            joint = self.build_joint(joint_key)

            negative_angle, positive_angle = self.get_test_angles(joint)

            self.assertTrue(
                joint.is_within_limits(negative_angle)
            )

            self.assertTrue(
                joint.is_within_limits(positive_angle)
            )

            self.assertTrue(
                joint.check_angle_limits(negative_angle)
            )

            self.assertTrue(
                joint.check_angle_limits(positive_angle)
            )


    def test_angles_outside_limits(self):

        for joint_key in ("joint1", "joint2"):

            joint = self.build_joint(joint_key)

            below_minimum = joint.min_angle_deg - 5.0
            above_maximum = joint.max_angle_deg + 5.0

            self.assertFalse(
                joint.is_within_limits(below_minimum)
            )

            self.assertFalse(
                joint.is_within_limits(above_maximum)
            )

            with self.assertRaises(ValueError):
                joint.check_angle_limits(below_minimum)

            with self.assertRaises(ValueError):
                joint.check_angle_limits(above_maximum)

            with self.assertRaises(ValueError):
                joint.calculate_goal_positions(below_minimum)

            with self.assertRaises(ValueError):
                joint.calculate_goal_positions(above_maximum)


    def test_joint2_motor_directions(self):

        joint = self.build_joint("joint2")

        motor_ids = list(joint.motors)

        self.assertEqual(
            len(motor_ids),
            2
        )

        first_direction = joint.motor_directions[motor_ids[0]]
        second_direction = joint.motor_directions[motor_ids[1]]

        self.assertEqual(
            first_direction,
            -second_direction
        )


    def test_joint2_generates_two_motor_goals(self):

        joint = self.build_joint("joint2")

        negative_angle, positive_angle = self.get_test_angles(joint)

        negative_goals = joint.calculate_goal_positions(
            negative_angle
        )

        positive_goals = joint.calculate_goal_positions(
            positive_angle
        )

        self.assertEqual(
            len(negative_goals),
            2
        )

        self.assertEqual(
            len(positive_goals),
            2
        )

        for motor_id in joint.motors:

            self.assertNotEqual(
                negative_goals[motor_id],
                positive_goals[motor_id]
            )


    def test_invalid_gear_ratio(self):

        joint = self.build_joint("joint1")

        with self.assertRaises(ValueError):

            Joint(
                name=joint.name,
                motors=joint.motors,
                home_raw=joint.home_raw,
                motor_directions=joint.motor_directions,
                gear_ratio=0,
                negative_limit_raw=joint.negative_limit_raw,
                middle_raw=joint.middle_raw,
                positive_limit_raw=joint.positive_limit_raw
            )

        with self.assertRaises(ValueError):

            Joint(
                name=joint.name,
                motors=joint.motors,
                home_raw=joint.home_raw,
                motor_directions=joint.motor_directions,
                gear_ratio=-1,
                negative_limit_raw=joint.negative_limit_raw,
                middle_raw=joint.middle_raw,
                positive_limit_raw=joint.positive_limit_raw
            )


    def test_invalid_motor_mapping(self):

        joint = self.build_joint("joint2")

        bad_directions = dict(joint.motor_directions)

        removed_motor_id = next(iter(bad_directions))
        bad_directions.pop(removed_motor_id)

        with self.assertRaises(ValueError):

            Joint(
                name=joint.name,
                motors=joint.motors,
                home_raw=joint.home_raw,
                motor_directions=bad_directions,
                gear_ratio=joint.gear_ratio,
                negative_limit_raw=joint.negative_limit_raw,
                middle_raw=joint.middle_raw,
                positive_limit_raw=joint.positive_limit_raw
            )

        bad_home = dict(joint.home_raw)

        removed_motor_id = next(iter(bad_home))
        bad_home.pop(removed_motor_id)

        with self.assertRaises(ValueError):

            Joint(
                name=joint.name,
                motors=joint.motors,
                home_raw=bad_home,
                motor_directions=joint.motor_directions,
                gear_ratio=joint.gear_ratio,
                negative_limit_raw=joint.negative_limit_raw,
                middle_raw=joint.middle_raw,
                positive_limit_raw=joint.positive_limit_raw
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)