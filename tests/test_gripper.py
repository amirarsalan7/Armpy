import unittest

from armpy.robot.gripper import Gripper


class FakeConnection:

    def __init__(self, motor):

        self.motor = motor

        self.sync_write_calls = []


    def sync_write(
        self,
        address,
        data_length,
        values_by_id
    ):

        self.sync_write_calls.append(
            {
                "address": address,
                "data_length": data_length,
                "values_by_id": dict(
                    values_by_id
                )
            }
        )

        if (
            address
            == self.motor.ADDR_TORQUE_ENABLE
        ):

            motor_id = int(
                self.motor.motor_id
            )

            if motor_id in values_by_id:

                self.motor.torque_enabled = (
                    values_by_id[
                        motor_id
                    ]
                )

        return True


class FakeMotor:

    COUNTS_PER_REVOLUTION = 4096

    MODE_POSITION = 3

    TORQUE_OFF = 0
    TORQUE_ON = 1

    TORQUE_ON_BY_GOAL_MASK = 0x08

    ADDR_TORQUE_ENABLE = 64

    PROFILE_VELOCITY_UNIT_RPM = 0.229


    def __init__(
        self,
        motor_id=7,
        position_raw=1500
    ):

        self.motor_id = motor_id

        self.position_raw = int(
            position_raw
        )

        self.torque_enabled = (
            self.TORQUE_ON
        )

        self.profile_velocity_raw = 0

        self.staged_goal_raw = None

        self.goal_write_count = 0

        self.connection = (
            FakeConnection(
                self
            )
        )


    def read_present_position_raw(
        self
    ):

        return self.position_raw


    def validate_goal_position_raw(
        self,
        goal_raw
    ):

        if not isinstance(
            goal_raw,
            int
        ):

            raise TypeError(
                "Goal raw must be an integer."
            )

        if not (
            0
            <= goal_raw
            < self.COUNTS_PER_REVOLUTION
        ):

            raise ValueError(
                "Invalid raw goal."
            )

        return True


    def read_operating_mode(self):

        return self.MODE_POSITION


    def read_drive_mode(self):

        return 0


    def read_hardware_error(self):

        return 0


    def read_torque_enabled(self):

        return self.torque_enabled


    def rpm_to_profile_velocity_raw(
        self,
        rpm
    ):

        return max(
            1,
            round(
                float(rpm)
                / self.PROFILE_VELOCITY_UNIT_RPM
            )
        )


    def set_profile_velocity_raw(
        self,
        raw
    ):

        self.profile_velocity_raw = int(
            raw
        )

        return True


    def stage_goal_position_raw(
        self,
        goal_raw
    ):

        self.validate_goal_position_raw(
            goal_raw
        )

        self.staged_goal_raw = (
            goal_raw
        )

        return True


    def set_goal_position_raw(
        self,
        goal_raw
    ):

        self.validate_goal_position_raw(
            goal_raw
        )

        self.goal_write_count += 1

        # Simulate immediate motor movement.
        self.position_raw = (
            goal_raw
        )

        return True


