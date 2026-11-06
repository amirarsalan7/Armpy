import json
import shutil

from datetime import datetime
from pathlib import Path

from armpy.hardware.dynamixel_connection import (
    DynamixelConnection
)

from armpy.hardware.dynamixel_motor import (
    DynamixelMotor
)

from armpy.hardware.hardware_inventory import (
    HardwareInventory
)

from armpy.config.robot_config import (
    RobotConfig
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

HARDWARE_INVENTORY_FILE = (
    PROJECT_ROOT
    / "data"
    / "hardware_inventory.json"
)

ROBOT_CONFIG_FILE = (
    PROJECT_ROOT
    / "src"
    / "armpy"
    / "config"
    / "robot_joints.json"
)

CALIBRATION_FILE = (
    PROJECT_ROOT
    / "data"
    / "joint_calibration.json"
)


def disable_gripper_torque(
    motor
):

    torque_state = (
        motor.read_torque_enabled()
    )

    if torque_state is None:

        raise RuntimeError(
            "Could not read Gripper torque state."
        )

    if torque_state == 0:

        print(
            "Gripper torque is already OFF."
        )

        return True

    print(
        "Disabling Gripper torque..."
    )

    torque_off = getattr(
        motor,
        "TORQUE_OFF",
        0
    )

    motor.connection.sync_write(
        address=(
            motor.ADDR_TORQUE_ENABLE
        ),
        data_length=1,
        values_by_id={
            int(
                motor.motor_id
            ): torque_off
        }
    )

    torque_state = (
        motor.read_torque_enabled()
    )

    if torque_state != 0:

        raise RuntimeError(
            "Could not disable Gripper torque."
        )

    print(
        "Gripper torque is OFF."
    )

    return True


def capture_position(
    motor,
    label
):

    input(
        f"\nMove the Gripper manually to "
        f"{label}, then press Enter..."
    )

    raw_position = (
        motor.read_present_position_raw()
    )

    if raw_position is None:

        raise RuntimeError(
            "Could not read Gripper position."
        )

    raw_position = int(
        raw_position
    )

    motor.validate_goal_position_raw(
        raw_position
    )

    print(
        f"{label}: raw={raw_position}"
    )

    return raw_position


def create_backup():

    timestamp = (
        datetime.now()
        .strftime(
            "%Y%m%d_%H%M%S"
        )
    )

    backup_file = (
        CALIBRATION_FILE.parent
        / (
            "joint_calibration."
            f"backup_{timestamp}.json"
        )
    )

    shutil.copy2(
        CALIBRATION_FILE,
        backup_file
    )

    print(
        f"Calibration backup: "
        f"{backup_file}"
    )

    return backup_file


def main():

    connection = (
        DynamixelConnection()
    )

    if not connection.open():

        print(
            "Could not open robot connection."
        )

        return

    try:

        print(
            "\n=== ARMPy Gripper Calibration ==="
        )

        if not connection.ping(
            connection.CM550_ID
        ):

            raise RuntimeError(
                "CM-550 did not respond."
            )

        if not (
            connection
            .prepare_dynamixel_access()
        ):

            raise RuntimeError(
                "DYNAMIXEL access is not ready."
            )

        hardware_inventory = (
            HardwareInventory(
                HARDWARE_INVENTORY_FILE
            )
        )

        robot_config = (
            RobotConfig(
                ROBOT_CONFIG_FILE
            )
        )

        gripper_config = (
            robot_config
            .get_gripper_config()
        )

        motor_id = int(
            gripper_config[
                "motor_id"
            ]
        )

        motor_info = (
            hardware_inventory
            .get_motor(
                motor_id
            )
        )

        identity = (
            motor_info[
                "identity"
            ]
        )

        motor = DynamixelMotor(
            connection=connection,
            motor_id=motor_id,
            model_number=(
                identity[
                    "model_number"
                ]
            ),
            firmware_version=(
                identity[
                    "firmware_version"
                ]
            )
        )

        print(
            f"Gripper Motor ID: "
            f"{motor_id}"
        )

        disable_gripper_torque(
            motor
        )

        print(
            "\nIMPORTANT:"
        )

        print(
            "Do not force the Gripper "
            "against a hard mechanical stop."
        )

        open_raw = (
            capture_position(
                motor,
                "the FULLY OPEN SAFE position"
            )
        )

        closed_raw = (
            capture_position(
                motor,
                "the FULLY CLOSED SAFE position"
            )
        )

        if open_raw == closed_raw:

            raise ValueError(
                "Open and Closed positions "
                "cannot be equal."
            )

        with CALIBRATION_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:

            calibration_data = (
                json.load(
                    file
                )
            )

        gripper_data = (
            calibration_data
            .setdefault(
                "gripper",
                {}
            )
        )

        gripper_data[
            "motor_id"
        ] = motor_id

        gripper_data[
            "open_close"
        ] = {
            "calibrated": True,
            "open_raw": open_raw,
            "closed_raw": closed_raw
        }

        create_backup()

        with CALIBRATION_FILE.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                calibration_data,
                file,
                indent=4
            )

            file.write(
                "\n"
            )

        print(
            "\nGripper calibration saved."
        )

        print(
            f"Open raw:   {open_raw}"
        )

        print(
            f"Closed raw: {closed_raw}"
        )

        print(
            "\nGripper torque remains OFF."
        )

    finally:

        connection.close()


if __name__ == "__main__":
    main()