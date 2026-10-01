import json
import shutil

from datetime import datetime
from pathlib import Path

from dynamixel_connection import DynamixelConnection
from hardware_inventory import HardwareInventory
from config.robot_config import RobotConfig
from joint_calibration import JointCalibration
from calibration_menu import CalibrationMenu


CALIBRATION_FILE = "config/joint_calibration.json"


def prepare_calibration(calibration, file_path):

    path = Path(file_path)

    if not path.exists():

        calibration.create_new()
        calibration.save(path)

        print(f"Created new calibration: {path}")

        return

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    version = data.get("schema_version")

    if version == 2:

        calibration.load(path)

        print(f"Loaded existing calibration: {path}")

        return

    if version != 1:
        raise ValueError(f"Unsupported calibration schema version: {version}")

    print("\nExisting calibration uses schema version 1.")
    print("A backup will be created before starting schema version 2.")

    answer = input(
        "Back up version 1 and start NEW calibration? [y/n]: "
    ).strip().lower()

    if answer != "y":
        raise RuntimeError("Calibration initialization cancelled.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup = path.with_name(
        f"{path.stem}_v1_backup_{timestamp}{path.suffix}"
    )

    if backup.exists():
        raise FileExistsError(f"Backup already exists: {backup}")

    shutil.copy2(path, backup)

    print(f"Old calibration backed up to: {backup}")

    calibration.create_new()
    calibration.save(path)

    print(f"Created schema version 2: {path}")


def main():

    connection = DynamixelConnection()

    if not connection.open():
        print("Could not open the robot connection.")
        return

    try:

        print("\n=== ARMPy Robot Calibration ===")

        if not connection.ping(connection.CM550_ID):
            raise RuntimeError("CM-550 did not respond.")

        if not connection.prepare_dynamixel_access():
            raise RuntimeError("DYNAMIXEL access is not ready.")

        hardware_inventory = HardwareInventory()

        robot_config = RobotConfig("config/robot_joints.json")

        calibration = JointCalibration(
            connection=connection,
            hardware_inventory=hardware_inventory,
            robot_config=robot_config
        )

        prepare_calibration(calibration, CALIBRATION_FILE)

        menu = CalibrationMenu(
            calibration=calibration,
            file_path=CALIBRATION_FILE
        )

        menu.show()

    except (RuntimeError, ValueError, KeyError, FileNotFoundError, OSError) as error:
        print(f"\nCalibration error: {error}")

    except KeyboardInterrupt:
        print("\nInterrupted. Previously accepted results remain saved.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()