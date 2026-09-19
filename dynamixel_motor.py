class DynamixelMotor:

    SUPPORTED_MODEL_NUMBER = 1060
    MODEL_NAME = "XL430-W250"

    ADDR_TORQUE_ENABLE = 64
    ADDR_HARDWARE_ERROR = 70
    ADDR_PRESENT_POSITION = 132
    ADDR_PRESENT_INPUT_VOLTAGE = 144
    ADDR_PRESENT_TEMPERATURE = 146

    POSITION_DEG_PER_PULSE = 360.0 / 4096.0

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

    def ping(self):
        return self.connection.ping(
            self.motor_id
        )

    def read_torque_enabled(self):
        return self.connection.read_1byte(
            self.motor_id,
            self.ADDR_TORQUE_ENABLE
        )

    def read_present_position_raw(self):

        raw_position = self.connection.read_4byte(
            self.motor_id,
            self.ADDR_PRESENT_POSITION
        )

        if raw_position is None:
            return None

        if raw_position >= 2**31:
            raw_position -= 2**32

        return raw_position

    def read_present_position_degrees(self):

        raw_position = self.read_present_position_raw()

        if raw_position is None:
            return None

        return (
            raw_position
            * self.POSITION_DEG_PER_PULSE
        )

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

    def read_status(self):

        position_raw = self.read_present_position_raw()

        if position_raw is None:
            position_deg = None
        else:
            position_deg = (
                position_raw
                * self.POSITION_DEG_PER_PULSE
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