from dynamixel_connection import DynamixelConnection


connection = DynamixelConnection()


if connection.open():

    try:

        if connection.ping(connection.CM550_ID):

            dxl_power = connection.read_1byte(
                connection.CM550_ID,
                connection.ADDR_DXL_POWER
            )

            print(f"DYNAMIXEL power state: {dxl_power}")

            if dxl_power == 1:

                motor_count = connection.scan_dynamixels()

                if motor_count == 7:
                    print(
                        "All 7 DYNAMIXEL motors were detected."
                    )

                elif motor_count is not None:
                    print(
                        f"Expected 7 motors, "
                        f"but detected {motor_count}."
                    )

            else:
                print("DYNAMIXEL power is OFF.")

    finally:

        connection.close()