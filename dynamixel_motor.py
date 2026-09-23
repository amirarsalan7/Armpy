class DynamixelMotor:

    SUPPORTED_MODEL_NUMBER = 1060
    MODEL_NAME = "XL430-W250"

    # -------------------------------------------------
    # Control Table Addresses
    # -------------------------------------------------

    ADDR_DRIVE_MODE = 10
    ADDR_OPERATING_MODE = 11

    ADDR_MAX_POSITION_LIMIT = 48
    ADDR_MIN_POSITION_LIMIT = 52

    ADDR_TORQUE_ENABLE = 64
    ADDR_HARDWARE_ERROR = 70

    ADDR_GOAL_POSITION = 116
    ADDR_PRESENT_POSITION = 132

    ADDR_PRESENT_INPUT_VOLTAGE = 144
    ADDR_PRESENT_TEMPERATURE = 146

    # -------------------------------------------------
    # Operating Modes
    # -------------------------------------------------

    MODE_VELOCITY = 1
    MODE_POSITION = 3
    MODE_EXTENDED_POSITION = 4
    MODE_PWM = 16

    # -------------------------------------------------
    # Torque
    # -------------------------------------------------

    TORQUE_OFF = 0
    TORQUE_ON = 1

    # Drive Mode Bit 3
    TORQUE_ON_BY_GOAL_MASK = 0x08

    # -------------------------------------------------
    # Position
    # -------------------------------------------------

    MIN_RAW_POSITION = 0
    MAX_RAW_POSITION = 4095

    COUNTS_PER_REVOLUTION = 4096
    DEGREES_PER_COUNT = 360.0 / COUNTS_PER_REVOLUTION

    # -------------------------------------------------
    # Constructor
    # -------------------------------------------------

    def __init__(
        self,
        connection,
        motor_id,
        model_number,
        firmware_version
    ):
        self.connection = connection
        self.motor_id = motor_id
        self.model_number = model_number
        self.firmware_version = firmware_version

        if self.model_number != self.SUPPORTED_MODEL_NUMBER:
            raise ValueError(
                f"Unsupported DYNAMIXEL model: "
                f"{self.model_number}"
            )

    # -------------------------------------------------
    # Basic Communication
    # -------------------------------------------------

    def ping(self):

        return self.connection.ping(
            self.motor_id
        )

    # -------------------------------------------------
    # Operating / Drive Mode
    # -------------------------------------------------

    def read_operating_mode(self):

        return self.connection.read_1byte(
            self.motor_id,
            self.ADDR_OPERATING_MODE
        )

    def read_drive_mode(self):

        return self.connection.read_1byte(
            self.motor_id,
            self.ADDR_DRIVE_MODE
        )

    # -------------------------------------------------
    # Torque
    # -------------------------------------------------

    def read_torque_enabled(self):

        return self.connection.read_1byte(
            self.motor_id,
            self.ADDR_TORQUE_ENABLE
        )

    def enable_torque(self):

        success = self.connection.write_1byte(
            self.motor_id,
            self.ADDR_TORQUE_ENABLE,
            self.TORQUE_ON
        )

        if success:
            print(
                f"Motor {self.motor_id}: torque enabled."
            )

        return success

    def disable_torque(self):

        success = self.connection.write_1byte(
            self.motor_id,
            self.ADDR_TORQUE_ENABLE,
            self.TORQUE_OFF
        )

        if success:
            print(
                f"Motor {self.motor_id}: torque disabled."
            )

        return success

    def _require_torque_off(self):

        torque = self.read_torque_enabled()

        if torque is None:
            raise RuntimeError(
                f"Motor {self.motor_id}: "
                "could not read torque state."
            )

        if torque != self.TORQUE_OFF:
            raise RuntimeError(
                f"Motor {self.motor_id}: "
                "torque must be OFF before "
                "changing EEPROM configuration."
            )

    # -------------------------------------------------
    # Operating Mode Configuration
    # -------------------------------------------------

    def set_operating_mode(self, mode):

        valid_modes = {
            self.MODE_VELOCITY,
            self.MODE_POSITION,
            self.MODE_EXTENDED_POSITION,
            self.MODE_PWM,
        }

        if mode not in valid_modes:
            raise ValueError(
                f"Invalid operating mode: {mode}"
            )

        self._require_torque_off()

        success = self.connection.write_1byte(
            self.motor_id,
            self.ADDR_OPERATING_MODE,
            mode
        )

        if not success:
            return False

        actual_mode = self.read_operating_mode()

        if actual_mode != mode:
            raise RuntimeError(
                f"Motor {self.motor_id}: "
                "operating mode verification failed."
            )

        return True

    # -------------------------------------------------
    # Present Position
    # -------------------------------------------------

    def read_present_position_raw(self):

        raw_position = self.connection.read_4byte(
            self.motor_id,
            self.ADDR_PRESENT_POSITION
        )

        if raw_position is None:
            return None

        # Convert unsigned 32-bit to signed 32-bit.
        if raw_position >= 2**31:
            raw_position -= 2**32

        return raw_position

    def raw_to_motor_degrees(self, raw_position):

        return (
            raw_position
            * self.DEGREES_PER_COUNT
        )

    def read_present_position_degrees(self):

        raw_position = self.read_present_position_raw()

        if raw_position is None:
            return None

        return self.raw_to_motor_degrees(
            raw_position
        )

    def motor_degrees_to_raw(self, degrees):

        raw_position = round(
            degrees / self.DEGREES_PER_COUNT
        )

        if not (
            self.MIN_RAW_POSITION
            <= raw_position
            <= self.MAX_RAW_POSITION
        ):
            raise ValueError(
                "Motor angle is outside "
                "single-turn range."
            )

        return raw_position

    # -------------------------------------------------
    # Voltage / Temperature / Error
    # -------------------------------------------------

    def read_input_voltage(self):

        raw_voltage = self.connection.read_2byte(
            self.motor_id,
            self.ADDR_PRESENT_INPUT_VOLTAGE
        )

        if raw_voltage is None:
            return None

        return raw_voltage * 0.1

    def read_temperature(self):

        return self.connection.read_1byte(
            self.motor_id,
            self.ADDR_PRESENT_TEMPERATURE
        )

    def read_hardware_error(self):

        return self.connection.read_1byte(
            self.motor_id,
            self.ADDR_HARDWARE_ERROR
        )

    # -------------------------------------------------
    # Position Limits
    # -------------------------------------------------

    def read_position_limits(self):

        min_position = self.connection.read_4byte(
            self.motor_id,
            self.ADDR_MIN_POSITION_LIMIT
        )

        max_position = self.connection.read_4byte(
            self.motor_id,
            self.ADDR_MAX_POSITION_LIMIT
        )

        if (
            min_position is None
            or max_position is None
        ):
            return None

        return {
            "min": min_position,
            "max": max_position,
        }

    def set_position_limits(
        self,
        min_position,
        max_position
    ):

        if not (
            self.MIN_RAW_POSITION
            <= min_position
            < max_position
            <= self.MAX_RAW_POSITION
        ):
            raise ValueError(
                "Invalid position limits. "
                "Expected: "
                "0 <= min < max <= 4095."
            )

        self._require_torque_off()

        success_max = self.connection.write_4byte(
            self.motor_id,
            self.ADDR_MAX_POSITION_LIMIT,
            max_position
        )

        if not success_max:
            return False

        success_min = self.connection.write_4byte(
            self.motor_id,
            self.ADDR_MIN_POSITION_LIMIT,
            min_position
        )

        if not success_min:
            return False

        limits = self.read_position_limits()

        if limits is None:
            return False

        if (
            limits["min"] != min_position
            or limits["max"] != max_position
        ):
            raise RuntimeError(
                f"Motor {self.motor_id}: "
                "position limit verification failed."
            )

        return True

    # -------------------------------------------------
    # Goal Position
    # -------------------------------------------------

    def read_goal_position_raw(self):

        return self.connection.read_4byte(
            self.motor_id,
            self.ADDR_GOAL_POSITION
        )

    def validate_goal_position_raw(
        self,
        goal_position
    ):

        mode = self.read_operating_mode()

        if mode != self.MODE_POSITION:
            raise RuntimeError(
                f"Motor {self.motor_id}: "
                "motor is not in Position Control Mode."
            )

        limits = self.read_position_limits()

        if limits is None:
            raise RuntimeError(
                f"Motor {self.motor_id}: "
                "could not read position limits."
            )

        if not (
            limits["min"]
            <= goal_position
            <= limits["max"]
        ):
            raise ValueError(
                f"Motor {self.motor_id}: "
                f"goal {goal_position} is outside "
                f"[{limits['min']}, {limits['max']}]."
            )

        return True

    def set_goal_position_raw(
        self,
        goal_position
    ):

        self.validate_goal_position_raw(
            goal_position
        )

        drive_mode = self.read_drive_mode()

        if drive_mode is None:
            raise RuntimeError(
                f"Motor {self.motor_id}: "
                "could not read Drive Mode."
            )

        if drive_mode & self.TORQUE_ON_BY_GOAL_MASK:
            raise RuntimeError(
                f"Motor {self.motor_id}: "
                "Torque On by Goal Update is enabled. "
                "Disable this feature before motion."
            )

        torque = self.read_torque_enabled()

        if torque != self.TORQUE_ON:
            raise RuntimeError(
                f"Motor {self.motor_id}: "
                "torque is not enabled."
            )

        return self.connection.write_4byte(
            self.motor_id,
            self.ADDR_GOAL_POSITION,
            goal_position
        )

    # -------------------------------------------------
    # Configuration / Status
    # -------------------------------------------------

    def read_configuration(self):

        return {
            "id": self.motor_id,
            "drive_mode": self.read_drive_mode(),
            "operating_mode": self.read_operating_mode(),
            "torque_enabled": self.read_torque_enabled(),
            "position_limits": self.read_position_limits(),
            "goal_position": self.read_goal_position_raw(),
            "present_position": self.read_present_position_raw(),
        }

    def read_status(self):

        position_raw = self.read_present_position_raw()

        if position_raw is None:
            position_deg = None
        else:
            position_deg = self.raw_to_motor_degrees(
                position_raw
            )

        return {
            "id": self.motor_id,
            "model_number": self.model_number,
            "model_name": self.MODEL_NAME,
            "firmware_version": self.firmware_version,
            "torque_enabled": self.read_torque_enabled(),
            "position_raw": position_raw,
            "position_deg": position_deg,
            "voltage": self.read_input_voltage(),
            "temperature": self.read_temperature(),
            "hardware_error": self.read_hardware_error(),
        }