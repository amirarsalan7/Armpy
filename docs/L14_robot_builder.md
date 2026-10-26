# Lesson 14 — Building the Robot Assembly Layer with RobotBuilder

## Table of Contents
1. [Project Roadmap](#1-project-roadmap)
2. [Lesson 14 Goal](#2-lesson-14-goal)
3. [Why RobotBuilder Exists](#3-why-robotbuilder-exists)
4. [Inputs and Outputs](#4-inputs-and-outputs)
5. [OOP Concepts](#5-oop-concepts)
6. [Construction Flow](#6-construction-flow)
7. [RobotBuilder Responsibilities](#7-robotbuilder-responsibilities)
8. [Motor Construction](#8-motor-construction)
9. [Joint Construction](#9-joint-construction)
10. [Gripper Assembly](#10-gripper-assembly)
11. [Validation](#11-validation)
12. [Testing Strategy](#12-testing-strategy)
13. [Files Added](#13-files-added)
14. [Next Step](#14-next-step)

## 1. Project Roadmap

```text
Hardware Communication
        ↓
Motor Abstraction
        ↓
Hardware Discovery
        ↓
Hardware Inventory
        ↓
Robot Configuration
        ↓
Calibration
        ↓
Joint Coordinate Model
        ↓
RobotBuilder              ← Lesson 14
        ↓
Robot Model
        ↓
Safe Single-Joint Motion
        ↓
Dual-Motor Joint Control
        ↓
Synchronized Motion
        ↓
Trajectory
        ↓
Forward Kinematics
        ↓
Inverse Kinematics
        ↓
Cartesian Motion
        ↓
ROS
```

Lesson 13 created the calibrated `Joint` coordinate model. Lesson 14 connects the existing project layers and automatically assembles the runtime motor and joint objects.

## 2. Lesson 14 Goal

Create:

```text
src/armpy/robot/robot_builder.py
```

`RobotBuilder` receives existing dependencies and project data, validates their compatibility, creates runtime objects, and returns an assembled component graph for the next layer.

It does not move the robot.

## 3. Why RobotBuilder Exists

Without a builder, application code would manually create every motor, look up every joint mapping, load calibration values, and construct every `Joint`.

`RobotBuilder` centralizes this construction process.

Conceptually:

```python
builder = RobotBuilder(
    connection,
    hardware_inventory,
    robot_config,
    calibration_data
)

components = builder.build()
```

## 4. Inputs and Outputs

### Inputs

```text
DynamixelConnection
HardwareInventory
RobotConfig
Calibration Data
```

The connection is the live communication dependency used by each `DynamixelMotor`.

`HardwareInventory` describes the discovered hardware: motor IDs, model numbers, and firmware versions.

`RobotConfig` describes the intended robot structure: joint names, motor mapping, gear ratios, and gripper mapping.

Calibration data contains measured HOME positions, motor directions, safe limits, and gripper calibration.

### Output

For Lesson 14, `build()` returns runtime components:

```text
robot_name
motors
joints
gripper
```

Conceptually:

```text
components
├── robot_name
├── motors
│   ├── "1" → DynamixelMotor
│   ├── "2" → DynamixelMotor
│   └── ...
├── joints
│   ├── joint1 → Joint
│   ├── joint2 → Joint
│   ├── joint3 → Joint
│   ├── joint4 → Joint
│   └── joint5 → Joint
└── gripper
    ├── motor
    ├── config
    └── calibration
```

This is an intermediate assembly result. The next lesson will build the final `Robot` object around these components.

## 5. OOP Concepts

### Builder Pattern

Builder is a creational design pattern. It separates how a complex object graph is constructed from how that object graph is used.

```text
RobotBuilder
    ↓
constructs Motors and Joints

Robot
    ↓
uses Motors and Joints
```

### Dependency Injection

The builder receives its dependencies instead of creating global objects internally:

```text
connection
hardware_inventory
robot_config
calibration_data
```

### Composition

The runtime graph is composed from smaller objects:

```text
DynamixelConnection
        ↓
DynamixelMotor
        ↓
Joint
        ↓
Robot
```

### Fail-Fast Validation

The builder rejects incompatible configuration, hardware, or calibration before constructing a usable runtime graph.

## 6. Construction Flow

```text
Connection
    +
HardwareInventory
    +
RobotConfig
    +
Calibration Data
        ↓
Validate Sources
        ↓
Build DynamixelMotor Objects
        ↓
Map Motors to Joints
        ↓
Build Joint Objects
        ↓
Attach Gripper Motor + Calibration
        ↓
Return Runtime Components
```

## 7. RobotBuilder Responsibilities

`RobotBuilder` should validate source compatibility, create one motor object per discovered motor, reuse those motor objects while constructing joints, construct one calibrated `Joint` per configured joint, prepare gripper runtime information, and return all components.

It should not open the serial port, perform discovery, run calibration, enable torque, move motors, calculate trajectories, or perform kinematics.

## 8. Motor Construction

For every motor in `HardwareInventory`, the builder reads:

```text
motor_id
model_number
firmware_version
```

and constructs:

```python
DynamixelMotor(
    connection=connection,
    motor_id=motor_id,
    model_number=model_number,
    firmware_version=firmware_version
)
```

Motor objects are indexed using string IDs so they match the calibration JSON keys.

## 9. Joint Construction

For each configured joint, the builder combines:

```text
RobotConfig
+
Calibration Data
+
Runtime Motor Objects
```

For example:

```text
joint2
├── Config
│   ├── name = shoulder
│   ├── motor_ids = [2, 3]
│   └── gear_ratio = 1.0
├── Calibration
│   ├── HOME
│   ├── directions
│   └── limits
└── Runtime Motors
    ├── Motor 2
    └── Motor 3
```

The result is one calibrated logical `Joint`.

## 10. Gripper Assembly

The gripper is kept separate from the revolute arm joints. The builder prepares its motor object, configuration, and calibration data. A dedicated Gripper class can be added later if required.

## 11. Validation

Before construction, RobotBuilder verifies:

```text
Calibration robot name matches RobotConfig
Calibration joint keys match configured joint keys
Configured motors exist in HardwareInventory
Calibration motor mappings match RobotConfig
HOME is calibrated
Direction is calibrated
Limits are calibrated
Gripper motor exists
Gripper calibration is present
```

The `Joint` constructor then performs another validation layer for the individual Joint object.

## 12. Testing Strategy

RobotBuilder can be tested without moving the real robot. Constructing `DynamixelMotor` objects does not itself send a motion command.

The test should verify:

```text
7 motor objects are created
5 Joint objects are created
Joint 1 uses Motor 1
Joint 2 uses Motors 2 and 3
All runtime object types are correct
Gripper uses Motor 7
Robot name is correct
Calibration is attached correctly
Invalid source mappings are rejected
```

No torque or Goal Position command is used.

## 13. Files Added

```text
src/armpy/robot/robot_builder.py
tests/test_robot_builder.py
docs/L14_robot_builder.md
```

## 14. Next Step

After RobotBuilder is tested, Lesson 15 can replace the old Robot prototype with a calibrated runtime Robot model.

```text
RobotBuilder
    ↓
Runtime Components
    ↓
Robot
    ↓
Robot-Level State and Control API
```

Only after the Robot layer is stable should the project begin real safe motion commands.
