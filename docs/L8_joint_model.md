Lesson 8 — Joint Model
OOP Concept: Composition vs Inheritance

A Joint is not a Motor.

Therefore:

Joint IS-A Motor    -> incorrect
Joint HAS-A Motor   -> correct

The Joint Class contains a reference to a DynamixelMotor Object.

Joint
  |
  +-- DynamixelMotor

This relationship is Composition.

Motor Coordinates vs Joint Coordinates

A motor reports actuator coordinates.

A Joint represents robot mechanical coordinates.

These coordinates can differ because of:

Zero offset
Direction
Gear ratio
Mechanical limits

A conceptual conversion is:

joint_angle =
direction *
(motor_angle - zero_offset) /
gear_ratio
Joint State

A Joint Object contains information such as:

name
motor
zero_offset_deg
direction
gear_ratio
min_angle_deg
max_angle_deg

These values are Instance Variables because each Joint can have different mechanical configuration.

Joint Responsibilities

The Joint Class is responsible for:

Motor-to-joint coordinate conversion
Joint-to-motor coordinate conversion
Mechanical joint limits
Joint state
Joint calibration parameters

The DynamixelMotor Class remains responsible for:

Motor registers
Motor position
Voltage
Temperature
Torque
Hardware errors
Single Responsibility Principle

Each Class should have one primary responsibility.

DynamixelConnection
    -> communication

DynamixelMotor
    -> actuator

Joint
    -> mechanical joint

This keeps hardware communication, actuator behavior, and robot mechanics separated.

Current Architecture
Joint
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

No motion command is introduced in this lesson.