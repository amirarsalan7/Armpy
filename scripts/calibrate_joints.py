from src.armpy.hardware.dynamixel_connection import (DynamixelConnection)
from src.armpy.hardware.hardware_inventory import (HardwareInventory)
from src.armpy.calibration.joint_calibration import (JointCalibration)
from armpy.config.robot_config import (RobotConfig)


CALIBRATION_FILE = ("config/joint_calibration.json")

connection = DynamixelConnection()

if connection.open():
    try:

        print("\n---joint Home Calibration ---")

        if not connection.ping(connection.CM550_ID):
            raise RuntimeError("CM-550 did not respond.")

        access_ready = connection.prepare_dynamixel_access()

        if not access_ready:
            raise RuntimeError(
                "Dynamixel access is not ready.")

        hardware_inventory = HardwareInventory()

        robot_config = RobotConfig(
            "config/robot_joints.json"
        )

        calibration  = JointCalibration(
            connection=connection,
            hardware_inventory= hardware_inventory,
            robot_config=robot_config
        )

        print()
        print(
            "This program does not command robot motion."
        )

        print(
            "Place the robot in the desired HOME pose."
        )

        print(
            "Make sure the robot is mechanically supported." 
        )

        print("Do not manually force a joint while its torque is enabled.")

        input("\nPress Enter when the robot is in HOME position . . .")

        data = calibration.capture_home()

        print("\nCaptured HOME position:")

        for joint_name, joint_data in data["joints"].items():
            print(f"\n{joint_name}:")

            for motor_id,position in joint_data["home_raw"].items():
                print(
                    f"Motor {motor_id}: {position}"
                )

        print("\nGripper:")

        print(f"Motor {data["gripper"]["motor_id"]}:"
                f"{data["gripper"]["reference_raw"]}"
            )

        output_path = (
            calibration.save(CALIBRATION_FILE)
        )

        print("\nCalibration saved to:")

        print(output_path)

    except( RuntimeError,ValueError,OSError)as error:
        print( f"\nCalibration error : {error}")

    finally:
        connection.close()