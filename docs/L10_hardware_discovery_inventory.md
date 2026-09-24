# Lesson 10 - Semi-Automatic Hardware Discovery and Inventory

## Goal

The goal of this lesson is to remove manually entered hardware
information from the normal robot startup workflow.

The physical robot should be inspected automatically and the detected
hardware information should be stored for later use.

The basic workflow is:

Physical Robot

↓

DynamixelConnection

↓

HardwareDiscovery

↓

Python Dictionary

↓

JSON Serialization

↓

hardware_inventory.json

↓

HardwareInventory


---

# OOP Concepts

## Service Object

Not every object represents a physical thing.

HardwareDiscovery is a service object.

It coordinates other objects to perform a task.

HardwareDiscovery uses:

- DynamixelConnection
- DynamixelMotor

It does not replace these classes.


## Object Collaboration

HardwareDiscovery delegates low-level operations to existing objects.

Example:

HardwareDiscovery

↓

DynamixelConnection.scan_dynamixels()

and:

HardwareDiscovery

↓

DynamixelMotor.read_status()


## Dependency Injection

HardwareDiscovery does not create its own connection.

The connection object is supplied from outside:

self.connection = connection

This keeps communication and discovery responsibilities separated.


## Serialization

Python dictionaries exist only in program memory.

To preserve hardware information after program termination, the data
is serialized to JSON.

Python Dictionary

↓

json.dump()

↓

JSON File


## Persistence

The generated JSON file provides persistent hardware information that
can be reused by future programs.


---

# Hardware Data Categories

Hardware information is divided into three categories.


## Identity

Identity describes the actuator itself.

Examples:

- Motor ID
- Model Number
- Model Name
- Firmware Version


## Configuration

Configuration represents settings that normally change less often.

Examples:

- Drive Mode
- Operating Mode
- Position Limits


## Snapshot

Snapshot represents the hardware state at the time discovery was run.

Examples:

- Present Position
- Goal Position
- Torque State
- Voltage
- Temperature
- Hardware Error

Snapshot values should not be treated as permanently valid values.


---

# HardwareDiscovery

HardwareDiscovery is responsible for:

1. Checking the CM-550 controller.
2. Checking DYNAMIXEL power.
3. Scanning the DYNAMIXEL bus.
4. Preparing USB DYNAMIXEL access.
5. Discovering actuators.
6. Creating temporary DynamixelMotor objects.
7. Reading actuator identity.
8. Reading actuator configuration.
9. Reading the current hardware snapshot.
10. Building a hardware inventory.
11. Saving the inventory to JSON.


---

# HardwareInventory

HardwareInventory provides access to previously generated discovery
data.

Example:

inventory = HardwareInventory()

motor_ids = inventory.get_motor_ids()

motor1 = inventory.get_motor(1)


HardwareInventory does not communicate with the physical robot.

It only reads persisted discovery data.


---

# Configuration Separation

Two different configuration concepts currently exist.


## robot_joints.json

Contains robot-specific mechanical information.

Examples:

- Joint Mapping
- Joint names
- Direction
- Home
- Zero offset
- Mechanical limits
- Gear ratio


## hardware_inventory.json

Contains information detected from the physical hardware.

Examples:

- Controller information
- Motor IDs
- Motor model numbers
- Firmware
- DYNAMIXEL configuration
- Hardware snapshot


These files serve different purposes and should not yet be combined.


---

# Current Robot Mapping

Current known mechanical mapping:

Joint 1
    Motor 1

Joint 2
    Motor 2
    Motor 3
    opposite actuator directions

Joint 3
    Motor 4

Joint 4
    Motor 5

Joint 5
    Motor 6

Gripper actuator
    Motor 7


This mapping is currently known from manual robot inspection.

It is not discovered automatically in Lesson 10.


---

# Architecture

Physical Robot
      |
      v
DynamixelConnection
      |
      v
HardwareDiscovery
      |
      v
hardware_inventory.json
      |
      v
HardwareInventory


Mechanical Configuration
      |
      v
robot_joints.json
      |
      v
RobotConfig


Future architecture:

HardwareInventory
       +
RobotConfig
       |
       v
RobotBuilder
       |
       +-- DynamixelMotor Objects
       |
       +-- Joint Objects
       |
       +-- Gripper
       |
       v
Robot Object


---

# Important Design Rule

Low-level classes should not directly open configuration files.

DynamixelMotor should remain responsible for actuator behavior.

Joint should remain responsible for mechanical joint behavior.

Configuration loading and object construction will be handled by
higher-level classes such as RobotBuilder.


---

# Safety

This lesson does not command robot motion.

Hardware discovery reads motor state and configuration.

CM-550 scan and access preparation may modify controller-side scan or
access state, but no Goal Position command is sent to the motors.


---

# Result of Lesson 10

After this lesson the software can:

Connect to the physical robot.

Discover connected DYNAMIXEL actuators.

Read actuator identity and configuration.

Read a current hardware snapshot.

Generate a persistent hardware inventory.

Reload the generated inventory without reconnecting to the robot.


---

# Next Step

The next stage is Semi-Automatic Joint Mapping and Calibration.

The goal will be to determine or assist the user in determining:

Motor-to-Joint mapping

Multiple motors per joint

Motor direction

Joint home position

Zero offset

Mechanical limits

Gripper actuator mapping

The generated calibration data will later be combined with the
hardware inventory to construct the complete Robot object.