# Lesson 16 — Safe Robot Motion, Velocity Control, and Synchronized Joint Control

## Table of Contents

1. [Project Roadmap](#1-project-roadmap)
2. [Lesson 16 Goal](#2-lesson-16-goal)
3. [Control Architecture](#3-control-architecture)
4. [OOP and Design Concepts](#4-oop-and-design-concepts)
   - [Facade](#41-facade)
   - [Command–Query Separation](#42-commandquery-separation)
   - [Delegation](#43-delegation)
   - [Fail-Fast Validation](#44-fail-fast-validation)
5. [Runtime Preflight](#5-runtime-preflight)
6. [Safe Joint Motion API](#6-safe-joint-motion-api)
7. [Motion Preview](#7-motion-preview)
8. [Joint Limits and Calibration Safety](#8-joint-limits-and-calibration-safety)
9. [Position Control and Profile Velocity](#9-position-control-and-profile-velocity)
10. [Joint Velocity to Motor Profile Velocity](#10-joint-velocity-to-motor-profile-velocity)
11. [Dynamic Motion Timeout](#11-dynamic-motion-timeout)
12. [Safe Torque Preparation](#12-safe-torque-preparation)
13. [Single-Motor Joint Motion](#13-single-motor-joint-motion)
14. [Dual-Motor Shoulder Control](#14-dual-motor-shoulder-control)
15. [Synchronized Goal Position with SyncWrite](#15-synchronized-goal-position-with-syncwrite)
16. [Coupled-Motor Alignment Check](#16-coupled-motor-alignment-check)
17. [Motion Monitoring](#17-motion-monitoring)
18. [Hold Joint Position](#18-hold-joint-position)
19. [Control Menu](#19-control-menu)
20. [Final Robot Motion API](#20-final-robot-motion-api)
21. [Files Used in Lesson 16](#21-files-used-in-lesson-16)
22. [Testing](#22-testing)
23. [Safety Rules](#23-safety-rules)
24. [Current Capabilities](#24-current-capabilities)
25. [Current Limitations](#25-current-limitations)
26. [Lesson 16 Result](#26-lesson-16-result)
27. [Next Stages](#27-next-stages)

---

# 1. Project Roadmap

ARMPy has now reached the first real robot-control layer.

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
Robot Runtime Model
        ↓
Safe Motion Control            ← Lesson 16
        ↓
Velocity-Controlled Motion     ← Lesson 16
        ↓
Synchronized Joint2 Control    ← Lesson 16
        ↓
Control Menu                   ← Lesson 16
        ↓
Multi-Joint Motion
        ↓
Named Poses / HOME
        ↓
Jog / Keyboard / Joystick
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

Before this lesson, ARMPy could build a complete runtime robot and read its state.

After this lesson, ARMPy can also command safe joint motion.

# 2. Lesson 16 Goal

The main goal of Lesson 16 is to provide a high-level motion API such as:

```python
robot.move_joint(
    "joint3",
    -40.0,
    velocity_deg_s=5.0
)
```

The caller works with:

```text
Joint name
Target angle in degrees
Joint velocity in degrees per second
```

The caller does not need to manage:

```text
Motor IDs
Raw encoder goals
HOME offsets
Motor directions
Profile Velocity registers
Torque preparation
SyncWrite packets
Motion timeout calculations
```

These responsibilities are handled by the lower software layers.

# 3. Control Architecture

```text
CLI
GUI
Keyboard
Joystick
ROS
  │
  ▼
Robot API
  │
  ▼
Joint Model
  │
  ▼
DynamixelMotor
  │
  ▼
DynamixelConnection
  │
  ▼
CM-550
  │
  ▼
DYNAMIXEL Bus
  │
  ▼
Physical Robot
```

The user interface never writes motor registers directly.

The same Robot API can therefore be reused by future interfaces.

# 4. OOP and Design Concepts

## 4.1 Facade

`Robot` is the main high-level control interface.

Instead of:

```python
motor.write(...)
```

application code uses:

```python
robot.move_joint(...)
```

The Robot object hides lower-level hardware details.

## 4.2 Command–Query Separation

Read-only operations are queries:

```python
robot.read_joint_angle("joint3")
robot.read_state()
robot.preview_joint_move("joint3", -20.0, 5.0)
```

Operations that change the physical robot are commands:

```python
robot.move_joint("joint3", -20.0, 5.0)
robot.hold_joint("joint3")
```

A preview operation must never move hardware.

## 4.3 Delegation

```text
Robot
    ↓ coordinates motion

Joint
    ↓ converts joint angle ↔ raw motor position

DynamixelMotor
    ↓ controls one physical actuator

DynamixelConnection
    ↓ performs packet communication
```

## 4.4 Fail-Fast Validation

Unsafe conditions are rejected before Goal Position is sent.

Examples:

```text
Invalid Joint
Target outside calibrated limits
Motor communication failure
Wrong Operating Mode
Wrong Drive Mode
Hardware error
Invalid motor goal
Mixed torque states
Coupled motors out of alignment
```

# 5. Runtime Preflight

The startup sequence is:

```text
Open serial port
        ↓
Ping CM-550
        ↓
Verify Manage Mode
        ↓
Verify USB Bypass Port
        ↓
Verify DYNAMIXEL Power Switch
        ↓
Build Runtime Robot
        ↓
Open Control Menu
```

Motion commands are available only after the hardware path is ready.

# 6. Safe Joint Motion API

The public API is:

```python
robot.move_joint(
    joint_key,
    target_angle_deg,
    velocity_deg_s
)
```

The same method is used for single-motor and dual-motor joints.

# 7. Motion Preview

```python
plan = robot.preview_joint_move(
    "joint1",
    25.0,
    velocity_deg_s=5.0
)
```

The preview contains:

```text
Joint
Current angle
Target angle
Movement distance
Velocity
Current raw position
Goal raw position
Profile Velocity raw value
Torque state
```

# 8. Joint Limits and Calibration Safety

All target angles are checked against calibrated software limits before motion.

The calibrated HOME position defines:

```text
Joint angle = 0°
```

The Joint model remains the source of truth for HOME, direction, gear ratio, limits, and raw/degree conversion.

# 9. Position Control and Profile Velocity

Lesson 16 keeps the motors in Position Control Mode.

The target is still a position, while Profile Velocity controls how fast the motor approaches that position.

The relevant DYNAMIXEL register is:

```text
Profile Velocity
Address: 112
```

ARMPy writes a non-zero Profile Velocity for controlled motion.

# 10. Joint Velocity to Motor Profile Velocity

ARMPy exposes speed in degrees per second.

```text
motor_rpm =
joint_velocity_deg_s × gear_ratio / 6
```

Then:

```text
profile_velocity_raw =
motor_rpm / 0.229
```

This converts a user-facing joint velocity into the DYNAMIXEL Profile Velocity value.

# 11. Dynamic Motion Timeout

Timeout is calculated from movement distance and requested speed.

```text
expected_time =
abs(movement_deg) / velocity_deg_s

timeout =
expected_time × scale
+ safety_margin
```

This avoids false timeouts during long or intentionally slow moves.

# 12. Safe Torque Preparation

If torque is OFF:

```text
Read Present Position
        ↓
Stage current position as Goal
        ↓
Enable Torque
        ↓
Verify Torque
        ↓
Send target Goal Position
```

For multi-motor joints, all motors must have consistent torque states.

# 13. Single-Motor Joint Motion

Single-motor joints use a normal Goal Position write after validation and Profile Velocity setup.

```text
Target Joint Angle
        ↓
Raw Goal
        ↓
Profile Velocity
        ↓
Torque Preparation
        ↓
Goal Position
        ↓
Feedback Monitoring
```

# 14. Dual-Motor Shoulder Control

`joint2` contains two mechanically coupled motors:

```text
joint2
├── Motor 2
└── Motor 3
```

One joint target is converted into two raw goals according to each motor's HOME and calibrated direction.

# 15. Synchronized Goal Position with SyncWrite

Joint2 Goal Positions are sent with DYNAMIXEL `GroupSyncWrite`.

```text
Motor 2 Goal ─┐
              ├── SyncWrite packet
Motor 3 Goal ─┘
```

The same synchronization mechanism can be used for multi-motor torque enable.

# 16. Coupled-Motor Alignment Check

Each motor position is independently converted into a logical joint angle.

If the two calculated angles disagree by more than the configured tolerance, the motion is rejected or stopped.

This protects the mechanically coupled shoulder from continuing when the two actuators disagree significantly.

# 17. Motion Monitoring

After the Goal Position is sent, ARMPy repeatedly reads Present Position.

Motion succeeds only when every motor in the Joint is inside the configured target tolerance.

If the dynamic timeout expires, the current position is held instead of leaving the old target active.

# 18. Hold Joint Position

```python
robot.hold_joint("joint1")
```

and:

```python
robot.hold_joint("joint2")
```

set the current physical position as the active Goal Position.

Single-motor joints use a normal write.

Multi-motor joints use SyncWrite.

# 19. Control Menu

```text
========================
ARMPy Control
========================

1. Read Robot State
2. Move One Joint
3. Show Joint Limits
4. Hold Joint Position
5. Set Default Velocity
0. Exit
```

The menu is only a frontend over the Robot API.

A motion command follows this flow:

```text
Select Joint
        ↓
Read current angle
        ↓
Show safe limits
        ↓
Enter target angle
        ↓
Enter velocity
        ↓
Preview motion
        ↓
Confirm
        ↓
Robot.move_joint()
```

# 20. Final Robot Motion API

```python
robot.read_joint_angle(...)
robot.read_state()

robot.preview_joint_move(
    joint_key,
    target_angle_deg,
    velocity_deg_s
)

robot.move_joint(
    joint_key,
    target_angle_deg,
    velocity_deg_s
)

robot.hold_joint(
    joint_key
)
```

Example:

```python
robot.move_joint(
    "joint1",
    -20.0,
    velocity_deg_s=5.0
)
```

Synchronized shoulder example:

```python
robot.move_joint(
    "joint2",
    10.0,
    velocity_deg_s=3.0
)
```

# 21. Files Used in Lesson 16

```text
src/armpy/hardware/dynamixel_connection.py
src/armpy/hardware/dynamixel_motor.py
src/armpy/robot/joint.py
src/armpy/robot/robot.py
src/armpy/control/control_menu.py
scripts/control_robot.py
tests/test_robot_motion.py
docs/L16_safe_robot_motion_velocity_sync_control.md
```

Main responsibilities:

```text
DynamixelConnection
→ SyncWrite communication

DynamixelMotor
→ Profile Velocity support

Joint
→ Joint coordinate mathematics

Robot
→ Safe motion orchestration

RobotControlMenu
→ Interactive CLI

control_robot.py
→ Application composition and startup
```

# 22. Testing

Relevant test groups are:

```text
tests/test_joint.py
tests/test_robot_builder.py
tests/test_robot.py
tests/test_robot_motion.py
```

The Joint, RobotBuilder, and Robot tests were executed successfully after the Lesson 16 changes.

The dedicated `test_robot_motion.py` test still needs to be updated to match the new motion API. Its fake motor must support the new Profile Velocity methods and synchronized-motion behavior.

Therefore the Lesson 16 implementation is integrated, but the dedicated motion unit-test coverage is not yet complete.

# 23. Safety Rules

Important rules:

- verify CM-550 communication before motion
- verify DYNAMIXEL power before motion
- verify calibration before motion
- never bypass calibrated joint limits
- use low velocity for initial tests
- use very small movements for the first Joint2 synchronized tests
- keep the workspace clear
- keep access to robot power available
- do not automatically disable torque on a loaded arm
- do not silently change Operating Mode during a motion command
- reject mixed torque states in coupled joints
- monitor coupled-motor disagreement
- use dynamic timeout instead of a fixed timeout
- hold the current position after a motion timeout

# 24. Current Capabilities

ARMPy can now:

```text
Read complete robot state
Read calibrated joint angles
Show calibrated joint limits
Preview movement
Command target joint angles
Control movement velocity
Control single-motor joints
Control the dual-motor shoulder
Send synchronized Goal Positions
Synchronize multi-motor torque enable
Monitor motion completion
Detect coupled-motor disagreement
Use dynamic motion timeout
Hold joint position
Control the robot through an interactive CLI
```

# 25. Current Limitations

Not yet implemented:

```text
Profile Acceleration control
Multi-joint coordinated motion
Whole-robot synchronized motion
Named poses
Automatic HOME motion
Jog control
Velocity Control Mode
Keyboard teleoperation
Joystick teleoperation
Trajectory generation
Forward kinematics
Inverse kinematics
Cartesian motion
ROS control
```

# 26. Lesson 16 Result

Before Lesson 16:

```text
Robot
    ↓
Read state
```

After Lesson 16:

```text
Robot
    ↓
Read State
    +
Preview Motion
    +
Control Position
    +
Control Velocity Profile
    +
Synchronize Dual-Motor Joint
    +
Monitor Motion
```

The main motion abstraction is:

```python
robot.move_joint(
    joint_key,
    target_angle_deg,
    velocity_deg_s
)
```

# 27. Next Stages

```text
Finish Motion Unit Tests
        ↓
Profile Acceleration
        ↓
Multi-Joint Motion
        ↓
Whole-Robot SyncWrite
        ↓
Named Poses / HOME
        ↓
Jog Control
        ↓
Keyboard / Joystick
        ↓
Trajectory Generation
        ↓
Forward Kinematics
        ↓
Inverse Kinematics
        ↓
Cartesian Motion
        ↓
ROS
```

Lesson 16 establishes the reusable motion-control foundation for the rest of ARMPy.
