import json

from pathlib import Path

class HardwareInventory:

    def __init__(
            self,
            file_path = "config/hardware_inventory.json"
    ):

        self.file_path= Path(file_path)
        self.data= self._load()

    def _load(self):
        if not self.file_path.exists():
            raise FileNotFoundError(
                f"Hardwareinventory not found :"
                f"{self.file_path}"
            )

        with self.file_path.open(
            "r",
            encoding = "utf-8"
        )as file:
            return json.load(file)


    def get_controller(self):

        return self.data["controller"]

    def get_bus(self):

        return self.data["bus"]

    def get_all_motors(self):

        return self.data["motors"]

    def get_motor(
            self,
            motor_id
    ):

        key = str(motor_id)

        motors = self.data["motors"]

        if key not in motors:

            raise ValueError(
                f"Motor ID {motor_id}"
                "does not exist in hardware inventory."
            )
        return motors[key]

    def get_motor_ids(self):

        return sorted(
            int(motor_id)
            for motor_id
            in self.data["motors"].keys()
        )

    