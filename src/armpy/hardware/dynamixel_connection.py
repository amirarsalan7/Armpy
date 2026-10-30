import time
from dynamixel_sdk import PortHandler, PacketHandler
from dynamixel_sdk import COMM_SUCCESS, GroupSyncWrite

class DynamixelConnection:

# Class Variables

    CM550_ID = 200

    ADDR_BYPASS_PORT = 20
    ADDR_MODE_NUMBER = 21
    ADDR_DXL_POWER = 22
    ADDr_CONTROLLER_ERROR = 23
    ADDR_NUM_DXL = 39
    ADDR_SCAN_DXL= 40

    DXL_POWER_OFF = 0
    DXL_POWER_ON = 1

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

    def read_dynamixel_power(self):

        return self.read_1byte(
            self.CM550_ID,
            self.ADDR_DXL_POWER
        )


    def read_controller_error_code(self):

        return self.read_2byte(
            self.CM550_ID,
            self.ADDR_CONTROLLER_ERROR
        )

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

    def read_2byte(self,device_id,address):

        value,comm_result,device_error =(
            self.packet_handler.read2ByteTxRx(
                self.port_handler,
                device_id,
                address
            )
        )
        if comm_result != COMM_SUCCESS:
            print(
                "COMMUNICATION ERROR:",
                self.packet_handler.getTxRxResult(
                    comm_result
                )
            )
            return None
        if device_error != 0:
            print(
                "DEVICE ERROR:",
                self.packet_handler.getRxPacketError(
                    device_error
                )
            )
            return None
            
        
        return value
    
    def read_4byte(self, device_id, address):

        value, comm_result, device_error = (
            self.packet_handler.read4ByteTxRx(
                self.port_handler,
                device_id,
                address
            )
        )

        if comm_result != COMM_SUCCESS:
            print(
                "COMMUNICATION ERROR:",
                self.packet_handler.getTxRxResult(
                    comm_result
                )
            )
            return None

        if device_error != 0:
            print(
                "DEVICE ERROR:",
                self.packet_handler.getRxPacketError(
                    device_error
                )
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

    
    def write_4byte(self,device_id,address,value):

        comm_result,device_error = (
            self.packet_handler.write4ByteTxRx(
                self.port_handler,
                device_id,
                address,
                value
            )
        )
        if comm_result != COMM_SUCCESS:
            print(
                "COMMUNICATION ERROR:",
                self.packet_handler.getTxRxResult(
                    comm_result
                )

            )
            return False
        if device_error != 0:
            print(
                "DEVICE ERROR:",
                self.packet_handler.getRxPacketError(
                    device_error
                )
            )
            return False
        return True

    def sync_write(
        self,
        address,
        data_length,
        values_by_id
    ):

        if data_length not in (1, 2, 4):
            raise ValueError(
                "SyncWrite supports 1, 2, or 4 byte values."
            )

        group = GroupSyncWrite(
            self.port_handler,
            self.packet_handler,
            address,
            data_length
        )

        try:

            max_value = ( 1 << ( 8 * data_length) ) - 1

            for device_id, value in values_by_id.items():

                value = int(value)

                if not (
                    0
                    <= value
                    <= max_value
                ):
                    raise ValueError(
                        f"Invalid SyncWrite value "
                        f"for Motor {device_id}: {value}"
                    )

                data = [
                    (value >> (8 * index)) & 0xFF
                    for index in range(data_length)
                ]

                if not group.addParam(
                    int(device_id),
                    data
                ):
                    raise RuntimeError(
                        f"Could not add Motor {device_id} "
                        "to SyncWrite."
                    )

            comm_result = group.txPacket()

            if comm_result != COMM_SUCCESS:
                raise RuntimeError(
                    "SyncWrite communication failed: "
                    f"{self.packet_handler.getTxRxResult(comm_result)}"
                )

            return True

        finally:

            group.clearParam()

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

        print("Scan command sent.")

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

        dxl_power = self.read_dynamixel_power()

        if dxl_power is None:
            print("Could not read DYNAMIXEL power state.")
            return False

        print(f"DYNAMIXEL power switch:{dxl_power}")

        if dxl_power != self.DXL_POWER_ON:

            error_code = self.read_controller_error_code()

            print("DYNAMIXEL power is OFF.")

            if error_code is not None:
                print(f"CM-550 error code:{error_code}")

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
    