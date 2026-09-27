# Lesson 11 - Semi-Automatic Joint Home Calibration

## Goal

The goal of this lesson is to begin converting manual robot
configuration into measured robot calibration data.

The software validates the known motor-to-joint mapping and records
the current encoder position of every actuator as the selected HOME
reference.

No motion command is sent to the robot.


# Robot Structure

The current robot contains five revolute arm joints and one gripper
actuator.

Joint 1:
Motor 1

Joint 2:
Motor 2 + Motor 3

Joint 3:
Motor 4

Joint 4:
Motor 5

Joint 5:
Motor 6

Gripper:
Motor 7


Joint 2 is a dual-motor joint.


# What Is Joint Calibration?

Hardware discovery identifies the connected actuators.

Joint calibration identifies how those actuators relate to the
assembled mechanical robot.

Calibration data can include:

- Home position
- Zero reference
- Motor direction
- Gear ratio
- Safe mechanical limits
- Gripper open position
- Gripper closed position


Lesson 11 begins with Home / Zero reference capture.


# OOP Concept: Stateful Service Object

JointCalibration is a service object.

It does not represent a physical joint.

Instead, it performs a calibration process using other objects.

JointCalibration collaborates with:

- DynamixelConnection
- HardwareInventory
- RobotConfig
- DynamixelMotor


The object also contains state.

Before capture:

calibration = None

After capture:

calibration = measured calibration data


# Separation of Responsibilities

Joint is a robot domain object.

JointCalibration is a setup and measurement service.

Joint should eventually represent:

- Joint angle
- Motor references
- Mechanical limits
- Coordinate conversion

JointCalibration is responsible for:

- Validating configuration
- Reading calibration measurements
- Organizing calibration data
- Saving calibration data


# Dependency Injection

JointCalibration receives its dependencies from outside.

Example:

JointCalibration(
    connection,
    hardware_inventory,
    robot_config
)

It does not create a new connection internally.

This allows existing application objects to collaborate without
duplicating hardware resources.


# Mapping Validation

Before calibration, the configured mapping is compared with the
hardware inventory.

Example:

robot_joints.json:

Joint 3 -> Motor 4

hardware_inventory.json:

Motor 4 exists

Result:

Mapping valid


If a configured motor does not exist in the hardware inventory,
calibration stops with an error.


# Building Motor Objects From Inventory

Lesson 10 generated persistent hardware identity information.

JointCalibration reuses this information.

hardware_inventory.json

↓

HardwareInventory

↓

stored Motor ID / Model / Firmware

↓

DynamixelMotor objects


This avoids repeating full hardware discovery simply to reconstruct
motor objects.


# Home Position

Home is a reference pose selected for the robot.

For each actuator the current raw encoder position is recorded.

Example:

Joint 1:

Motor 1 home = 2046


Dual-motor Joint 2:

Motor 2 home = 2039

Motor 3 home = 2055


Each motor receives its own measured reference.

A dual-motor joint therefore does not use one shared raw zero value.


# Why Raw Counts Are Stored

The calibration system stores measured encoder counts instead of
inventing a mechanical angle.

Measured value:

home_raw = 2039

Later the Joint model will convert the measured motor displacement
into joint angle using:

- motor direction
- zero reference
- gear ratio
- motor resolution


# Calibration Persistence

Measured calibration is serialized to:

config/joint_calibration.json


The basic data flow is:

Physical Robot

↓

DynamixelMotor

↓

JointCalibration

↓

Python Dictionary

↓

JSON Serialization

↓

joint_calibration.json


# Current Calibration State

After Lesson 11:

Motor-to-joint mapping:
Known

Hardware inventory:
Available

Home position:
Measured

Motor direction:
Not yet calibrated

Mechanical limits:
Not yet calibrated

Gripper open / close:
Not yet calibrated


# Safety

Lesson 11 does not:

- Enable torque
- Disable torque
- Write Goal Position
- Move any actuator

It only reads Present Position.

Manual repositioning must never be attempted against an enabled
motor.

Heavy robot links must be mechanically supported before manually
repositioning joints with torque disabled.


# Current Architecture

Physical Robot
      |
      v
DynamixelConnection
      |
      v
DynamixelMotor


hardware_inventory.json
      |
      v
HardwareInventory


robot_joints.json
      |
      v
RobotConfig


HardwareInventory
       +
RobotConfig
       +
Live Connection
       |
       v
JointCalibration
       |
       v
joint_calibration.json


# Result of Lesson 11

The software can now:

- Validate motor-to-joint mapping against discovered hardware.
- Recreate motor objects using persistent hardware inventory.
- Read live encoder positions.
- Capture the selected robot HOME pose.
- Store a separate HOME reference for each actuator.
- Correctly support the dual-motor shoulder joint.
- Persist calibration measurements for future robot software.


# Next Lesson

Semi-Automatic Direction Calibration.

The system will capture motor positions before and after a small
manual joint displacement.

It will calculate encoder deltas and determine the direction of each
motor relative to joint motion.

This is especially important for Joint 2, where Motor 2 and Motor 3
move in opposite directions.