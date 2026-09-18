from dynamixel_connection import DynamixelConnection

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

                    motors = (
                        connection.discover_dynamixels()
                    )

                    print("\nDiscovered motors:")

                    for motor_id,info in motors.items():
                        print(
                            f"ID {motor_id}:",
                            f"Model={info['model_number']}"
                            f"Firmeare={info['firmware_version']}"
                            )

                    print(
                        f"\nBroadcast discovery count: "
                        f"{len(motors)}"
                    )

                    if len(motors)==EXPECTED_MOTOR_COUNT:
                        print(
                            "All expected motors"
                            "were discovered"
                        )
                    else:
                        print(
                            f"Expected"
                            f"{EXPECTED_MOTOR_COUNT}motors,"
                            f"but discovered"
                            f"{len(motors)}."
                        )

    finally:

        connection.close()