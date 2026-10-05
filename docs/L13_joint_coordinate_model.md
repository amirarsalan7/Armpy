# Lesson 13 — Building the Calibrated Joint Coordinate Model

## Table of Contents

1. [Project Roadmap](#1-project-roadmap)
2. [Where Lesson 13 Fits](#2-where-lesson-13-fits)
3. [Lesson 13 Goal](#3-lesson-13-goal)
4. [Joint Architecture](#4-joint-architecture)
5. [OOP Concepts Used](#5-oop-concepts-used)
   - [Object Invariant](#51-object-invariant)
   - [Composition](#52-composition)
   - [Abstraction](#53-abstraction)
6. [Calibration Data Used by Joint](#6-calibration-data-used-by-joint)
7. [Joint Coordinate System](#7-joint-coordinate-system)
8. [Counts per Joint Degree](#8-counts-per-joint-degree)
9. [Raw Position to Joint Angle](#9-raw-position-to-joint-angle)
10. [Joint Angle to Raw Position](#10-joint-angle-to-raw-position)
11. [Dual-Motor Joint](#11-dual-motor-joint)
12. [Safe Joint Limits](#12-safe-joint-limits)
13. [Final Joint API](#13-final-joint-api)
14. [Why Motion Commands Are Not Added Yet](#14-why-motion-commands-are-not-added-yet)
15. [Testing Strategy](#15-testing-strategy)
16. [Numeric Test Summary](#16-numeric-test-summary)
17. [Package and Test Execution](#17-package-and-test-execution)
18. [Lesson 13 Result](#18-lesson-13-result)

---

# 1. Project Roadmap

After finishing hardware discovery, robot configuration, and calibration, the next development path is:

```text
Calibration
    ↓
Joint Model
    ↓
RobotBuilder
    ↓
Robot
    ↓
Safe Motion
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

The main idea is to move from low-level hardware information toward a higher-level robot control system.

The project already knows:

```text
Which motors exist
Which motors belong to each joint
HOME / zero positions
Motor directions
Safe limits
Gripper calibration
```

The next step is to convert this information into a usable robot coordinate model.

---

# 2. Where Lesson 13 Fits

Before Lesson 13, the project architecture was approximately:

```text
Physical Robot
      ↓
DynamixelConnection
      ↓
DynamixelMotor
      ↓
HardwareDiscovery
      ↓
HardwareInventory
      ↓
RobotConfig
      ↓
JointCalibration
      ↓
joint_calibration.json
```

This gives the project accurate hardware and calibration data, but it does not yet provide a clean interface such as:

```python
joint_angle = 20.0
```

or:

```python
goal_positions = joint.calculate_goal_positions(20.0)
```

Lesson 13 adds the missing coordinate-conversion layer.

The new logical path becomes:

```text
Calibration Data
      ↓
Joint Coordinate Model
      ↓
Motor Raw Goals
```

This is the first important layer between calibration and motion control.

---

# 3. Lesson 13 Goal

The goal of Lesson 13 is to build a calibrated `Joint` class that converts between:

```text
Joint Angle in Degrees
        ↕
Motor Raw Encoder Position
```

The class must work for:

- single-motor joints
- multi-motor joints
- calibrated HOME positions
- different motor directions
- gear ratios
- calibrated safe limits

The class does not move the robot yet.

Its responsibility is only to produce correct and safe coordinate calculations.

---

# 4. Joint Architecture

The `Joint` class is stored in:

```text
src/armpy/robot/joint.py
```

A `Joint` object contains:

```text
name
motors
home_raw
motor_directions
gear_ratio
negative_limit_raw
middle_raw
positive_limit_raw
min_angle_deg
max_angle_deg
```

Conceptually:

```text
Joint
│
├── Name
├── Motor Objects
├── HOME Calibration
├── Motor Directions
├── Gear Ratio
├── Negative Limit
├── Middle / HOME Limit Reference
├── Positive Limit
├── Minimum Joint Angle
└── Maximum Joint Angle
```

For example:

```text
joint1
└── Motor 1
```

and:

```text
joint2
├── Motor 2
└── Motor 3
```

---

# 5. OOP Concepts Used

## 5.1 Object Invariant

An object invariant is a condition that must always be true for a valid object.

When a `Joint` object is created, its internal state must already be valid.

Examples of invalid states:

```text
No motors
Gear ratio <= 0
Missing HOME data
Missing direction data
Missing limit data
Direction is not +1 or -1
Motor IDs do not match calibration data
```

The constructor calls:

```python
self._validate_configuration()
```

so an invalid `Joint` object is rejected immediately.

This means later methods can assume that the object was created with valid data.

---

## 5.2 Composition

A Joint contains one or more Motor objects.

This is a HAS-A relationship.

```text
Joint HAS-A Motor
```

For a dual-motor joint:

```text
Joint HAS multiple Motors
```

The class therefore stores:

```python
self.motors
```

instead of assuming that every joint contains only one motor.

---

## 5.3 Abstraction

The hardware works with raw encoder counts.

The robot control layer should work with joint angles.

Without `Joint`:

```text
User
 ↓
Raw Encoder Position
```

With `Joint`:

```text
User / Robot
      ↓
Joint Angle in Degrees
      ↓
Joint
      ↓
Raw Encoder Position
```

This hides low-level encoder details behind a higher-level robot interface.

---

# 6. Calibration Data Used by Joint

The `Joint` class does not open JSON files directly.

It receives already-loaded data from other parts of the project.

This keeps responsibilities separate.

The intended architecture is:

```text
robot_joints.json
        +
joint_calibration.json
        ↓
RobotBuilder
        ↓
Joint
```

The `Joint` object receives:

```text
Joint name
Motor objects
HOME positions
Motor directions
Gear ratio
Negative limit positions
Middle positions
Positive limit positions
```

This makes the class independent from file paths and JSON storage.

---

# 7. Joint Coordinate System

The calibrated HOME pose is defined as:

```text
Joint Angle = 0°
```

Therefore:

```text
raw_position == home_raw
```

must produce:

```text
joint_angle == 0°
```

Positive and negative joint angles are determined by the calibrated motor direction.

For example:

```text
direction = +1
```

means a positive joint movement increases the motor raw position.

```text
direction = -1
```

means a positive joint movement decreases the motor raw position.

---

# 8. Counts per Joint Degree

The XL430 encoder uses:

```text
4096 counts per motor revolution
```

The project defines:

```text
gear_ratio =
motor revolutions / joint revolutions
```

Therefore:

```text
counts_per_joint_degree
=
4096 × gear_ratio / 360
```

In code:

```python
def _counts_per_joint_degree(self):

    return (
        self.POSITION_COUNTS_PER_REV
        * self.gear_ratio
        / 360
    )
```

For:

```text
gear_ratio = 1
```

the result is approximately:

```text
11.3778 counts per joint degree
```

---

# 9. Raw Position to Joint Angle

The raw motor position is converted to a joint angle relative to calibrated HOME.

First:

```text
delta_raw =
raw_position - home_raw
```

Then:

```text
joint_angle =
delta_raw / counts_per_joint_degree × direction
```

The method is:

```python
motor_raw_to_joint_angle(motor_id, raw_position)
```

Example:

```text
HOME = 2000
Direction = +1
Current Raw = 2114
```

The joint angle is approximately:

```text
+10°
```

If the same motor direction were `-1`, the same raw increase would represent a negative joint angle.

---

# 10. Joint Angle to Raw Position

The reverse conversion is:

```text
raw_delta =
angle_deg × counts_per_joint_degree × direction
```

Then:

```text
raw_goal =
home_raw + raw_delta
```

The method is:

```python
joint_angle_to_motor_raw(motor_id, angle_deg)
```

Example:

```text
HOME = 2000
Direction = +1
Requested Angle = +10°
```

The resulting raw goal is approximately:

```text
2114
```

For:

```text
Direction = -1
```

the result is approximately:

```text
1886
```

This allows different motors to produce the same physical joint movement.

---

# 11. Dual-Motor Joint

Joint 2 uses two mechanically coupled motors:

```text
joint2
├── Motor 2
└── Motor 3
```

The two motors have opposite encoder directions.

Conceptually:

```text
Joint2 +20°
       |
       +---- Motor 2 moves according to Direction 2
       |
       +---- Motor 3 moves according to Direction 3
```

If:

```text
Motor 2 direction = -1
Motor 3 direction = +1
```

then one positive joint command produces two different raw motor goals.

The method:

```python
calculate_goal_positions(angle_deg)
```

creates one raw goal for every motor in the joint.

Example structure:

```python
{
    "2": 1834,
    "3": 2262
}
```

The exact values depend on calibration data.

---

# 12. Safe Joint Limits

Calibration stores safe software limits in raw encoder values:

```text
negative_limit_raw
middle_raw
positive_limit_raw
```

The `Joint` class converts the negative and positive raw limits into joint angles.

For a single-motor joint:

```text
Negative Raw Limit
        ↓
Negative Joint Angle

Positive Raw Limit
        ↓
Positive Joint Angle
```

For a multi-motor joint, all motor ranges must overlap.

The safe shared range is calculated using:

```python
min_angle_deg = max(negative_angles)
max_angle_deg = min(positive_angles)
```

This creates the intersection of all motor-safe ranges.

The class provides:

```python
is_within_limits(angle_deg)
```

which returns:

```text
True / False
```

and:

```python
check_angle_limits(angle_deg)
```

which raises an exception when the requested angle is outside calibrated limits.

`calculate_goal_positions()` checks the limits before generating any motor goals.

---

# 13. Final Joint API

The main methods implemented in Lesson 13 are:

```python
_counts_per_joint_degree()
```

Calculates encoder counts per joint degree.

```python
motor_raw_to_joint_angle(motor_id, raw_position)
```

Converts one motor raw position into joint degrees.

```python
joint_angle_to_motor_raw(motor_id, angle_deg)
```

Converts a joint angle into a raw motor position.

```python
is_within_limits(angle_deg)
```

Checks whether an angle is inside calibrated safe limits.

```python
check_angle_limits(angle_deg)
```

Rejects unsafe joint angles.

```python
calculate_goal_positions(angle_deg)
```

Calculates raw goals for all motors in the joint.

```python
calculate_joint_angle(raw_positions)
```

Converts the raw positions of all joint motors into one joint angle.

---

# 14. Why Motion Commands Are Not Added Yet

Lesson 13 intentionally does not include methods such as:

```python
move_to()
```

```python
enable_torque()
```

```python
set_goal_position()
```

The reason is safety and separation of responsibilities.

Before sending commands to real hardware, the coordinate model must first be verified independently.

The current development sequence is:

```text
Calibration Data
      ↓
Joint Math
      ↓
Tested Coordinate Conversion
      ↓
Safe Motion Layer
      ↓
Real Hardware Command
```

This prevents a mathematical or calibration error from immediately becoming a physical robot movement.

---

# 15. Testing Strategy

The test file is stored in:

```text
tests/test_joint.py
```

The test uses real project data from:

```text
src/armpy/config/robot_joints.json
data/joint_calibration.json
```

No real motor communication is required.

The `motors` dictionary uses placeholder objects because the current lesson tests coordinate mathematics, not hardware control.

Example:

```python
motors = {
    "2": object(),
    "3": object()
}
```

The tests cover:

- object creation
- stored attributes
- counts per degree
- HOME equals zero degrees
- angle-to-raw conversion
- raw-to-angle conversion
- round-trip conversion
- goal-position calculation
- current joint-angle calculation
- inside-limit checks
- outside-limit rejection
- dual-motor direction behavior
- dual-motor goal generation
- invalid gear ratio rejection
- invalid motor mapping rejection

Both `joint1` and `joint2` are used so the model is tested with single-motor and dual-motor joints.

---

# 16. Numeric Test Summary

The completed Lesson 13 test run produced:

```text
12 tests executed
12 tests passed
0 failures
0 errors
```

Execution result:

```text
Ran 12 tests in 0.002s

OK
```

Coverage summary:

```text
Single-motor joint tested:     joint1
Dual-motor joint tested:       joint2

HOME → 0° validation:          Passed
Raw → Angle conversion:        Passed
Angle → Raw conversion:        Passed
Round-trip conversion:         Passed
Safe limit validation:         Passed
Out-of-limit rejection:        Passed
Goal generation:               Passed
Dual-motor directions:         Passed
Invalid gear ratio checks:     Passed
Invalid motor mapping checks:  Passed
```

The tests use real calibration and robot configuration data, but they do not send motion commands to the physical robot.

---

# 17. Package and Test Execution

The project uses a `src` layout:

```text
Armpy/
├── src/
│   └── armpy/
├── tests/
├── data/
├── docs/
└── pyproject.toml
```

The package is installed in editable mode:

```bash
pip install -e .
```

This allows standard imports such as:

```python
from armpy.robot.joint import Joint
```

without manually setting:

```text
PYTHONPATH=src
```

The editable install also means changes made inside:

```text
src/armpy/
```

are immediately used by the installed development package.

The test can therefore be run directly from VS Code with the selected project interpreter:

```text
~/Armpy/.venv/bin/python
```

or from the terminal using:

```bash
python tests/test_joint.py
```

---

# 18. Lesson 13 Result

At the end of Lesson 13, the project has a tested calibrated joint coordinate model.

The `Joint` class now connects calibration data to future motion control.

The completed path is:

```text
Hardware
    ↓
Discovery
    ↓
Inventory
    ↓
Robot Configuration
    ↓
Calibration
    ↓
Joint Coordinate Model
```

The new `Joint` layer can:

```text
Validate joint configuration
Convert raw encoder values to joint degrees
Convert joint degrees to raw motor goals
Handle opposite motor directions
Handle dual-motor joints
Calculate shared safe limits
Reject unsafe requested angles
Calculate a joint angle from motor positions
```

The class was tested successfully with real ARMPy calibration data.

The next stage is to build the higher-level robot construction layer:

```text
RobotBuilder
    ↓
Create Motor Objects
    ↓
Create Joint Objects
    ↓
Create Robot
```

After that, the project can move toward safe controlled motion on real hardware.
