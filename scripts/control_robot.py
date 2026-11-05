import json
import time

from pathlib import Path

from armpy.hardware.dynamixel_connection import DynamixelConnection
from armpy.hardware.hardware_inventory import HardwareInventory
from armpy.config.robot_config import RobotConfig
from armpy.robot.robot_builder import RobotBuilder
from armpy.robot.robot import Robot
from armpy.control.control_menu import RobotControlMenu

from armpy.control.pose_library import PoseLibrary
from armpy.control.pose_controller import PoseController
from armpy.control.jog_controller import JogController
from armpy.control.keyboard_jog import KeyboardJogController
from armpy.control.joystick_jog import JoystickJogController


PROJECT_ROOT = Path(__file__).resolve().parents[1]

HARDWARE_INVENTORY_FILE = ( PROJECT_ROOT/ "data"/ "hardware_inventory.json")

ROBOT_CONFIG_FILE = (PROJECT_ROOT/ "src"/ "armpy"/ "config"/ "robot_joints.json")

CALIBRATION_FILE = ( PROJECT_ROOT/ "data"/ "joint_calibration.json")

POSES_FILE = ( PROJECT_ROOT/ "src"/ "armpy"/ "config"/ "robot_poses.json")


JOYSTICK_AXIS_MAP = {}


def verify_expected_motors(
    connection,
    hardware_inventory,
    attempts=3,
    retry_delay_s=0.5
):

    expected_ids = set(
        hardware_inventory.get_motor_ids()
    )

    last_discovered_ids = set()

    for attempt in range(
        1,
        attempts + 1
    ):

        discovered = (
            connection.discover_dynamixels()
        )

        discovered_ids = set(
            discovered
        )

        last_discovered_ids = (
            discovered_ids
        )

        missing_ids = (
            expected_ids
            - discovered_ids
        )

        if not missing_ids:

            print(
                "Runtime hardware preflight passed: "
                f"{len(discovered_ids)} motors responded."
            )

            return True

        if attempt < attempts:

            print(
                f"Hardware preflight attempt "
                f"{attempt}/{attempts} failed. "
                "Retrying..."
            )

            time.sleep(
                retry_delay_s
            )

    missing_ids = (
        expected_ids
        - last_discovered_ids
    )

    raise RuntimeError(
        "DYNAMIXEL runtime preflight failed. "
        f"Missing motors: {sorted(missing_ids)}."
    )
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

        verify_expected_motors(
            connection,
            hardware_inventory
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

        pose_library = PoseLibrary(
            POSES_FILE,
            robot
        )

        pose_controller = PoseController(
            robot,
            pose_library
        )

        jog_controller = JogController(
            robot,
            step_deg=1.0
        )

        keyboard_controller = KeyboardJogController(
            jog_controller,
            pose_controller
        )



        joystick_controller = JoystickJogController(
            jog_controller,
            pose_controller,
            JOYSTICK_AXIS_MAP
        )

        menu = RobotControlMenu(
            robot=robot,
            pose_controller=pose_controller,
            jog_controller=jog_controller,
            keyboard_controller=keyboard_controller,
            joystick_controller=joystick_controller
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


if __name__ == "__main__":
    main()