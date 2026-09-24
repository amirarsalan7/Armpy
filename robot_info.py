from dynamixel_connection import DynamixelConnection
from dynamixel_motor import DynamixelMotor


EXPECTED_MOTOR_COUNT = 7


# =====================================================
# Terminal UI
# =====================================================

def print_title(title):
    print()
    print("=" * 72)
    print(f"  {title}")
    print("=" * 72)


def print_section(title):
    print()
    print(f"--- {title} ---")


def format_value(value, digits=None):

    if value is None:
        return "N/A"

    if digits is not None and isinstance(value, float):
        return f"{value:.{digits}f}"

    return str(value)


def print_table(headers, rows):

    string_rows = [
        [str(value) for value in row]
        for row in rows
    ]

    widths = [
        len(str(header))
        for header in headers
    ]

    for row in string_rows:
        for index, value in enumerate(row):
            widths[index] = max(
                widths[index],
                len(value)
            )

    separator = "+-" + "-+-".join(
        "-" * width
        for width in widths
    ) + "-+"

    header_row = "| " + " | ".join(
        str(header).ljust(widths[index])
        for index, header in enumerate(headers)
    ) + " |"

    print(separator)
    print(header_row)
    print(separator)

    for row in string_rows:

        print(
            "| "
            + " | ".join(
                value.ljust(widths[index])
                for index, value in enumerate(row)
            )
            + " |"
        )

    print(separator)


# =====================================================
# Display Helpers
# =====================================================

def torque_text(value):

    if value == 1:
        return "ON"

    if value == 0:
        return "OFF"

    return "N/A"


def operating_mode_text(value):

    modes = {
        1: "Velocity",
        3: "Position",
        4: "Extended Position",
        16: "PWM",
    }

    if value is None:
        return "N/A"

    return modes.get(
        value,
        f"Unknown ({value})"
    )


def hardware_error_text(value):

    if value is None:
        return "N/A"

    if value == 0:
        return "OK"

    return f"ERROR ({value})"


# =====================================================
# Motor Creation
# =====================================================

def create_motor_objects(
    connection,
    discovered_motors
):

    motor_objects = {}

    for motor_id, info in discovered_motors.items():

        motor = DynamixelMotor(
            connection=connection,
            motor_id=motor_id,
            model_number=info["model_number"],
            firmware_version=info["firmware_version"]
        )

        motor_objects[motor_id] = motor

    return motor_objects


# =====================================================
# Discovery Table
# =====================================================

def show_discovery_table(discovered_motors):

    rows = []

    for motor_id, info in discovered_motors.items():

        rows.append([
            motor_id,
            info["model_number"],
            info["firmware_version"],
        ])

    print_table(
        [
            "ID",
            "Model Number",
            "Firmware"
        ],
        rows
    )


# =====================================================
# Motor Status Table
# =====================================================

def show_motor_status_table(motor_objects):

    rows = []

    for motor_id, motor in motor_objects.items():

        status = motor.read_status()

        rows.append([
            motor_id,
            status["model_name"],
            status["firmware_version"],
            torque_text(
                status["torque_enabled"]
            ),
            format_value(
                status["position_raw"]
            ),
            format_value(
                status["position_deg"],
                2
            ),
            format_value(
                status["voltage"],
                1
            ),
            format_value(
                status["temperature"]
            ),
            hardware_error_text(
                status["hardware_error"]
            ),
        ])

    print_table(
        [
            "ID",
            "Model",
            "FW",
            "Torque",
            "Position",
            "Deg",
            "Voltage",
            "Temp C",
            "HW Error",
        ],
        rows
    )


# =====================================================
# Motor Configuration Table
# =====================================================

def show_motor_configuration_table(
    motor_objects
):

    rows = []

    for motor_id, motor in motor_objects.items():

        config = motor.read_configuration()

        limits = config["position_limits"]

        if limits is None:
            min_position = "N/A"
            max_position = "N/A"
        else:
            min_position = limits["min"]
            max_position = limits["max"]

        rows.append([
            motor_id,
            config["drive_mode"],
            operating_mode_text(
                config["operating_mode"]
            ),
            torque_text(
                config["torque_enabled"]
            ),
            min_position,
            max_position,
            format_value(
                config["goal_position"]
            ),
            format_value(
                config["present_position"]
            ),
        ])

    print_table(
        [
            "ID",
            "Drive",
            "Operating Mode",
            "Torque",
            "Min",
            "Max",
            "Goal",
            "Present",
        ],
        rows
    )


# =====================================================
# Main Startup Check
# =====================================================

