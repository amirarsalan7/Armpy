import time


class Gripper:

    DEFAULT_VELOCITY_RPM = 5.0

    MIN_VELOCITY_RPM = 0.5
    MAX_VELOCITY_RPM = 30.0

    POSITION_TOLERANCE_RAW = 20

    MOTION_TIMEOUT_SCALE = 2.0
    MOTION_TIMEOUT_MARGIN_S = 1.0
    MIN_MOTION_TIMEOUT_S = 2.0


    def __init__(
        self,
        motor,
        config,
        calibration
    ):

        self.motor = motor

        self.config = (
            config
            if isinstance(config, dict)
            else {}
        )

        self.calibration = (
            calibration
            if isinstance(calibration, dict)
            else {}
        )

        self.default_velocity_rpm = (
            self.DEFAULT_VELOCITY_RPM
        )

        self.open_raw = (
            self._read_calibration_raw(
                "open"
            )
        )

        self.closed_raw = (
            self._read_calibration_raw(
                "closed"
            )
        )

        self._validate_configuration()


    def _read_calibration_raw(
        self,
        key
    ):

        direct_data = (
            self.calibration.get(
                key
            )
        )

        if isinstance(
            direct_data,
            dict
        ):

            raw = direct_data.get(
                "raw"
            )

            if raw is not None:
                return int(raw)

        open_close = (
            self.calibration.get(
                "open_close"
            )
        )

        if not isinstance(
            open_close,
            dict
        ):

            return None

        raw_key = (
            f"{key}_raw"
        )

        raw = open_close.get(
            raw_key
        )

        if raw is not None:
            return int(raw)

        nested_data = (
            open_close.get(
                key
            )
        )

        if isinstance(
            nested_data,
            dict
        ):

            raw = nested_data.get(
                "raw"
            )

            if raw is not None:
                return int(raw)

        return None


    def _validate_configuration(self):

        motor_id = str(
            self.motor.motor_id
        )

        configured_motor_id = (
            self.config.get(
                "motor_id"
            )
        )

        if configured_motor_id is not None:

            if str(
                configured_motor_id
            ) != motor_id:

                raise ValueError(
                    "Gripper configuration "
                    "motor ID does not match "
                    "the Gripper motor object."
                )

        calibration_motor_id = (
            self.calibration.get(
                "motor_id"
            )
        )

        if calibration_motor_id is not None:

            if str(
                calibration_motor_id
            ) != motor_id:

                raise ValueError(
                    "Gripper calibration "
                    "motor ID does not match "
                    "the Gripper motor object."
                )

        if (
            self.open_raw is None
            and self.closed_raw is None
        ):
            return True

        if (
            self.open_raw is None
            or self.closed_raw is None
        ):

            raise ValueError(
                "Gripper calibration must "
                "contain both open.raw "
                "and closed.raw."
            )

        self._validate_raw_position(
            self.open_raw
        )

        self._validate_raw_position(
            self.closed_raw
        )

        if (
            self.open_raw
            == self.closed_raw
        ):

            raise ValueError(
                "Gripper open and closed "
                "positions cannot be equal."
            )

        return True


    def _validate_raw_position(
        self,
        raw_position
    ):

        counts = getattr(
            self.motor,
            "COUNTS_PER_REVOLUTION",
            4096
        )

        if not (
            0
            <= int(raw_position)
            < counts
        ):

            raise ValueError(
                f"Gripper raw position "
                f"{raw_position} is outside "
                f"[0, {counts - 1}]."
            )

        return True


    def is_motion_calibrated(self):

        return (
            self.open_raw is not None
            and self.closed_raw is not None
        )


    def _require_motion_calibration(
        self
    ):

        if not self.is_motion_calibrated():

            raise RuntimeError(
                "Gripper movement calibration "
                "is missing. Calibrate open "
                "and closed positions first."
            )

        return True


    def _shortest_raw_delta(
        self,
        reference_raw,
        position_raw
    ):

        counts = getattr(
            self.motor,
            "COUNTS_PER_REVOLUTION",
            4096
        )

        half_range = (
            counts // 2
        )

        delta = (
            int(position_raw)
            - int(reference_raw)
        )

        return (
            (
                delta
                + half_range
            )
            % counts
            - half_range
        )


    def calculate_goal_raw(
        self,
        opening_percent
    ):

        self._require_motion_calibration()

        if (
            isinstance(
                opening_percent,
                bool
            )
            or not isinstance(
                opening_percent,
                (int, float)
            )
        ):

            raise TypeError(
                "Gripper opening must be "
                "an int or float."
            )

        opening_percent = float(
            opening_percent
        )

        if not (
            0.0
            <= opening_percent
            <= 100.0
        ):

            raise ValueError(
                "Gripper opening must be "
                "between 0 and 100 percent."
            )

        span = (
            self._shortest_raw_delta(
                self.closed_raw,
                self.open_raw
            )
        )

        logical_goal = (
            self.closed_raw
            + (
                span
                * opening_percent
                / 100.0
            )
        )

        counts = getattr(
            self.motor,
            "COUNTS_PER_REVOLUTION",
            4096
        )

        goal_raw = (
            round(logical_goal)
            % counts
        )

        self._validate_raw_position(
            goal_raw
        )

        return goal_raw


    def calculate_opening_percent(
        self,
        raw_position
    ):

        if not self.is_motion_calibrated():
            return None

        span = (
            self._shortest_raw_delta(
                self.closed_raw,
                self.open_raw
            )
        )

        if span == 0:

            raise RuntimeError(
                "Gripper calibration span "
                "cannot be zero."
            )

        current_delta = (
            self._shortest_raw_delta(
                self.closed_raw,
                raw_position
            )
        )

        percent = (
            current_delta
            / span
            * 100.0
        )

        return max(
            0.0,
            min(
                100.0,
                percent
            )
        )


    def _validate_velocity(
        self,
        velocity_rpm
    ):

        if (
            isinstance(
                velocity_rpm,
                bool
            )
            or not isinstance(
                velocity_rpm,
                (int, float)
            )
        ):

            raise TypeError(
                "Gripper velocity must "
                "be numeric."
            )

        velocity_rpm = float(
            velocity_rpm
        )

        if not (
            self.MIN_VELOCITY_RPM
            <= velocity_rpm
            <= self.MAX_VELOCITY_RPM
        ):

            raise ValueError(
                "Gripper velocity must be "
                f"between "
                f"{self.MIN_VELOCITY_RPM:.2f} "
                f"and "
                f"{self.MAX_VELOCITY_RPM:.2f} RPM."
            )

        return velocity_rpm


    def set_default_velocity_rpm(
        self,
        velocity_rpm
    ):

        velocity_rpm = (
            self._validate_velocity(
                velocity_rpm
            )
        )

        self.default_velocity_rpm = (
            velocity_rpm
        )

        return (
            self.default_velocity_rpm
        )


    def read_raw_position(self):

        position = (
            self.motor
            .read_present_position_raw()
        )

        if position is None:

            raise RuntimeError(
                "Could not read "
                "gripper position."
            )

        return int(
            position
        )


    def _preflight_goal(
        self,
        goal_raw
    ):

        self.motor.validate_goal_position_raw(
            goal_raw
        )

        operating_mode = (
            self.motor.read_operating_mode()
        )

        if operating_mode is None:

            raise RuntimeError(
                "Could not read gripper "
                "Operating Mode."
            )

        if (
            operating_mode
            != self.motor.MODE_POSITION
        ):

            raise RuntimeError(
                "Gripper motor must be in "
                "Position Control Mode."
            )

        drive_mode = (
            self.motor.read_drive_mode()
        )

        if drive_mode is None:

            raise RuntimeError(
                "Could not read gripper "
                "Drive Mode."
            )

        if (
            drive_mode
            & self.motor.TORQUE_ON_BY_GOAL_MASK
        ):

            raise RuntimeError(
                "Gripper motor has "
                "Torque On by Goal Update enabled."
            )

        hardware_error = (
            self.motor.read_hardware_error()
        )

        if hardware_error is None:

            raise RuntimeError(
                "Could not read gripper "
                "Hardware Error Status."
            )

        if hardware_error != 0:

            raise RuntimeError(
                "Gripper motor hardware error: "
                f"{hardware_error}."
            )

        return True


    def _set_profile_velocity(
        self,
        velocity_rpm
    ):

        velocity_rpm = (
            self._validate_velocity(
                velocity_rpm
            )
        )

        profile_raw = (
            self.motor
            .rpm_to_profile_velocity_raw(
                velocity_rpm
            )
        )

        if not (
            self.motor
            .set_profile_velocity_raw(
                profile_raw
            )
        ):

            raise RuntimeError(
                "Could not set gripper "
                "Profile Velocity."
            )

        return profile_raw


    def _prepare_torque(self):

        torque = (
            self.motor
            .read_torque_enabled()
        )

        if torque is None:

            raise RuntimeError(
                "Could not read gripper "
                "torque state."
            )

        if torque == self.motor.TORQUE_ON:

            return False

        current_raw = (
            self.read_raw_position()
        )

        if not (
            self.motor
            .stage_goal_position_raw(
                current_raw
            )
        ):

            raise RuntimeError(
                "Could not stage current "
                "gripper position."
            )

        self.motor.connection.sync_write(
            address=(
                self.motor
                .ADDR_TORQUE_ENABLE
            ),
            data_length=1,
            values_by_id={
                int(
                    self.motor.motor_id
                ):
                self.motor.TORQUE_ON
            }
        )

        torque = (
            self.motor
            .read_torque_enabled()
        )

        if torque != self.motor.TORQUE_ON:

            raise RuntimeError(
                "Gripper torque enable "
                "verification failed."
            )

        return True


    def _calculate_timeout(
        self,
        current_raw,
        goal_raw,
        velocity_rpm
    ):

        distance_counts = abs(
            self._shortest_raw_delta(
                current_raw,
                goal_raw
            )
        )

        counts = getattr(
            self.motor,
            "COUNTS_PER_REVOLUTION",
            4096
        )

        counts_per_second = (
            velocity_rpm
            * counts
            / 60.0
        )

        expected_time = (
            distance_counts
            / counts_per_second
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


    def _hold_raw_position(
        self,
        raw_position
    ):

        raw_position = int(
            raw_position
        )

        self.motor.validate_goal_position_raw(
            raw_position
        )

        if not (
            self.motor.set_goal_position_raw(
                raw_position
            )
        ):

            raise RuntimeError(
                "Could not hold gripper position."
            )

        return raw_position


    def _wait_for_target(
        self,
        goal_raw,
        velocity_rpm
    ):

        start_raw = (
            self.read_raw_position()
        )

        timeout = (
            self._calculate_timeout(
                start_raw,
                goal_raw,
                velocity_rpm
            )
        )

        deadline = (
            time.monotonic()
            + timeout
        )

        while True:

            current_raw = (
                self.read_raw_position()
            )

            error_raw = abs(
                self._shortest_raw_delta(
                    current_raw,
                    goal_raw
                )
            )

            if (
                error_raw
                <= self.POSITION_TOLERANCE_RAW
            ):

                return current_raw

            if (
                time.monotonic()
                >= deadline
            ):

                self._hold_raw_position(
                    current_raw
                )

                raise TimeoutError(
                    "Gripper motion timeout. "
                    f"Goal={goal_raw}, "
                    f"actual={current_raw}, "
                    f"error={error_raw} counts. "
                    "Current position was held."
                )

            time.sleep(
                0.05
            )


    def move_to_raw(
        self,
        goal_raw,
        velocity_rpm=None,
        wait=True
    ):

        self._require_motion_calibration()

        goal_raw = int(
            goal_raw
        )

        self._validate_raw_position(
            goal_raw
        )

        self._preflight_goal(
            goal_raw
        )

        if velocity_rpm is None:

            velocity_rpm = (
                self.default_velocity_rpm
            )

        velocity_rpm = (
            self._validate_velocity(
                velocity_rpm
            )
        )

        profile_raw = (
            self._set_profile_velocity(
                velocity_rpm
            )
        )

        self._prepare_torque()

        if not (
            self.motor.set_goal_position_raw(
                goal_raw
            )
        ):

            raise RuntimeError(
                "Could not write gripper "
                "Goal Position."
            )

        final_raw = None

        if wait:

            final_raw = (
                self._wait_for_target(
                    goal_raw,
                    velocity_rpm
                )
            )

        return {
            "goal_raw": goal_raw,
            "final_raw": final_raw,
            "velocity_rpm": velocity_rpm,
            "profile_velocity_raw": (
                profile_raw
            )
        }


    def set_opening(
        self,
        opening_percent,
        velocity_rpm=None,
        wait=True
    ):

        goal_raw = (
            self.calculate_goal_raw(
                opening_percent
            )
        )

        result = (
            self.move_to_raw(
                goal_raw,
                velocity_rpm=velocity_rpm,
                wait=wait
            )
        )

        result[
            "opening_percent"
        ] = float(
            opening_percent
        )

        return result


    def open(
        self,
        velocity_rpm=None,
        wait=True
    ):

        return self.set_opening(
            100.0,
            velocity_rpm=velocity_rpm,
            wait=wait
        )


    def close(
        self,
        velocity_rpm=None,
        wait=True
    ):

        return self.set_opening(
            0.0,
            velocity_rpm=velocity_rpm,
            wait=wait
        )


    def hold(self):

        current_raw = (
            self.read_raw_position()
        )

        self._preflight_goal(
            current_raw
        )

        self._prepare_torque()

        self._hold_raw_position(
            current_raw
        )

        return current_raw


    def read_state(self):

        raw_position = (
            self.read_raw_position()
        )

        torque = (
            self.motor
            .read_torque_enabled()
        )

        return {
            "motor_id": (
                self.motor.motor_id
            ),
            "raw_position": (
                raw_position
            ),
            "opening_percent": (
                self.calculate_opening_percent(
                    raw_position
                )
            ),
            "torque_enabled": (
                torque
            ),
            "motion_calibrated": (
                self.is_motion_calibrated()
            ),
            "open_raw": (
                self.open_raw
            ),
            "closed_raw": (
                self.closed_raw
            ),
            "velocity_rpm": (
                self.default_velocity_rpm
            )
        }