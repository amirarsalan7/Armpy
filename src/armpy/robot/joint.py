class Joint:

    POSITION_COUNTS_PER_REV = 4096

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

        self.min_angle_deg,self.max_angle_deg = self._calculate_angle_limits()

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

    def motor_raw_to_joint_angle(self,motor_id,raw_position):

        if motor_id not in self.motors:
            raise ValueError(
                f"Motor {motor_id} does not belong to {self.name}."
            )

        home = self.home_raw[motor_id]
        direction = self.motor_directions[motor_id]

        delta_raw = raw_position - home

        angle_deg = (delta_raw
                     / self._counts_per_joint_degree()
                     * direction )

        return angle_deg

    def joint_angle_to_motor_raw(self,motor_id,angle_deg):

        if motor_id not in self.motors:
            raise ValueError(
                f"Motor {motor_id} does not belong to {self.name}."
            )

        home = self.home_raw[motor_id]
        direction = self.motor_directions[motor_id]

        raw_delta = (
            angle_deg
            *self._counts_per_joint_degree()
            * direction
        )

        return round(home + raw_delta)

    def _calculate_angle_limits(self):

        negative_angles = []
        positive_angles = []

        for motor_id in self.motors:

            negative_angle = self.motor_raw_to_joint_angle(
                motor_id,
                self.negative_limit_raw[motor_id]
            )

            positive_angle = self.motor_raw_to_joint_angle(
                motor_id,
                self.positive_limit_raw[motor_id]
            )

            negative_angles.append(negative_angle)
            positive_angles.append(positive_angle)

        min_angle_deg = max(negative_angles)
        max_angle_deg = min(positive_angles)

        if min_angle_deg >= max_angle_deg:
            raise ValueError(
                f"{self.name} calibrated limits are invalid."
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

    
    