def main():

    print_title(
        "ARMPy Robot Startup Check"
    )

    connection = DynamixelConnection()

    system_checks = []

    # -------------------------------------------------
    # Open Port
    # -------------------------------------------------

    print_section(
        "1. Communication"
    )

    if not connection.open():

        print(
            "FATAL: Could not open communication port."
        )

        return

    system_checks.append([
        "Serial port",
        "PASS",
        connection.device_name
    ])

    try:

        # -------------------------------------------------
        # CM-550
        # -------------------------------------------------

        print_section(
            "2. CM-550 Controller"
        )

        if not connection.ping(
            connection.CM550_ID
        ):

            system_checks.append([
                "CM-550",
                "FAIL",
                "No response"
            ])

            print_table(
                ["Check", "Result", "Details"],
                system_checks
            )

            return

        system_checks.append([
            "CM-550",
            "PASS",
            f"ID {connection.CM550_ID}"
        ])

        # -------------------------------------------------
        # DYNAMIXEL Power
        # -------------------------------------------------

        dxl_power = connection.read_1byte(
            connection.CM550_ID,
            connection.ADDR_DXL_POWER
        )

        if dxl_power != 1:

            system_checks.append([
                "DXL power",
                "FAIL",
                str(dxl_power)
            ])

            print_table(
                ["Check", "Result", "Details"],
                system_checks
            )

            return

        system_checks.append([
            "DXL power",
            "PASS",
            "ON"
        ])

        # -------------------------------------------------
        # CM-550 Scan
        # -------------------------------------------------

        print_section(
            "3. DYNAMIXEL Bus Scan"
        )

        scan_count = (
            connection.scan_dynamixels()
        )

        if scan_count is None:

            system_checks.append([
                "CM-550 scan",
                "FAIL",
                "No result"
            ])

            print_table(
                ["Check", "Result", "Details"],
                system_checks
            )

            return

        scan_result = (
            "PASS"
            if scan_count == EXPECTED_MOTOR_COUNT
            else "WARN"
        )

        system_checks.append([
            "CM-550 scan",
            scan_result,
            (
                f"{scan_count}/"
                f"{EXPECTED_MOTOR_COUNT} motors"
            )
        ])

        # -------------------------------------------------
        # USB Bypass / Manage Access
        # -------------------------------------------------

        print_section(
            "4. DYNAMIXEL Access"
        )

        if not connection.prepare_dynamixel_access():

            system_checks.append([
                "USB DXL access",
                "FAIL",
                "Not ready"
            ])

            print_table(
                ["Check", "Result", "Details"],
                system_checks
            )

            return

        system_checks.append([
            "USB DXL access",
            "PASS",
            "Manage / USB ready"
        ])

        # -------------------------------------------------
        # Broadcast Discovery
        # -------------------------------------------------

        print_section(
            "5. Motor Discovery"
        )

        discovered_motors = (
            connection.discover_dynamixels()
        )

        discovered_count = len(
            discovered_motors
        )

        discovery_result = (
            "PASS"
            if discovered_count
            == EXPECTED_MOTOR_COUNT
            else "WARN"
        )

        system_checks.append([
            "Broadcast discovery",
            discovery_result,
            (
                f"{discovered_count}/"
                f"{EXPECTED_MOTOR_COUNT} motors"
            )
        ])

        show_discovery_table(
            discovered_motors
        )

        # -------------------------------------------------
        # Create Motor Objects
        # -------------------------------------------------

        print_section(
            "6. Motor Objects"
        )

        motor_objects = create_motor_objects(
            connection,
            discovered_motors
        )

        print(
            f"Created {len(motor_objects)} "
            "DynamixelMotor objects."
        )

        # -------------------------------------------------
        # Status
        # -------------------------------------------------

        print_section(
            "7. Motor Status"
        )

        show_motor_status_table(
            motor_objects
        )

        # -------------------------------------------------
        # Configuration
        # -------------------------------------------------

        print_section(
            "8. Motor Configuration"
        )

        show_motor_configuration_table(
            motor_objects
        )

        # -------------------------------------------------
        # Final Summary
        # -------------------------------------------------

        print_section(
            "9. Startup Summary"
        )

        print_table(
            [
                "Check",
                "Result",
                "Details"
            ],
            system_checks
        )

        if (
            scan_count == EXPECTED_MOTOR_COUNT
            and discovered_count
            == EXPECTED_MOTOR_COUNT
        ):

            print()
            print(
                "SYSTEM STATUS: "
                "READ-ONLY STARTUP CHECK PASSED"
            )

            print(
                "Motion commands are not executed "
                "by this program."
            )

        else:

            print()
            print(
                "SYSTEM STATUS: "
                "STARTUP CHECK COMPLETED WITH WARNINGS"
            )

    except (ValueError, RuntimeError) as error:

        print()
        print(
            f"CONFIGURATION ERROR: {error}"
        )

    finally:

        print_section(
            "Shutdown"
        )

        connection.close()


# =====================================================
# Program Entry Point
# =====================================================

if __name__ == "__main__":
    main()