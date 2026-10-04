from src.armpy.hardware.dynamixel_connection import DynamixelConnection
from src.armpy.hardware.hardware_inventory import HardwareInventory
from src.armpy.calibration.joint_calibration import JointCalibration
from armpy.config.robot_config import RobotConfig

CALIBRATION_FILE = "data/joint_calibration.json"

MIN_MOVEMENT_COUNTS = 20

connection = DynamixelConnection()

if connection.open():
    try:
        print("\n---Motor Direction---")

        if not connection.ping(connection.CM550_ID):

            raise RuntimeError("CM-550 did not respond.")

        access_ready = connection.prepare_dynamixel_access()

        if not access_ready:
            raise RuntimeError("DYNAMIXEL access is not ready.")

        hardware_inventory = HardwareInventory()

        robot_config = RobotConfig("config/robot_joints.json")

        calibration = JointCalibration(
            connection=connection,
            hardware_inventory=hardware_inventory,
            robot_config=robot_config
        )

        calibration.load(CALIBRATION_FILE)

        joints = robot_config.get_all_joints()

        print()
        print("Each joint will be calibrated separately.")

        print("Move the requested joint only a small amount.")

        print("The direction you move will be defined "
              "as the POSITIVE joint direction.")

        for joint_key,joint_data in joints.items():

            print("\n----------------------------------")
            print(f"joint:{joint_key}")
            print(f"Name:{joint_data['name']}")
            print(f"Motors:{joint_data['motor_ids']}")

            calibration.check_joint_torque_off(joint_key)

            input("\nPlace this joint at a safe starting position "
                  "and press Enter . . .")

            before_positions = (
                calibration.read_joint_positions(joint_key)
            )

            print(f"BEFORE:{before_positions}")

            input(
                "\nMove this joint a small amount in the "
                "POSITIVE direction, then press Enter . . ."
            )

            after_positions = (
                calibration.read_joint_positions(joint_key)
            )

            print(f"AFTER:{after_positions}")

            directions,deltas = (
                calibration.calculate_joint_directions(
                    before_positions,
                    after_positions,
                    MIN_MOVEMENT_COUNTS
                )
            )

            calibration.store_joint_direction(
                joint_key=joint_key,
                before_positions=before_positions,
                after_positions=after_positions,
                deltas=deltas,
                directions=directions   
            )

            calibration.save(CALIBRATION_FILE)

            print("\nDirection result:")

            for motor_id in directions:
                print(
                    f"Motor {motor_id} "
                    f"delta={deltas[motor_id]} "
                    f"direction={directions[motor_id]}"
                )

            input("\nReturn the joint to a safe position, "
                  "then press Enter to continue . . .")

            print("\nMotor direction calibration completed.")

            print(f"Calibration saved to :{CALIBRATION_FILE}")

    except(RuntimeError,ValueError,FileNotFoundError,OSError)as error:
        print(f"\nCalibration error:{error}")

    finally:

        connection.close()