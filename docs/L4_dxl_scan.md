Lesson 4 — DYNAMIXEL Scan and Control Table
Device ID vs Control Table Address

A Device ID identifies a device on the communication network.

Example:

CM-550 ID = 200

A Control Table Address identifies a specific data item inside that device.

Example:

Address 39 = Number of DYNAMIXELs
Address 40 = Scan DYNAMIXEL

Therefore:

ID      -> Which device?
Address -> Which data inside the device?
CM-550 Scan Algorithm
Open communication port
        ↓
Ping CM-550 ID 200
        ↓
Read DYNAMIXEL power state
        ↓
Write 1 to Address 40
        ↓
CM-550 scans the DYNAMIXEL bus
        ↓
Read Address 39
        ↓
Receive number of detected motors
        ↓
Compare result with expected motor count
        ↓
Close communication port

For ARMPy:

Expected motor count = 7
Important CM-550 Addresses
22 = DYNAMIXEL Power Switch

39 = Number of connected DYNAMIXELs

40 = Scan DYNAMIXEL

Address 39 is read-only.

Address 40 is read/write.

Writing 1 to Address 40 asks the CM-550 to scan connected DYNAMIXEL devices.

Generic Read Method
read_1byte(device_id, address)

is a reusable low-level method.

It can be used to read many different 1-byte Control Table values.

Example:

power = connection.read_1byte(200, 22)

or:

count = connection.read_1byte(200, 39)
Generic Write Method
write_1byte(device_id, address, value)

provides reusable one-byte write access.

Example:

connection.write_1byte(
    200,
    40,
    1
)

means:

Device ID = 200
Instruction = WRITE
Address = 40
Value = 1
OOP Abstraction

High-level operations should use lower-level reusable methods.

Example:

scan_dynamixels()
        ↓
write_1byte()
read_1byte()
        ↓
PacketHandler
        ↓
DYNAMIXEL Protocol

The high-level method does not need to know every detail of packet construction.

This is abstraction.

Class Variables

Hardware constants shared by every connection instance can be stored as Class Variables:

CM550_ID = 200

ADDR_DXL_POWER = 22
ADDR_NUM_DXL = 39
ADDR_SCAN_DXL = 40

These values describe the hardware interface rather than the state of one particular connection object.

Instance Variables

Connection-specific state remains in Instance Variables:

self.device_name
self.baudrate
self.protocol_version
self.port_handler
self.packet_handler
Current Software Architecture
main.py
   |
   v
DynamixelConnection
   |
   +-- PortHandler
   |
   +-- PacketHandler
   |
   +-- read_1byte()
   |
   +-- write_1byte()
   |
   +-- scan_dynamixels()

At this stage no motor motion is commanded.

The program only establishes communication and discovers the number of connected DYNAMIXEL actuators.