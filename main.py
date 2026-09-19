from dynamixel_connection import DynamixelConnection
from dynamixel_motor import DynamixelMotor

EXPECTED_MOTOR_COUNT = 7

connection = DynamixelConnection()

if connection.open():
    
    try:

        if not connection.ping(connection.CM550_ID):
            print("CM-550 did not respond.")

        else:

            dxl_power = connection.read_1byte(
                connection.CM550_ID,
                connection.ADDR_DXL_POWER
            )

            print(f"DYNAMIXEL power state: {dxl_power}")

            if dxl_power != 1:
                print("DYNAMIXEL power is OFF.")

            else:

                scan_count = connection.scan_dynamixels()

                if scan_count is not None:

                    print(
                        f"CM-550 scan count:{scan_count}"
                    )

                access_ready = (
                    connection.prepare_dynamixel_access()
                )

                if access_ready:

                    discovered_motors = (
                        connection.discover_dynamixels()
                    )

                    print("\nDiscovered motors:")

                    for motor_id,info in discovered_motors.items():
                        print(
                            f"ID {motor_id}:",
                            f"Model={info['model_number']}"
                            f"Firmeare={info['firmware_version']}"
                            )

                    print(
                        f"\nBroadcast discovery count: "
                        f"{len(discovered_motors)}"
                    )

                    if len(discovered_motors)==EXPECTED_MOTOR_COUNT:
                        print(
                            "All expected motors"
                            "were discovered"
                        )
                    else:
                        print(
                            f"Expected"
                            f"{EXPECTED_MOTOR_COUNT}motors,"
                            f"but discovered"
                            f"{len(discovered_motors)}."
                        )

                    motor_objects = {}

                    for motor_id,info in discovered_motors.items():
                        motor = DynamixelMotor(
                            connection=connection,
                            motor_id = motor_id,
                            model_number=info["model_number"],
                            firmware_version=info["firmware_version"]
                        )
                        motor_objects[motor_id] = motor


                    print("\nMotor objects created.")

                    for motor_id, motor in motor_objects.items():

                        status = motor.read_status()

                        print(
                            f"\nMotor {motor_id}"
                        )

                        print(
                            f"  Model: "
                            f"{status['model_name']} "
                            f"({status['model_number']})"
                        )

                        print(
                            f"  Firmware: "
                            f"{status['firmware_version']}"
                        )

                        print(
                            f"  Torque: "
                            f"{status['torque_enabled']}"
                        )

                        print(
                            f"  Position raw: "
                            f"{status['position_raw']}"
                        )

                        print(
                            f"  Position deg: "
                            f"{status['position_deg']:.2f}"
                        )

                        print(
                            f"  Voltage: "
                            f"{status['voltage']} V"
                        )

                        print(
                            f"  Temperature: "
                            f"{status['temperature']} C"
                        )

                        print(
                            f"  Hardware error: "
                            f"{status['hardware_error']}"
                        )

    except ValueError as error:

        print(
            f"Motor configuration error:{error}"
        )
    
    finally:

        connection.close()