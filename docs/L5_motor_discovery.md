Lesson 5 — DYNAMIXEL Motor Discovery
Goal

The purpose of this lesson is to move from knowing only the number of connected DYNAMIXEL devices to discovering each device individually.

The desired information is:

DYNAMIXEL ID
Model Number
Firmware Version

No motor motion is commanded during this stage.

Discovery Architecture
Python
  |
  v
DynamixelConnection
  |
  v
USB
  |
  v
CM-550
  |
  v
DYNAMIXEL Bus
  |
  +-- Motor
  +-- Motor
  +-- Motor
  +-- ...
CM-550 Scan vs Broadcast Ping

The CM-550 Scan feature tells us how many DYNAMIXEL devices are connected.

Address 40 -> Start Scan
Address 39 -> Number of DYNAMIXELs

This provides a count only.

A Protocol 2.0 Broadcast Ping asks all connected DYNAMIXEL devices to respond.

The responses provide:

ID
Model Number
Firmware Version

Therefore:

CM-550 Scan
    ->
Motor count

Broadcast Ping
    ->
Individual motor identity
Manage Mode

CM-550 Address 21 stores the current operating mode.

0 = IDLE
1 = Task Play
2 = Manage
3 = Bootloader
4 = Reboot

Manage Mode is used when accessing and configuring the controller and connected DYNAMIXEL devices.

Bypass Port

CM-550 Address 20 reports which communication port is bypassed to the DYNAMIXEL port.

0 = BLE
1 = UART
2 = USB

Address 20 is read-only.

When using the PC through USB for direct DYNAMIXEL discovery, the expected bypass value is:

2 = USB
Broadcast Ping

DYNAMIXEL Protocol 2.0 defines Broadcast ID:

254
0xFE

A Broadcast Ping asks all devices on the bus to respond.

In Python DYNAMIXEL SDK:

dxl_data, comm_result = (
    packet_handler.broadcastPing(
        port_handler
    )
)

The returned data contains information for responding devices.

Python Dictionary

Discovery results can be stored as a dictionary:

{
    motor_id: {
        "model_number": value,
        "firmware_version": value
    }
}

A dictionary stores information as:

key -> value

For motor discovery, the DYNAMIXEL ID is a natural dictionary key.

OOP — Encapsulation

Encapsulation means keeping implementation details inside an Object and exposing a simpler interface to the rest of the application.

Instead of writing DYNAMIXEL packet logic directly in main.py, the application can call:

connection.discover_dynamixels()

Internally, the DynamixelConnection Object handles:

Packet creation
Communication
Protocol handling
Result parsing
Error checking

The caller only uses the high-level interface.

Current DynamixelConnection Responsibilities
DynamixelConnection
|
|-- open()
|-- close()
|-- ping()
|-- read_1byte()
|-- write_1byte()
|-- scan_dynamixels()
|-- prepare_dynamixel_access()
|-- discover_dynamixels()

The class is responsible for communication and discovery.

It is not responsible for robot kinematics or joint behavior.

try, except, and finally

try contains an operation that may fail.

except handles selected exceptions.

finally contains cleanup code that should run whether the operation succeeds or fails.

Example:

try:
    perform_hardware_operations()

finally:
    connection.close()

For hardware software, finally is useful for reliably releasing resources such as communication ports.

Current Project Layer

The software development sequence is:

Connection
    ↓
Discovery
    ↓
Motor Model
    ↓
Joint Model
    ↓
Robot Model
    ↓
Control

This lesson completes most of the Discovery layer.

The next software layer will represent each physical DYNAMIXEL as a Python Object.
