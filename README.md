# ARMPy

> **A modular Python robotics project for building, calibrating, modeling, and controlling a real DYNAMIXEL-based robotic arm.**

ARMPy is a hands-on robotics project built around a real robot, real actuators, and real software architecture.

The project starts at the lowest level — serial communication with DYNAMIXEL hardware — and grows step by step toward joint-level control, coordinated robot motion, trajectories, kinematics, and eventually higher-level robotics frameworks.

Rather than treating the robot as a collection of motor IDs, ARMPy is being designed as a reusable software system with clear layers for hardware access, configuration, calibration, joint modeling, robot construction, and motion control.

---

## Table of Contents

- [Why ARMPy?](#why-armpy)
- [Hardware Platform](#hardware-platform)
- [Project Goals](#project-goals)
- [Current Architecture](#current-architecture)
- [Project Structure](#project-structure)
- [Development Roadmap](#development-roadmap)
  - [Completed](#completed)
  - [Current Stage](#current-stage)
  - [Next Stages](#next-stages)
- [What Has Been Built So Far](#what-has-been-built-so-far)
  - [1. DYNAMIXEL Connection](#1-dynamixel-connection)
  - [2. Motor Abstraction](#2-motor-abstraction)
  - [3. Hardware Discovery](#3-hardware-discovery)
  - [4. Hardware Inventory](#4-hardware-inventory)
  - [5. Robot Configuration](#5-robot-configuration)
  - [6. Unified Calibration System](#6-unified-calibration-system)
  - [7. Calibrated Joint Coordinate Model](#7-calibrated-joint-coordinate-model)
- [Calibration Data Flow](#calibration-data-flow)
- [Joint Coordinate Model](#joint-coordinate-model)
- [Getting Started](#getting-started)
  - [Clone the Repository](#clone-the-repository)
  - [Create a Virtual Environment](#create-a-virtual-environment)
  - [Install Dependencies](#install-dependencies)
  - [Install ARMPy in Editable Mode](#install-armpy-in-editable-mode)
  - [Run Tests](#run-tests)
- [Running Calibration](#running-calibration)
- [Testing](#testing)
- [Documentation](#documentation)
- [Safety](#safety)
- [Design Principles](#design-principles)
- [Future Direction](#future-direction)
- [License](#license)

---

## Why ARMPy?

Robotics software becomes difficult when hardware communication, motor commands, calibration values, joint math, and robot logic are mixed together.

ARMPy separates these responsibilities into clear layers.

Instead of writing code like:

```python
motor.write_goal_position(2348)
```

the long-term goal is to work at robot level:

```python
robot.move_joint("joint3", 30.0)
```

and eventually:

```python
robot.move_joints({
    "joint1": 20.0,
    "joint2": -15.0,
    "joint3": 35.0
})
```

The software underneath should automatically understand:

- which motor or motors belong to the joint,
- the calibrated HOME position,
- encoder direction,
- gear ratio,
- safe joint limits,
- raw motor goals,
- synchronized movement requirements.

That is the central idea behind the project.

---

## Hardware Platform

The current ARMPy hardware setup includes:

- **ROBOTIS CM-550** controller
- **DYNAMIXEL XL430-W250** actuators
- **7 DYNAMIXEL motors**
- USB connection between the development computer and CM-550
- External 12 V robot power supply
- Multi-joint robotic arm with a dedicated gripper actuator

Current motor mapping:

```text
Joint 1  → Motor 1
Joint 2  → Motors 2 + 3
Joint 3  → Motor 4
Joint 4  → Motor 5
Joint 5  → Motor 6
Gripper  → Motor 7
```

Joint 2 is mechanically coupled and uses two motors whose encoder directions are opposite.

---

## Project Goals

ARMPy is being developed to build a clean and extensible robot-control stack covering:

- Python-based hardware communication
- Object-oriented robot architecture
- DYNAMIXEL motor abstraction
- hardware discovery
- hardware inventory
- configuration-driven robot mapping
- persistent calibration
- joint coordinate modeling
- safe motion control
- synchronized multi-motor control
- robot state management
- trajectory generation
- forward kinematics
- inverse kinematics
- Cartesian motion
- future ROS integration

The project is intentionally developed in layers so every new control feature is built on top of verified lower-level behavior.

---

## Current Architecture

The current software stack is moving toward this structure:

```text
User / Application
        |
        v
      Robot
        |
        v
   RobotBuilder
        |
        v
      Joint
        |
        v
DynamixelMotor
        |
        v
DynamixelConnection
        |
        v
      CM-550
        |
        v
Physical DYNAMIXEL Bus
```

Supporting data flows into the runtime model:

```text
robot_joints.json
        |
        +------> RobotConfig
        |
hardware_inventory.json
        |
        +------> HardwareInventory
        |
joint_calibration.json
        |
        +------> Calibration Data
                    |
                    v
               RobotBuilder
                    |
                    v
              Runtime Robot
```

The project is designed so low-level hardware code does not need to know about robot kinematics, while higher-level robot code does not need to manually manage raw motor registers.

---

## Project Structure

Current project organization:

```text
ARMPy/
├── data/
│   ├── hardware_inventory.json
│   └── joint_calibration.json
│
├── docs/
│   └── ...
│
├── scripts/
│   ├── calibrate_robot.py
│   └── ...
│
├── src/
│   └── armpy/
│       ├── __init__.py
│       │
│       ├── calibration/
│       │   ├── __init__.py
│       │   ├── calibration_menu.py
│       │   └── joint_calibration.py
│       │
│       ├── config/
│       │   ├── robot_config.py
│       │   └── robot_joints.json
│       │
│       ├── hardware/
│       │   ├── __init__.py
│       │   ├── dynamixel_connection.py
│       │   ├── dynamixel_motor.py
│       │   ├── hardware_discovery.py
│       │   └── hardware_inventory.py
│       │
│       └── robot/
│           ├── __init__.py
│           ├── joint.py
│           └── robot.py
│
├── tests/
│   ├── test_config.py
│   └── test_joint.py
│
├── pyproject.toml
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

The main organization rule is:

```text
src/armpy/   → reusable Python package
scripts/     → executable workflows
data/        → generated hardware/calibration data
tests/       → automated tests
docs/        → development documentation
```

---

# Development Roadmap

The roadmap is the core development path of ARMPy:

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
Robot Model
        ↓
Safe Single-Joint Motion
        ↓
Dual-Motor Joint Control
        ↓
Synchronized Multi-Joint Motion
        ↓
Motion Profiles / Trajectories
        ↓
Forward Kinematics
        ↓
Inverse Kinematics
        ↓
Cartesian Motion
        ↓
ROS Integration
```

## Completed

- [x] DYNAMIXEL connection layer
- [x] DYNAMIXEL motor abstraction
- [x] hardware discovery
- [x] hardware inventory
- [x] robot configuration
- [x] unified calibration workflow
- [x] HOME calibration
- [x] motor direction calibration
- [x] joint safe-limit calibration
- [x] gripper calibration
- [x] calibration persistence in JSON
- [x] calibration status and verification
- [x] calibrated Joint coordinate model
- [x] raw ↔ angle conversion
- [x] calibrated joint limit checks
- [x] single-motor and dual-motor Joint tests
- [x] editable Python package setup with `pyproject.toml`

## Current Stage

The current development stage is:

> **Build the runtime robot model on top of the calibrated Joint layer.**

The next major component is expected to be a **RobotBuilder** that combines:

```text
HardwareInventory
        +
RobotConfig
        +
Calibration Data
        ↓
DynamixelMotor Objects
        ↓
Joint Objects
        ↓
Robot Object
```

## Next Stages

Planned development sequence:

1. **RobotBuilder**
   - create motor objects automatically
   - create calibrated Joint objects
   - assemble the runtime robot

2. **Robot class**
   - expose joints by name
   - read complete robot state
   - provide robot-level control interfaces

3. **Safe single-joint motion**
   - validate requested angles
   - calculate motor goals
   - verify operating mode
   - manage torque safely
   - execute small controlled movements

4. **Dual-motor shoulder control**
   - command Motors 2 and 3 as one logical joint
   - verify coupled motion
   - monitor disagreement between motors

5. **Synchronized multi-joint motion**
   - coordinated motor writes
   - synchronized state reads

6. **Motion profiles and trajectories**
   - velocity and acceleration profiles
   - smooth point-to-point motion
   - trajectory execution

7. **Forward kinematics**
   - joint angles → end-effector pose

8. **Inverse kinematics**
   - desired pose → joint angles

9. **Cartesian motion**
   - command end-effector movement in workspace coordinates

10. **ROS integration**
    - expose the robot to a larger robotics software ecosystem

---

# What Has Been Built So Far

## 1. DYNAMIXEL Connection

The connection layer manages communication between Python and the CM-550 / DYNAMIXEL bus.

Its responsibilities include:

- serial port access
- baudrate configuration
- protocol configuration
- CM-550 access preparation
- opening and closing communication safely

This layer isolates transport details from the rest of the project.

---

## 2. Motor Abstraction

`DynamixelMotor` represents one physical actuator as a Python object.

Instead of scattering register-level communication throughout the project, motor operations are centralized behind a reusable interface.

Conceptually:

```text
DynamixelMotor
      ↓
Motor ID
Model Information
Torque State
Present Position
Goal Position
Other Motor State
```

This becomes the hardware building block used by higher-level Joint objects.

---

## 3. Hardware Discovery

Hardware discovery scans the robot bus and determines which motors physically exist.

The discovery layer answers questions such as:

```text
Which motor IDs responded?
Which DYNAMIXEL model is connected?
Which firmware version is running?
```

This separates real hardware detection from manually written robot configuration.

---

## 4. Hardware Inventory

The discovered hardware is persisted into:

```text
data/hardware_inventory.json
```

This creates a stable record of the detected robot hardware.

The inventory can later be compared against the intended robot configuration.

---

## 5. Robot Configuration

Robot configuration describes the intended structure of the robot.

It defines information such as:

- joint names
- motor mapping
- gear ratios
- physical positive-motion conventions
- gripper mapping

This data is different from calibration data.

```text
Configuration
=
What the robot is intended to be

Calibration
=
What was measured on the physical robot
```

---

## 6. Unified Calibration System

Calibration was refactored into one unified system.

The main components are:

```text
scripts/calibrate_robot.py
        |
        v
CalibrationMenu
        |
        v
JointCalibration
```

The calibration workflow includes:

- HOME calibration
- direction calibration
- joint safe-limit calibration
- gripper reference calibration
- gripper open/close calibration
- calibration status
- stored-data verification
- automatic persistence

Measured calibration data is stored in:

```text
data/joint_calibration.json
```

The calibration process is manual by design.

The software checks torque state but does not automatically release torque before manual positioning.

---

## 7. Calibrated Joint Coordinate Model

The current `Joint` class converts calibration data into a coordinate model that works in degrees.

The Joint layer provides:

```text
Raw Motor Position
        ↕
Joint Angle
```

Its current responsibilities include:

- validating joint configuration
- handling one or multiple motors
- applying calibrated encoder direction
- applying gear ratio
- defining HOME as `0°`
- converting raw positions to joint angles
- converting joint angles to raw motor goals
- calculating shared safe limits
- rejecting out-of-limit angles
- generating raw goals for all motors in a joint

The class has already been tested with both:

```text
joint1 → single motor
joint2 → dual motor
```

---

## Calibration Data Flow

Calibration follows this flow:

```text
Physical Robot
      |
      v
DynamixelMotor
      |
      v
Raw Measurements
      |
      v
JointCalibration
      |
      v
Validation
      |
      v
User Accepts Measurement
      |
      v
Auto Save
      |
      v
joint_calibration.json
```

The stored calibration includes:

```text
HOME
Direction
Negative Safe Limit
Middle / HOME Reference
Positive Safe Limit
Gripper Reference
Gripper Open Position
Gripper Close Position
```

The system stores only accepted calibration measurements.

---

## Joint Coordinate Model

The current Joint coordinate model defines:

```text
Calibrated HOME = 0°
```

Motor encoder direction determines how raw position changes map to positive or negative joint angles.

The basic conversion is conceptually:

```text
raw position
    ↓
subtract HOME
    ↓
apply encoder direction
    ↓
apply counts-per-degree
    ↓
joint angle
```

And in reverse:

```text
requested joint angle
    ↓
check safe limits
    ↓
apply counts-per-degree
    ↓
apply motor direction
    ↓
add calibrated HOME
    ↓
raw motor goal
```

For the dual-motor shoulder:

```text
One Joint Angle
      |
      +------> Motor 2 Goal
      |
      +------> Motor 3 Goal
```

Both motors represent the same physical joint even though their raw encoder directions are opposite.

---

# Getting Started

## Clone the Repository

```bash
git clone https://github.com/amirarsalan7/Armpy.git
cd Armpy
```

---

## Create a Virtual Environment

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

After activation, the shell should show:

```text
(.venv)
```

---

## Install Dependencies

```bash
python -m pip install -r requirements.txt
```

---

## Install ARMPy in Editable Mode

ARMPy uses a `src` package layout.

Install the project in editable mode:

```bash
pip install -e .
```

This enables imports such as:

```python
from armpy.robot.joint import Joint
```

without manually setting `PYTHONPATH`.

Editable mode also means changes inside:

```text
src/armpy/
```

are immediately available to the installed development package.

---

## Run Tests

Run the Joint tests:

```bash
python tests/test_joint.py
```

The current Joint test suite verifies:

```text
12 tests executed
12 tests passed
0 failures
0 errors
```

It covers:

- object construction
- HOME → `0°`
- raw → angle conversion
- angle → raw conversion
- round-trip conversion
- calibrated limits
- unsafe-angle rejection
- dual-motor direction handling
- goal generation
- invalid gear-ratio rejection
- invalid motor-mapping rejection

---

# Running Calibration

With the robot connected and powered correctly, the calibration workflow is started from the calibration script.

The calibration system guides the user through:

```text
HOME
  ↓
Direction
  ↓
Joint Limits
  ↓
Gripper
  ↓
Status
  ↓
Verification
```

Calibration movement is manual.

The calibration system does not use automatic Goal Position commands during measurement.

---

# Testing

Tests live under:

```text
tests/
```

The goal is to keep mathematical and software behavior testable without requiring the physical robot for every check.

For example, `test_joint.py` uses real configuration and calibration data while replacing physical motor objects with lightweight placeholders.

This makes it possible to test coordinate conversion independently from hardware motion.

Future tests can be separated into:

```text
Unit Tests
Integration Tests
Hardware Tests
Motion Safety Tests
```

---

# Documentation

Detailed development notes are stored in:

```text
docs/
```

The documentation follows the project evolution lesson by lesson, including topics such as:

- CM-550 communication
- DYNAMIXEL scanning
- motor objects
- hardware discovery
- joint mapping
- calibration architecture
- calibrated joint coordinates

The README provides the project-level overview, while the files under `docs/` explain individual development stages in more detail.

---

# Safety

ARMPy controls real electromechanical hardware.

Safety is part of the software architecture, not an optional extra.

Important rules:

- verify communication before enabling torque
- verify motor IDs before movement
- verify robot configuration against detected hardware
- calibrate HOME before joint control
- calibrate motor direction before generating joint commands
- use safe software limits with margin before mechanical hard stops
- support the arm mechanically when torque is OFF
- do not automatically release torque on a loaded arm
- test coordinate mathematics before sending motion commands
- begin real motion with small, controlled movements
- treat stored-data verification separately from live mechanical verification

A successful software verification does **not** automatically mean the robot is mechanically safe to move.

---

# Design Principles

ARMPy follows several design principles:

### Separation of Responsibilities

```text
Connection      → communication
Motor           → one actuator
Discovery       → detect hardware
Inventory       → store detected hardware
Config          → define intended robot
Calibration     → measure physical robot
Joint           → convert motor space ↔ joint space
RobotBuilder    → assemble runtime objects
Robot           → high-level robot interface
Motion Layer    → controlled movement
```

### Configuration-Driven Design

Robot structure should come from configuration instead of being duplicated across the codebase.

### Calibration-Driven Control

Runtime control should use measured calibration data rather than hard-coded raw positions.

### Safe Defaults

Unsafe or incomplete states should fail early.

### Reusable Components

Core code lives under:

```text
src/armpy/
```

and executable workflows live under:

```text
scripts/
```

### Test Before Motion

Mathematics and software behavior should be verified before commands are sent to physical motors.

---

# Future Direction

The long-term ARMPy vision is to move from:

```text
Raw DYNAMIXEL Register Access
```

to:

```text
High-Level Robot Motion
```

through a controlled sequence of abstractions.

The future software stack is expected to look approximately like:

```text
Application
    ↓
Robot
    ↓
Motion Controller
    ↓
Trajectory
    ↓
Joint
    ↓
DynamixelMotor
    ↓
DynamixelConnection
    ↓
Physical Robot
```

With kinematics added:

```text
Desired Cartesian Pose
        ↓
Inverse Kinematics
        ↓
Joint Targets
        ↓
Trajectory
        ↓
Robot Motion
```

This keeps ARMPy useful not only as a hardware-control project, but as a foundation for increasingly advanced robotics work.

---

# License

This project is licensed under the terms included in the repository's `LICENSE` file.

---

## Project Status

**Current milestone:** calibrated Joint coordinate model completed and tested.

**Next milestone:** build the runtime robot assembly layer with `RobotBuilder`, then move toward safe real joint motion.

If you are exploring Python robotics, DYNAMIXEL control, robot software architecture, or the path from raw actuators to a structured robot API, ARMPy is designed to make that path visible — one layer at a time.