class TestGripper(
    unittest.TestCase
):

    def setUp(self):

        self.motor = FakeMotor(
            motor_id=7,
            position_raw=1500
        )

        self.config = {
            "motor_id": 7
        }

        self.calibration = {
            "motor_id": 7,

            "reference": {
                "raw": 1500
            },

            "open": {
                "raw": 2000
            },

            "closed": {
                "raw": 1000
            }
        }

        self.gripper = Gripper(
            motor=self.motor,
            config=self.config,
            calibration=self.calibration
        )


    def test_gripper_motor_is_reused(
        self
    ):

        self.assertIs(
            self.gripper.motor,
            self.motor
        )


    def test_motion_is_calibrated(
        self
    ):

        self.assertTrue(
            self.gripper
            .is_motion_calibrated()
        )


    def test_zero_percent_is_closed(
        self
    ):

        goal_raw = (
            self.gripper
            .calculate_goal_raw(
                0
            )
        )

        self.assertEqual(
            goal_raw,
            1000
        )


    def test_full_percent_is_open(
        self
    ):

        goal_raw = (
            self.gripper
            .calculate_goal_raw(
                100
            )
        )

        self.assertEqual(
            goal_raw,
            2000
        )


    def test_half_opening(
        self
    ):

        goal_raw = (
            self.gripper
            .calculate_goal_raw(
                50
            )
        )

        self.assertEqual(
            goal_raw,
            1500
        )


    def test_quarter_opening(
        self
    ):

        goal_raw = (
            self.gripper
            .calculate_goal_raw(
                25
            )
        )

        self.assertEqual(
            goal_raw,
            1250
        )


    def test_invalid_negative_opening_is_rejected(
        self
    ):

        with self.assertRaises(
            ValueError
        ):

            self.gripper.calculate_goal_raw(
                -1
            )


    def test_opening_above_100_is_rejected(
        self
    ):

        with self.assertRaises(
            ValueError
        ):

            self.gripper.calculate_goal_raw(
                101
            )


    def test_non_numeric_opening_is_rejected(
        self
    ):

        with self.assertRaises(
            TypeError
        ):

            self.gripper.calculate_goal_raw(
                "50"
            )


    def test_open_command(
        self
    ):

        result = (
            self.gripper.open()
        )

        self.assertEqual(
            result["goal_raw"],
            2000
        )

        self.assertEqual(
            result["final_raw"],
            2000
        )

        self.assertEqual(
            self.motor.position_raw,
            2000
        )


    def test_close_command(
        self
    ):

        result = (
            self.gripper.close()
        )

        self.assertEqual(
            result["goal_raw"],
            1000
        )

        self.assertEqual(
            result["final_raw"],
            1000
        )

        self.assertEqual(
            self.motor.position_raw,
            1000
        )


    def test_set_opening(
        self
    ):

        result = (
            self.gripper
            .set_opening(
                25
            )
        )

        self.assertEqual(
            result[
                "opening_percent"
            ],
            25.0
        )

        self.assertEqual(
            result[
                "goal_raw"
            ],
            1250
        )

        self.assertEqual(
            self.motor.position_raw,
            1250
        )


    def test_open_command_sets_profile_velocity(
        self
    ):

        result = (
            self.gripper.open(
                velocity_rpm=10.0
            )
        )

        expected_raw = (
            self.motor
            .rpm_to_profile_velocity_raw(
                10.0
            )
        )

        self.assertEqual(
            self.motor
            .profile_velocity_raw,
            expected_raw
        )

        self.assertEqual(
            result[
                "profile_velocity_raw"
            ],
            expected_raw
        )


    def test_default_velocity(
        self
    ):

        self.assertEqual(
            self.gripper
            .default_velocity_rpm,
            self.gripper
            .DEFAULT_VELOCITY_RPM
        )


    def test_set_default_velocity(
        self
    ):

        updated = (
            self.gripper
            .set_default_velocity_rpm(
                12.0
            )
        )

        self.assertEqual(
            updated,
            12.0
        )

        self.assertEqual(
            self.gripper
            .default_velocity_rpm,
            12.0
        )


    def test_invalid_low_velocity_is_rejected(
        self
    ):

        with self.assertRaises(
            ValueError
        ):

            self.gripper.set_default_velocity_rpm(0.1)


    def test_invalid_high_velocity_is_rejected(
        self
    ):

        with self.assertRaises(
            ValueError
        ):

            self.gripper.set_default_velocity_rpm(100.0)


    def test_read_state(
        self
    ):

        state = (
            self.gripper
            .read_state()
        )

        self.assertEqual(
            state[
                "motor_id"
            ],
            7
        )

        self.assertEqual(
            state[
                "raw_position"
            ],
            1500
        )

        self.assertAlmostEqual(
            state[
                "opening_percent"
            ],
            50.0
        )

        self.assertTrue(
            state[
                "motion_calibrated"
            ]
        )

        self.assertEqual(
            state[
                "open_raw"
            ],
            2000
        )

        self.assertEqual(
            state[
                "closed_raw"
            ],
            1000
        )


    def test_hold(
        self
    ):

        self.motor.position_raw = (
            1600
        )

        raw = (
            self.gripper.hold()
        )

        self.assertEqual(
            raw,
            1600
        )

        self.assertEqual(
            self.motor.position_raw,
            1600
        )


    def test_torque_already_on_is_preserved(
        self
    ):

        self.motor.torque_enabled = (
            self.motor.TORQUE_ON
        )

        self.gripper.open()

        self.assertEqual(
            self.motor.torque_enabled,
            self.motor.TORQUE_ON
        )


    def test_torque_off_is_enabled_safely(
        self
    ):

        self.motor.torque_enabled = (
            self.motor.TORQUE_OFF
        )

        self.motor.position_raw = (
            1500
        )

        result = (
            self.gripper.open()
        )

        self.assertEqual(
            self.motor.staged_goal_raw,
            1500
        )

        self.assertEqual(
            self.motor.torque_enabled,
            self.motor.TORQUE_ON
        )

        self.assertEqual(
            result[
                "goal_raw"
            ],
            2000
        )

        self.assertGreater(
            len(
                self.motor
                .connection
                .sync_write_calls
            ),
            0
        )


    def test_missing_motion_calibration(
        self
    ):

        gripper = Gripper(
            motor=self.motor,
            config=self.config,
            calibration={
                "motor_id": 7,

                "reference": {
                    "raw": 1500
                }
            }
        )

        self.assertFalse(
            gripper
            .is_motion_calibrated()
        )

        with self.assertRaises(
            RuntimeError
        ):

            gripper.open()


    def test_partial_calibration_is_rejected(
        self
    ):

        with self.assertRaises(
            ValueError
        ):

            Gripper(
                motor=self.motor,
                config=self.config,
                calibration={
                    "motor_id": 7,

                    "open": {
                        "raw": 2000
                    }
                }
            )


    def test_equal_open_and_closed_are_rejected(
        self
    ):

        with self.assertRaises(
            ValueError
        ):

            Gripper(
                motor=self.motor,
                config=self.config,
                calibration={
                    "motor_id": 7,

                    "open": {
                        "raw": 1500
                    },

                    "closed": {
                        "raw": 1500
                    }
                }
            )


    def test_configuration_motor_mismatch_is_rejected(
        self
    ):

        with self.assertRaises(
            ValueError
        ):

            Gripper(
                motor=self.motor,
                config={
                    "motor_id": 99
                },
                calibration=(
                    self.calibration
                )
            )


    def test_calibration_motor_mismatch_is_rejected(
        self
    ):

        bad_calibration = {
            "motor_id": 99,

            "open": {
                "raw": 2000
            },

            "closed": {
                "raw": 1000
            }
        }

        with self.assertRaises(
            ValueError
        ):

            Gripper(
                motor=self.motor,
                config=self.config,
                calibration=bad_calibration
            )


    def test_wrap_around_mapping(
        self
    ):

        gripper = Gripper(
            motor=self.motor,
            config=self.config,
            calibration={
                "motor_id": 7,

                "open": {
                    "raw": 100
                },

                "closed": {
                    "raw": 4000
                }
            }
        )

        goal = (
            gripper
            .calculate_goal_raw(
                50
            )
        )

        self.assertEqual(
            goal,
            2
        )


    def test_wrap_around_opening_percent(
        self
    ):

        gripper = Gripper(
            motor=self.motor,
            config=self.config,
            calibration={
                "motor_id": 7,

                "open": {
                    "raw": 100
                },

                "closed": {
                    "raw": 4000
                }
            }
        )

        percent = (
            gripper
            .calculate_opening_percent(
                2
            )
        )

        self.assertAlmostEqual(
            percent,
            50.0,
            delta=1.0
        )


if __name__ == "__main__":

    unittest.main(
        verbosity=2
    )