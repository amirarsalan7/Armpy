import json

from pathlib import Path

from armpy.hardware.dynamixel_connection import DynamixelConnection
from armpy.hardware.hardware_inventory import HardwareInventory
from armpy.config.robot_config import RobotConfig
from armpy.robot.robot_builder import RobotBuilder
from armpy.robot.robot import Robot
from armpy.control.control_menu import RobotControlMenu


PROJECT_ROOT = Path(__file__).resolve().parents[1]

HARDWARE_INVENTORY_FILE = ( PROJECT_ROOT/ "data"/ "hardware_inventory.json")

ROBOT_CONFIG_FILE = (PROJECT_ROOT/ "src"/ "armpy"/ "config"/ "robot_joints.json")

CALIBRATION_FILE = ( PROJECT_ROOT/ "data"/ "joint_calibration.json")


def main():

    connection = DynamixelConnection()

    if not connection.open():
        print("Could not open robot connection.")
        return

    try:

        print("\n=== ARMPy Robot Control ===")

        if not connection.ping(
            connection.CM550_ID
        ):
            raise RuntimeError(
                "CM-550 did not respond."
            )

        if not connection.prepare_dynamixel_access():
            raise RuntimeError(
                "DYNAMIXEL access is not ready."
            )

        hardware_inventory = HardwareInventory(
            HARDWARE_INVENTORY_FILE
        )

        robot_config = RobotConfig(
            ROBOT_CONFIG_FILE
        )

        with CALIBRATION_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:

            calibration_data = json.load(
                file
            )

        builder = RobotBuilder(
            connection=connection,
            hardware_inventory=hardware_inventory,
            robot_config=robot_config,
            calibration_data=calibration_data
        )

        components = builder.build()

        robot = Robot(
            name=components["robot_name"],
            motors=components["motors"],
            joints=components["joints"],
            gripper=components["gripper"]
        )

        menu = RobotControlMenu(
            robot
        )

        menu.show()

    except (
        RuntimeError,
        ValueError,
        TimeoutError,
        FileNotFoundError,
        OSError
    ) as error:

        print(
            f"\nRobot control error: {error}"
        )

    except KeyboardInterrupt:

        print(
            "\nInterrupted. "
            "Motor torque states were not changed automatically."
        )

    finally:

        connection.close()

def verify_expected_motors(connection, hardware_inventory):

    discovered = connection.discover_dynamixels()

    expected_ids = set(
        hardware_inventory.get_motor_ids()
    )

    discovered_ids = set(
        discovered
    )

    missing_ids = (
        expected_ids
        - discovered_ids
    )

    if missing_ids:
        raise RuntimeError(
            f"DYNAMIXEL runtime preflight failed. "
            f"Missing motors: {sorted(missing_ids)}. "
            "Check robot power, DYNAMIXEL cables, "
            "bus baudrate, and CM-550 DXL power."
        )

    print(
        f"Runtime hardware preflight passed: "
        f"{len(discovered_ids)} motors responded."
    )

    return True

if __name__ == "__main__":
    main()