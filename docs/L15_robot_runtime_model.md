# Lesson 15 — Building the Runtime Robot Model

## Table of Contents

1. [Project Roadmap](#1-project-roadmap)
2. [Where Lesson 15 Fits](#2-where-lesson-15-fits)
3. [Lesson Goal](#3-lesson-goal)
4. [Robot Inputs and Outputs](#4-robot-inputs-and-outputs)
5. [OOP Concepts](#5-oop-concepts)
6. [Robot Responsibilities](#6-robot-responsibilities)
7. [Component Validation](#7-component-validation)
8. [Reading Joint State](#8-reading-joint-state)
9. [Reading Complete Robot State](#9-reading-complete-robot-state)
10. [RobotBuilder Integration](#10-robotbuilder-integration)
11. [Why Motion Is Not Added Yet](#11-why-motion-is-not-added-yet)
12. [Testing Strategy](#12-testing-strategy)
13. [Final Robot API](#13-final-robot-api)
14. [Lesson Result](#14-lesson-result)
15. [Next Step](#15-next-step)

---

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
RobotBuilder
        ↓
Robot Model              ← Lesson 15
        ↓
Safe Single-Joint Motion
        ↓
Dual-Motor Joint Control
        ↓
Synchronized Motion
        ↓
Trajectory / Motion Profiles
        ↓
Forward Kinematics
        ↓
Inverse Kinematics
        ↓
Cartesian Motion
        ↓
ROS
```

Lesson 13 created the calibrated `Joint` coordinate model. Lesson 14 created the runtime component assembly layer. Lesson 15 wraps those runtime components in one high-level `Robot` object.

## 2. Where Lesson 15 Fits

```text
Connection
+
HardwareInventory
+
RobotConfig
+
Calibration
        ↓
RobotBuilder
        ↓
Runtime Components
        ↓
Robot
```

The runtime components contain the robot name, all motor objects, all Joint objects, and the gripper runtime information.

## 3. Lesson Goal

Create:

```text
src/armpy/robot/robot.py
```

The `Robot` object becomes the main runtime interface for reading the complete calibrated robot.

Examples:

```python
robot.get_joint("joint2")
robot.get_motor(4)
robot.read_joint_angle("joint3")
robot.read_all_joint_angles()
robot.read_state()
```

No motor motion is commanded in this lesson.

## 4. Robot Inputs and Outputs

Constructor inputs:

```text
name
motors
joints
gripper
```

These are created by `RobotBuilder`.

The Robot exposes:

```text
Joint objects
Motor objects
Joint names
Raw Joint positions
Joint angles
Gripper raw position
Complete Robot state
```

## 5. OOP Concepts

### Facade

`Robot` acts as a facade over Motors, Joints, and the gripper. Application code can request robot-level state without manually coordinating every lower-level object.

### Composition

The Robot contains references to the runtime Motor, Joint, and gripper objects.

### Delegation

Robot does not duplicate lower-level behavior. Motor objects read hardware positions; Joint objects perform raw-to-angle conversion; Robot coordinates them.

### Object Invariant

A Robot is valid only when its object graph is consistent. A Joint motor must be the same object stored in `robot.motors`, and the gripper motor must also belong to the Robot motor collection.

## 6. Robot Responsibilities

The Robot class should store and validate runtime components, provide Joint and Motor lookup, list Joint names, read raw Joint positions, read one Joint angle, read all Joint angles, read the gripper position, and produce one complete state snapshot.

It should not yet enable torque, write Goal Position, move joints, synchronize motors, calculate trajectories, or run kinematics.

## 7. Component Validation

The Robot verifies object identity across the runtime graph:

```text
robot.motors["2"]
        │
        │ same Python object
        ↓
robot.joints["joint2"].motors["2"]
```

This prevents multiple independent Python objects from representing the same physical actuator.

The gripper motor is checked in the same way.

## 8. Reading Joint State

Raw Joint positions are collected by asking each motor in the selected Joint for `read_present_position_raw()`.

Example:

```python
{
    "2": 2060,
    "3": 2036
}
```

To obtain an angle:

```text
Robot
  ↓
Read raw positions
  ↓
Joint.calculate_joint_angle(raw_positions)
  ↓
Joint angle in degrees
```

The coordinate mathematics remains inside `Joint`.

## 9. Reading Complete Robot State

`read_state()` creates one snapshot:

```text
{
    robot_name,
    joints: {
        joint1: {
            raw_positions,
            angle_deg
        },
        ...
    },
    gripper: {
        raw_position
    }
}
```

Each Joint is read once during the snapshot.

## 10. RobotBuilder Integration

Lesson 14 keeps its current contract:

```python
components = builder.build()
```

Lesson 15 creates the Robot from those components:

```python
robot = Robot(
    name=components["robot_name"],
    motors=components["motors"],
    joints=components["joints"],
    gripper=components["gripper"]
)
```

A later refactor may make RobotBuilder return a Robot directly, but that change is not required in this lesson.

## 11. Why Motion Is Not Added Yet

The project intentionally separates Robot State from Robot Motion.

Before commanding physical movement, the runtime Robot model must correctly locate components, read hardware positions, convert raw values to degrees, and aggregate robot state.

The next lesson can build motion control on top of this verified state layer.

## 12. Testing Strategy

Tests use fake motor objects that provide `read_present_position_raw()` while real `Joint` objects use the project calibration model.

The tests should verify Robot construction, Joint lookup, Motor lookup, invalid lookup rejection, Joint names, HOME-to-zero angle behavior, angle reading, all-Joint state reading, gripper state, complete state structure, and broken object-graph rejection.

No torque or Goal Position command is used.

## 13. Final Robot API

```python
get_joint(joint_key)
get_motor(motor_id)
get_joint_names()
read_joint_raw_positions(joint_key)
read_joint_angle(joint_key)
read_all_joint_angles()
read_gripper_raw_position()
read_state()
```

## 14. Lesson Result

After Lesson 15:

```text
Hardware
    ↓
DynamixelMotor
    ↓
Joint
    ↓
RobotBuilder
    ↓
Robot
```

The complete calibrated robot can now be represented and read through one runtime object.

## 15. Next Step

The next stage is safe single-joint motion:

```text
Requested Joint Angle
        ↓
Validate Safe Limits
        ↓
Calculate Raw Goals
        ↓
Verify Operating Mode
        ↓
Handle Torque Safely
        ↓
Write Small Goal Position
        ↓
Read Feedback
        ↓
Verify Result
```

Real movement begins only after the Robot state layer passes its tests.
