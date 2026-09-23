from dynamixel_connection import DynamixelConnection
from dynamixel_motor import DynamixelMotor


EXPECTED_MOTOR_COUNT = 7


connection = DynamixelConnection()


if connection.open():

    try:

        # -------------------------------------------------
        # 1. Check CM-550
        # -------------------------------------------------

        print("\n--- CM-550 Check ---")

        if not connection.ping(connection.CM550_ID):

            print("CM-550 did not respond.")

        else:

            # -------------------------------------------------
            # 2. Check DYNAMIXEL Power
            # -------------------------------------------------

            print("\n--- DYNAMIXEL Power Check ---")

            dxl_power = connection.read_1byte(
                connection.CM550_ID,
                connection.ADDR_DXL_POWER
            )

            print(
                f"DYNAMIXEL power state: {dxl_power}"
            )

            if dxl_power != 1:

                print("DYNAMIXEL power is OFF.")

            else:

                print("DYNAMIXEL power is ON.")

                # -------------------------------------------------
                # 3. Scan DYNAMIXEL Bus
                # -------------------------------------------------

                print("\n--- DYNAMIXEL Scan ---")

                scan_count = (
                    connection.scan_dynamixels()
                )

                if scan_count is None:

                    print(
                        "Could not scan DYNAMIXEL motors."
                    )

                else:

                    print(
                        f"CM-550 scan count: "
                        f"{scan_count}"
                    )

                    if scan_count == EXPECTED_MOTOR_COUNT:

                        print(
                            "Expected number of motors detected."
                        )

                    else:

                        print(
                            f"WARNING: Expected "
                            f"{EXPECTED_MOTOR_COUNT} motors, "
                            f"but CM-550 detected "
                            f"{scan_count}."
                        )

                    # -------------------------------------------------
                    # 4. Prepare DYNAMIXEL Access
                    # -------------------------------------------------

                    print(
                        "\n--- DYNAMIXEL Access Check ---"
                    )

                    access_ready = (
                        connection.prepare_dynamixel_access()
                    )

                    if not access_ready:

                        print(
                            "DYNAMIXEL access is not ready."
                        )

                    else:

                        # -------------------------------------------------
                        # 5. Discover Individual Motors
                        # -------------------------------------------------

                        print(
                            "\n--- Motor Discovery ---"
                        )

                        discovered_motors = (
                            connection.discover_dynamixels()
                        )

                        print(
                            "\nDiscovered motors:"
                        )

                        for motor_id, info in discovered_motors.items():

                            print(
                                f"ID {motor_id}: "
                                f"Model="
                                f"{info['model_number']}, "
                                f"Firmware="
                                f"{info['firmware_version']}"
                            )

                        print(
                            f"\nBroadcast discovery count: "
                            f"{len(discovered_motors)}"
                        )

                        if (
                            len(discovered_motors)
                            == EXPECTED_MOTOR_COUNT
                        ):

                            print(
                                "All expected motors "
                                "were discovered."
                            )

                        else:

                            print(
                                f"WARNING: Expected "
                                f"{EXPECTED_MOTOR_COUNT} motors, "
                                f"but discovered "
                                f"{len(discovered_motors)}."
                            )

                        # -------------------------------------------------
                        # 6. Create Motor Objects
                        # -------------------------------------------------

                        print(
                            "\n--- Creating Motor Objects ---"
                        )

                        motor_objects = {}

                        for motor_id, info in discovered_motors.items():

                            motor = DynamixelMotor(
                                connection=connection,
                                motor_id=motor_id,
                                model_number=info[
                                    "model_number"
                                ],
                                firmware_version=info[
                                    "firmware_version"
                                ]
                            )

                            motor_objects[motor_id] = motor

                        print(
                            f"{len(motor_objects)} "
                            "motor objects created."
                        )

                        # -------------------------------------------------
                        # 7. Read Motor Status
                        # -------------------------------------------------

                        print(
                            "\n--- Motor Status ---"
                        )

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

                            if (
                                status["position_deg"]
                                is not None
                            ):

                                print(
                                    f"  Position deg: "
                                    f"{status['position_deg']:.2f}"
                                )

                            else:

                                print(
                                    "  Position deg: N/A"
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

                        # -------------------------------------------------
                        # 8. Read Motor Configuration
                        # -------------------------------------------------

                        print(
                            "\n--- Motor Configuration ---"
                        )

                        for motor_id, motor in motor_objects.items():

                            config = (
                                motor.read_configuration()
                            )

                            print(
                                f"\nMotor {motor_id}"
                            )

                            print(
                                f"  Drive mode: "
                                f"{config['drive_mode']}"
                            )

                            print(
                                f"  Operating mode: "
                                f"{config['operating_mode']}"
                            )

                            print(
                                f"  Torque enabled: "
                                f"{config['torque_enabled']}"
                            )

                            limits = (
                                config["position_limits"]
                            )

                            if limits is not None:

                                print(
                                    f"  Min position: "
                                    f"{limits['min']}"
                                )

                                print(
                                    f"  Max position: "
                                    f"{limits['max']}"
                                )

                            else:

                                print(
                                    "  Position limits: N/A"
                                )

                            print(
                                f"  Goal position: "
                                f"{config['goal_position']}"
                            )

                            print(
                                f"  Present position: "
                                f"{config['present_position']}"
                            )

                        # -------------------------------------------------
                        # 9. Finished
                        # -------------------------------------------------

                        print(
                            "\n--- Startup Check Finished ---"
                        )

                        print(
                            "Connection, motors, status, "
                            "and configuration checked."
                        )

                        print(
                            "No motion command was sent."
                        )


    except (ValueError, RuntimeError) as error:

        print(
            f"\nERROR: {error}"
        )


    finally:

        print(
            "\nClosing connection..."
        )

        connection.close()