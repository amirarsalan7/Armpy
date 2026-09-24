from dynamixel_connection import DynamixelConnection
from hardware_discovery import HardwareDiscovery

EXPECTED_MOTOR_COUNT = 7

OUTPUT_FILE = (
    "config/hardware_inventory.json"
)

connection = DynamixelConnection()

if connection.open():

    try:

        print(
            "\n--- Hardware Discovery ---"
        )

        discovery = HardwareDiscovery(
            connection=connection,
            expected_motor_count=(
                EXPECTED_MOTOR_COUNT
            )
        )

        inventory = discovery.discover()

        output_path = discovery.save(
            OUTPUT_FILE
        )

        print(
            "\nHardware discovery completed."
        )

        print(
            f"Controller: "
            f"{inventory['controller']['type']}"
        )

        print(
            f"Motors discovered: "
            f"{inventory['bus']['broadcast_discovery_count']}"
        )

        print(
            "Motor IDs:",
            list(
                inventory["motors"].keys()
            )
        )

        print(
            f"Inventory saved to: "
            f"{output_path}"
        )

    except (
        RuntimeError,
        ValueError,
        OSError
    ) as error:

        print(
            f"\nDiscovery error: {error}"
        )

    finally:

        connection.close()