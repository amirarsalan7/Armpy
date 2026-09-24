import json

from datetime import datetime
from pathlib import Path

from dynamixel_motor import DynamixelMotor


class HardwareDiscovery:

    def __init__(
        self,
        connection,
        expected_motor_count=None
    ):

        self.connection = connection

        self.expected_motor_count = (
            expected_motor_count
        )

        self.inventory = None


    def _build_motor_record(
        self,
        motor_id,
        motor_info
    ):

        motor = DynamixelMotor(
            connection=self.connection,
            motor_id=motor_id,
            model_number=motor_info[
                "model_number"
            ],
            firmware_version=motor_info[
                "firmware_version"
            ]
        )

        status = motor.read_status()

        config = motor.read_configuration()


        motor_record = {

            "identity": {

                "id": motor_id,

                "model_number": (
                    status["model_number"]
                ),

                "model_name": (
                    status["model_name"]
                ),

                "firmware_version": (
                    status["firmware_version"]
                )
            },


            "configuration": {

                "drive_mode": (
                    config["drive_mode"]
                ),

                "operating_mode": (
                    config["operating_mode"]
                ),

                "position_limits": (
                    config["position_limits"]
                )
            },


            "snapshot": {

                "torque_enabled": (
                    status["torque_enabled"]
                ),

                "position_raw": (
                    status["position_raw"]
                ),

                "position_deg": (
                    status["position_deg"]
                ),

                "goal_position": (
                    config["goal_position"]
                ),

                "present_position": (
                    config["present_position"]
                ),

                "voltage": (
                    status["voltage"]
                ),

                "temperature": (
                    status["temperature"]
                ),

                "hardware_error": (
                    status["hardware_error"]
                )
            }
        }


        return motor_record


    def discover(self):

        if not self.connection.ping(
            self.connection.CM550_ID
        ):

            raise RuntimeError(
                "CM-550 did not respond."
            )


        dxl_power = (
            self.connection.read_1byte(
                self.connection.CM550_ID,
                self.connection.ADDR_DXL_POWER
            )
        )


        if dxl_power != 1:

            raise RuntimeError(
                "DYNAMIXEL power is OFF."
            )


        scan_count = (
            self.connection.scan_dynamixels()
        )


        if scan_count is None:

            raise RuntimeError(
                "CM-550 DYNAMIXEL scan failed."
            )


        access_ready = (
            self.connection
            .prepare_dynamixel_access()
        )


        if not access_ready:

            raise RuntimeError(
                "DYNAMIXEL USB access "
                "is not ready."
            )


        discovered_motors = (
            self.connection
            .discover_dynamixels()
        )


        motors = {}


        for (
            motor_id,
            motor_info
        ) in discovered_motors.items():

            motors[str(motor_id)] = (
                self._build_motor_record(
                    motor_id,
                    motor_info
                )
            )


        controller = {

            "type": "CM-550",

            "device_id": (
                self.connection.CM550_ID
            ),

            "device_name": (
                self.connection.device_name
            ),

            "baudrate": (
                self.connection.baudrate
            ),

            "protocol_version": (
                self.connection
                .protocol_version
            ),

            "dxl_power_state": dxl_power,

            "mode": (
                self.connection.read_1byte(
                    self.connection.CM550_ID,
                    self.connection.ADDR_MODE_NUMBER
                )
            ),

            "bypass_port": (
                self.connection.read_1byte(
                    self.connection.CM550_ID,
                    self.connection
                    .ADDR_BYPASS_PORT
                )
            )
        }


        bus = {

            "scan_count": scan_count,

            "broadcast_discovery_count": (
                len(discovered_motors)
            ),

            "expected_motor_count": (
                self.expected_motor_count
            )
        }


        if (
            self.expected_motor_count
            is not None
        ):

            bus["count_matches_expected"] = (
                len(discovered_motors)
                == self.expected_motor_count
            )


        self.inventory = {

            "schema_version": 1,

            "generated_at": (
                datetime.now()
                .astimezone()
                .isoformat(
                    timespec="seconds"
                )
            ),

            "controller": controller,

            "bus": bus,

            "motors": motors
        }


        return self.inventory


    def save(
        self,
        file_path
    ):

        if self.inventory is None:

            raise RuntimeError(
                "Run discover() before save()."
            )


        path = Path(file_path)


        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        with path.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.inventory,
                file,
                indent=4
            )


        return path