import time
from dynamixel_sdk import PortHandler, PacketHandler, COMM_SUCCESS


class DynamixelConnection:

# Class Variables

    CM550_ID = 200

    ADDR_BYPASS_PORT = 20
    ADDR_MODE_NUMBER = 21
    ADDR_DXL_POWER = 22
    ADDR_NUM_DXL = 39
    ADDR_SCAN_DXL= 40

    MODE_MANAGE = 2
    BYPASS_USB = 2

    # Methods
    def __init__(
        self,
        # Instance Variables
        device_name="/dev/ttyACM0",
        baudrate=57600,
        protocol_version=2.0
    ):
        self.device_name = device_name
        self.baudrate = baudrate
        self.protocol_version = protocol_version

        self.port_handler = PortHandler(self.device_name)
        self.packet_handler = PacketHandler(self.protocol_version)

    
    def open(self):

        if not self.port_handler.openPort():
            print(f"ERROR: Could not open {self.device_name}")
            return False

        if not self.port_handler.setBaudRate(self.baudrate):
            print(f"ERROR: Could not set baudrate to {self.baudrate}")
            self.port_handler.closePort()
            return False

        print(f"Port opened: {self.device_name}")
        print(f"Baudrate: {self.baudrate}")
        print(f"Protocol: {self.protocol_version}")

        return True


    def ping(self,device_id):

        model_number,comm_result,device_error =(
            self.packet_handler.ping(
                self.port_handler,
                device_id
            )
        )

        if comm_result != COMM_SUCCESS:
            print(
                "COMMUNICATION ERROR:",
                self.packet_handler.getTxRxResult(comm_result)
            )
            return False

        if device_error != 0:
            print("DEVICE ERROR",
                  self.packet_handler.getRxPacketError(device_error)
            )
            return False

        print(
            f"Device ID {device_id} responded. "
        )

        print(
            f"Model number: {model_number}"
        )

        return True

    def read_1byte(self,device_id,address):

        value,comm_result,device_error = (
            self.packet_handler.read1ByteTxRx(
                self.port_handler,
                device_id,
                address
            )
        )

        if comm_result != COMM_SUCCESS:
            print(
                "COMMUNICATION ERROR:",
                self.packet_handler.getTxRxResult(comm_result)
            )
            return None

        if device_error != 0:
            print(
                "DEVICE ERROR :",
                self.packet_handler.getRxPacketError(device_error)
            )
            return None

        return value


    def write_1byte(self, device_id, address, value):

        comm_result, device_error = (
            self.packet_handler.write1ByteTxRx(
                self.port_handler,
                device_id,
                address,
                value
            )
        )

        if comm_result != COMM_SUCCESS:
            print(
                "COMMUNICATION ERROR:",
                self.packet_handler.getTxRxResult(comm_result)
            )
            return False

        if device_error != 0:
            print(
                "DEVICE ERROR:",
                self.packet_handler.getRxPacketError(device_error)
            )
            return False

        return True

    def scan_dynamixels(self):

        print("Starting DYNAMIXEL scan . . .")

        success = self.write_1byte(
            self.CM550_ID,
            self.ADDR_SCAN_DXL,
            1
        )

        if not success:
            print("Could not start DYNAMIXEL scan.")
            return None

        print("Scane command sent.")

        time.sleep(3)

        motor_count = self.read_1byte(
            self.CM550_ID,
            self.ADDR_NUM_DXL
        )
        if motor_count is None:
            print("Could not read DYNAMIXEL count.")
            return None

        print(f"Detected DYNAMIXEL motors :{motor_count}")

        return motor_count

    def prepare_dynamixel_access(self):

        mode = self.read_1byte(
            self.CM550_ID,
            self.ADDR_MODE_NUMBER
        )

        if mode is None:
            print("Could not read CM-550 mode.")
            return False
        print(f"CM-550 mode:{mode}")

        if mode != self.MODE_MANAGE:
            print("Switching CM-550 to manage mode . . .")

            success = self.write_1byte(
                self.CM550_ID,
                self.ADDR_MODE_NUMBER,
                self.MODE_MANAGE
            )

            if not success:
                print("Could not enter MANAGE mode . . .")
                return False

            time.sleep(0.5)

        bypass_port = self.read_1byte(
            self.CM550_ID,
            self.ADDR_BYPASS_PORT
        )

        if bypass_port is None:
            print("Could not read bypass port.")
            return False

        print(f"Bypass port :{bypass_port}")

        if bypass_port != self.BYPASS_USB:
            print(
                "USB is not currently the DYNAMIXEL bypass port."
            )
            return False

        print("USB DYNAMIXEL access is ready.")

        return True

    def discover_dynamixels(self):

        print("Broadcast ping started . . .")

        dxl_data,comm_result = (
            self.packet_handler.broadcastPing(
                self.port_handler
            )
        )
        if comm_result != COMM_SUCCESS:
            print(
                "COMMUNICATION ERROR:",
                self.packet_handler.getTxRxResult(
                    comm_result
                )
            )
            return {}

        
        discovered = {}

        for device_id,data in sorted(dxl_data.items()):

            if device_id == self.CM550_ID:
                continue

            model_number = data[0]
            firmware_version = data[1]

            discovered[device_id] = {
                "model_number": model_number,
                "firmware_version":firmware_version,
            }
        return discovered

    def close(self):

        self.port_handler.closePort()

        print("Port closed.")
    