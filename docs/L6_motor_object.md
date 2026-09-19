Lesson 6 — DYNAMIXEL Motor Object
Current Hardware

Motor discovery found seven DYNAMIXEL devices.

All seven reported:

Model Number: 1060
Firmware Version: 47

Model Number 1060 identifies the actuator as:

XL430-W250

The exact motor model allows the software to use the correct Control Table addresses.

Software Layers

The project is being developed in layers:

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

The current lesson begins the Motor Model layer.

File Responsibilities
dynamixel_connection.py

handles communication.

Its responsibilities include:

Opening and closing the port
Sending and receiving packets
Reading and writing bytes
Discovering devices
dynamixel_motor.py

represents one physical DYNAMIXEL actuator.

Its responsibilities include interpreting motor-specific Control Table data such as:

Torque state
Position
Voltage
Temperature
Hardware error

joint.py and robot.py remain in the project but are not yet used by the Motor layer.

One Connection, Many Motors

The robot uses one shared communication connection:

             connection
                 |
      +----------+----------+
      |          |          |
   motor 1    motor 2    motor 3
      |
     ...
      |
   motor 7

All Motor Objects reference the same DynamixelConnection Object.

Dependency Injection

A Motor Object receives its required Connection Object through its constructor:

motor = DynamixelMotor(
    connection=connection,
    motor_id=1,
    model_number=1060,
    firmware_version=47
)

The Motor does not create its own connection.

This design is called Dependency Injection.

Composition

A DynamixelMotor contains a reference to a DynamixelConnection:

DynamixelMotor
    |
    +-- connection

The Motor uses this Object to communicate with the physical actuator.

Instance Variables

Each Motor Object contains its own:

self.connection
self.motor_id
self.model_number
self.firmware_version

For example:

motor1:
    ID = 1

motor2:
    ID = 2

These are Instance Variables because their values belong to individual Objects.

Class Variables

Control Table information shared by all XL430-W250 Motor Objects is stored as Class Variables:

ADDR_TORQUE_ENABLE = 64
ADDR_HARDWARE_ERROR = 70
ADDR_PRESENT_POSITION = 132
ADDR_PRESENT_INPUT_VOLTAGE = 144
ADDR_PRESENT_TEMPERATURE = 146

These values describe the XL430-W250 model rather than one individual motor.

Motor Object Creation

Discovery initially produces data:

ID
Model Number
Firmware Version

The program then converts this data into Objects:

Discovery Data
      |
      v
DynamixelMotor(...)
      |
      v
Motor Object

For seven motors:

motor_objects
|
|-- 1 -> DynamixelMotor
|-- 2 -> DynamixelMotor
|-- 3 -> DynamixelMotor
|-- 4 -> DynamixelMotor
|-- 5 -> DynamixelMotor
|-- 6 -> DynamixelMotor
|-- 7 -> DynamixelMotor
Encapsulation

Instead of asking the application to know:

Temperature Address = 146
Voltage Address = 144
Position Address = 132

the application asks the Motor Object:

motor.read_temperature()
motor.read_input_voltage()
motor.read_present_position_raw()

The implementation details remain inside the Motor Class.

Object Collaboration

Objects cooperate rather than each Object performing every operation itself.

Example:

motor.read_temperature()
        |
        v
DynamixelMotor
        |
        v
DynamixelConnection
        |
        v
DYNAMIXEL SDK
        |
        v
CM-550
        |
        v
Physical Motor

Each Object has a specific responsibility.

try, except, finally

try contains normal hardware operations.

except handles selected exceptions.

finally performs cleanup regardless of success or failure.

Example:

try:
    create_motor_objects()

except ValueError as error:
    print(error)

finally:
    connection.close()

This is useful because hardware resources such as communication ports should be released even when an error occurs.

Current Motor Data

At this stage the Motor Object can read:

Torque state
Present Position
Input Voltage
Temperature
Hardware Error Status

No movement command is sent in this lesson.

The robot remains in a read-only monitoring stage.