class Joint:

    POSITION_COUNTS_PER_REV = 4096
    HALF_POSITION_RANGE = 2048

    HOME_TOLERANCE_COUNTS = 100

    def __init__(
            self,
            name,
            motors,
            home_raw,
            motor_directions,
            gear_ratio,
            negative_limit_raw,
            middle_raw,
            positive_limit_raw
        ):

        self.name = name
        self.motors = motors

        self.home_raw = home_raw
        self.motor_directions = motor_directions

        self.gear_ratio = gear_ratio

        self.negative_limit_raw = negative_limit_raw
        self.middle_raw = middle_raw
        self.positive_limit_raw = positive_limit_raw

        self._validate_configuration()
        self._validate_calibration_geometry()

        self.min_angle_deg, self.max_angle_deg = (
            self._calculate_angle_limits()
        )

    def _validate_configuration(self):

        if not self.motors:
            raise ValueError(
                f"{self.name} must contain at least one motor."
            )

        if self.gear_ratio <= 0:
            raise ValueError(
                f"{self.name} gear ratio must be greater than zero."
            )

        motor_ids = set(self.motors)

        if set(self.home_raw) != motor_ids:
            raise ValueError(
                f"{self.name} HOME motor IDs do not match motors."
            )

        if set(self.motor_directions) != motor_ids:
            raise ValueError(
                f"{self.name} direction motor IDs do not match motors."
            )

        if set(self.negative_limit_raw) != motor_ids:
            raise ValueError(
                f"{self.name} negative limit motor IDs do not match motors."
            )

        if set(self.middle_raw) != motor_ids:
            raise ValueError(
                f"{self.name} middle motor IDs do not match motors."
            )

        if set(self.positive_limit_raw) != motor_ids:
            raise ValueError(
                f"{self.name} positive limit motor IDs do not match motors."
            )

        for motor_id,direction in self.motor_directions.items():

            if direction not in (-1,1):
                raise ValueError(
                    f"Motor {motor_id} direction must be +1 or -1 ."
                )

        return True

    def _counts_per_joint_degree(self):

        return(
            self.POSITION_COUNTS_PER_REV
            * self.gear_ratio
            / 360
        )

    def motor_raw_to_joint_angle(
        self,
        motor_id,
        raw_position
    ):

        if motor_id not in self.motors:
            raise ValueError(
                f"Motor {motor_id} does not belong "
                f"to Joint {self.name}."
            )

        raw_position = int(
            raw_position
        )

        # During Joint initialization, angle limits may
        # not exist yet. Calibration raw values are
        # already logical/unwrapped values.
        if not (
            hasattr(self, "min_angle_deg")
            and
            hasattr(self, "max_angle_deg")
        ):

            raise RuntimeError(
                f"{self.name}: Joint angle limits "
                "have not been initialized."
            )

        candidates = []

        for turn_offset in range(-2, 3):

            logical_raw = (
                raw_position
                + turn_offset
                * self.POSITION_COUNTS_PER_REV
            )

            angle = (
                self._logical_raw_to_joint_angle(
                    motor_id,
                    logical_raw
                )
            )

            candidates.append(
                angle
            )

        valid_candidates = [
            angle
            for angle in candidates
            if (
                self.min_angle_deg - 1.0
                <= angle
                <= self.max_angle_deg + 1.0
            )
        ]

        if len(valid_candidates) == 1:
            return valid_candidates[0]

        if valid_candidates:

            midpoint = (
                self.min_angle_deg
                + self.max_angle_deg
            ) / 2.0

            return min(
                valid_candidates,
                key=lambda angle: abs(
                    angle - midpoint
                )
            )

        # Fallback for diagnostics if the physical
        # position is outside calibrated limits.
        def distance_from_limits(angle):

            if angle < self.min_angle_deg:
                return (
                    self.min_angle_deg
                    - angle
                )

            if angle > self.max_angle_deg:
                return (
                    angle
                    - self.max_angle_deg
                )

            return 0.0

        return min(
            candidates,
            key=distance_from_limits
        )
    def _logical_raw_to_joint_angle(
        self,
        motor_id,
        logical_raw
    ):

        counts_per_degree = (
            self._counts_per_joint_degree()
        )

        direction = (
            self.motor_directions[motor_id]
        )

        delta = (
            logical_raw
            - self.home_raw[motor_id]
        )

        return (
            delta
            / counts_per_degree
            * direction
        )

    def _calibration_raw_to_joint_angle(
        self,
        motor_id,
        raw_position,
        expected_sign
    ):

        if expected_sign not in (-1, 1):
            raise ValueError(
                "Expected sign must be -1 or +1."
            )

        raw_position = int(
            raw_position
        )

        candidates = []

        for turn_offset in range(-2, 3):

            logical_raw = (
                raw_position
                + turn_offset
                * self.POSITION_COUNTS_PER_REV
            )

            angle = (
                self._logical_raw_to_joint_angle(
                    motor_id,
                    logical_raw
                )
            )

            if expected_sign * angle > 0:
                candidates.append(
                    angle
                )

        if not candidates:

            raise ValueError(
                f"{self.name}: Could not resolve "
                f"calibration position for Motor "
                f"{motor_id}."
            )

        return min(
            candidates,
            key=abs
        )

    def joint_angle_to_motor_raw(
        self,
        motor_id,
        angle_deg
    ):

        if motor_id not in self.motors:
            raise ValueError(
                f"Motor {motor_id} does not belong "
                f"to {self.name}."
            )

        home = self.home_raw[motor_id]

        direction = (
            self.motor_directions[motor_id]
        )

        raw_delta = (
            float(angle_deg)
            * self._counts_per_joint_degree()
            * direction
        )

        logical_raw = round(
            home + raw_delta
        )

        return (
            logical_raw
            % self.POSITION_COUNTS_PER_REV
        )

    def _calculate_angle_limits(self):

        negative_angles = []
        positive_angles = []

        for motor_id in self.motors:

            negative_angle = (
                self._calibration_raw_to_joint_angle(
                    motor_id,
                    self.negative_limit_raw[motor_id],
                    expected_sign=-1
                )
            )

            positive_angle = (
                self._calibration_raw_to_joint_angle(
                    motor_id,
                    self.positive_limit_raw[motor_id],
                    expected_sign=1
                )
            )

            negative_angles.append(negative_angle)
            positive_angles.append(positive_angle)

        min_angle_deg = max(negative_angles)
        max_angle_deg = min(positive_angles)

        if min_angle_deg >= max_angle_deg:
            raise ValueError(
                f"{self.name} calibrated limits are invalid."
            )

        if not (
            min_angle_deg
            <= 0.0
            <= max_angle_deg
        ):
            raise ValueError(
                f"{self.name}: calibrated limits "
                "do not contain HOME (0 deg)."
            )

        return min_angle_deg,max_angle_deg

    def is_within_limits(self,angle_deg):

        return self.min_angle_deg <= angle_deg <= self.max_angle_deg

    def check_angle_limits(self,angle_deg):

        if not self.is_within_limits(angle_deg):
            raise ValueError(
                f"{self.name} angle {angle_deg:.2f} deg is outside "
                f"calibrated limits [{self.min_angle_deg:.2f},"
                f"{self.max_angle_deg:.2f}]deg."
            )

        return True

    def calculate_goal_positions(self,angle_deg):

        self.check_angle_limits(angle_deg)

        goals = {}

        for motor_id in self.motors:
            goals[motor_id] = self.joint_angle_to_motor_raw(
                motor_id,
                angle_deg
            )

        return goals

    def calculate_joint_angle(self,raw_positions):

        if set(raw_positions) != set(self.motors):
            raise ValueError(
                f"{self.name} raw position motor IDs do not match motors."
            )

        angles =[]

        for motor_id,raw_position in raw_positions.items():

            angle = self.motor_raw_to_joint_angle(
                motor_id,
                raw_position
            )

            angles.append(angle)

        return sum(angles) / len(angles)

    
    def counts_per_joint_degree(self):

        return self._counts_per_joint_degree()

    def _calculate_single_turn_delta(self, reference_raw, position_raw):

        delta = position_raw - reference_raw

        delta = (
            (delta + self.HALF_POSITION_RANGE)
            % self.POSITION_COUNTS_PER_REV
            - self.HALF_POSITION_RANGE
        )

        return delta

    def _validate_calibration_geometry(self):

        for motor_id in self.motors:

            home = self.home_raw[motor_id]
            middle = self.middle_raw[motor_id]

            middle_error = self._calculate_single_turn_delta(
                home,
                middle
            )

            if abs(middle_error) > self.HOME_TOLERANCE_COUNTS:
                raise ValueError(
                    f"{self.name}: Motor {motor_id} limit-calibration "
                    f"middle is {middle_error} counts away from HOME."
                )

            negative_angle = (
                self._calibration_raw_to_joint_angle(
                    motor_id,
                    self.negative_limit_raw[motor_id],
                    expected_sign=-1
                )
            )

            positive_angle = (
                self._calibration_raw_to_joint_angle(
                    motor_id,
                    self.positive_limit_raw[motor_id],
                    expected_sign=1
                )
            )

            if negative_angle >= 0:
                raise ValueError(
                    f"{self.name}: Motor {motor_id} "
                    "negative limit is not below HOME."
                )

            if positive_angle <= 0:
                raise ValueError(
                    f"{self.name}: Motor {motor_id} "
                    "positive limit is not above HOME."
                )

        return True