# Lesson 12 — Unified Robot Calibration System

## Overview

Lesson 12 refactors the earlier calibration approach into one unified calibration system for ARMPy.

In Lesson 11, HOME calibration was implemented as a separate workflow. Direction calibration was also started as a separate script. During Lesson 12, this design was changed so all calibration operations use one shared calibration model, one menu-driven interface, and one persistent calibration file.

The final calibration workflow now includes:

- HOME / zero calibration
- Motor direction calibration
- Joint safe-limit calibration
- Gripper calibration
- Calibration status
- Calibration verification
- Automatic saving after accepted measurements
- Repeating one joint without restarting the complete process

The goal of this refactor is to keep calibration logic in one place and make the calibration process easier to repeat, verify, and extend.

---

## Main Architecture

The calibration system is separated into three main files:

```text
calibrate_robot.py
        |
        v
CalibrationMenu
        |
        v
JointCalibration
        |
        v
DynamixelMotor
        |
        v
Physical Motors
```

Supporting configuration and hardware information are loaded from:

```text
config/robot_joints.json
config/hardware_inventory.json
config/joint_calibration.json
```

Each class or file has a separate responsibility.

---

## 1. `calibrate_robot.py`

`calibrate_robot.py` is the application entry point.

Its responsibility is not to perform calibration calculations. It only creates and connects the objects needed by the calibration system.

The startup sequence is:

```text
Open DYNAMIXEL connection
        |
        v
Ping CM-550
        |
        v
Prepare USB bypass access
        |
        v
Load HardwareInventory
        |
        v
Load RobotConfig
        |
        v
Create JointCalibration
        |
        v
Load or create calibration data
        |
        v
Create CalibrationMenu
        |
        v
Start menu
        |
        v
Close connection safely
```

This file connects the application layers together.

Typical object creation looks like:

```python
hardware_inventory = HardwareInventory()

robot_config = RobotConfig("config/robot_joints.json")

calibration = JointCalibration(
    connection=connection,
    hardware_inventory=hardware_inventory,
    robot_config=robot_config
)

menu = CalibrationMenu(
    calibration=calibration,
    file_path="config/joint_calibration.json"
)

menu.show()
```

This is an example of **Dependency Injection**.

`JointCalibration` receives the connection, hardware inventory, and robot configuration instead of creating them internally.

---

## 2. `calibration_menu.py`

`CalibrationMenu` is the user interface for manual calibration.

Its responsibility is:

- display calibration options
- ask the user to move the robot manually
- select one joint or all joints
- display measured values
- ask whether a result should be accepted, retried, or skipped
- call the correct `JointCalibration` method
- save accepted results automatically

The menu does not directly communicate with DYNAMIXEL registers and does not calculate calibration data itself.

The main menu is conceptually:

```text
ARMPy Calibration

1. Home / Zero Calibration
2. Direction Calibration
3. Joint Limit Calibration
4. Gripper Calibration
5. Calibration Status
6. Verify Calibration
7. Exit
```

Because accepted measurements are automatically saved, a separate manual save step is not required for normal use.

---

## 3. `joint_calibration.py`

`JointCalibration` contains the actual calibration logic and calibration state.

It is a **stateful service object**.

When the object is first created:

```python
self.calibration = None
```

Before calibration operations can be used, the object must either:

```text
load existing calibration
```

or:

```text
create a new calibration structure
```

After that, `self.calibration` contains the current in-memory calibration data.

`JointCalibration` is responsible for:

- validating robot-to-motor mapping
- creating `DynamixelMotor` objects
- reading raw motor positions
- checking that torque is OFF before manual movement
- creating schema version 2
- loading calibration data
- saving calibration data
- HOME calibration
- direction calculation
- joint-limit validation
- gripper calibration storage
- calibration status
- calibration verification

---

# Calibration Data Flow

The complete data flow is:

```text
Physical Robot
      |
      v
DynamixelMotor
      |
      v
Raw Position Readings
      |
      v
JointCalibration
      |
      v
Validated Calibration Data
      |
      v
CalibrationMenu
      |
      v
User Accepts Result
      |
      v
Auto Save
      |
      v
config/joint_calibration.json
```

The important rule is:

> Measurements are read first, shown to the user, validated, and only then stored when the user accepts them.

This allows one joint to be repeated without overwriting good data unnecessarily.

---

# Configuration vs Calibration Data

The project separates configuration from measured calibration data.

## `robot_joints.json`

This file describes the robot structure and user-defined conventions.

Examples:

```text
joint name
motor IDs
positive-motion description
gear ratio
```

For example:

```json
"joint1": {
    "name": "base_rotation",
    "motor_ids": [1],
    "positive_motion": "Rotate the base counter-clockwise when viewed from above."
}
```

`positive_motion` defines the physical positive direction that must be used consistently during direction calibration.

## `joint_calibration.json`

This file stores measured data from the real robot.

Examples:

```text
HOME raw positions
measured encoder directions
negative safe limits
middle / HOME readings
positive safe limits
gripper reference
gripper open position
gripper close position
```

The important design rule is:

```text
Robot configuration = intended robot definition

Calibration file = measured hardware-specific data
```

---

# Calibration Schema Version 2

The refactor introduced schema version 2.

A simplified structure is:

```json
{
    "schema_version": 2,
    "robot_name": "ARMPy_6R",
    "calibrated_at": "...",

    "joints": {
        "joint1": {
            "name": "base_rotation",
            "motor_ids": [1],

            "home": {
                "calibrated": true,
                "raw": {
                    "1": 2025
                }
            },

            "direction": {
                "calibrated": true,
                "positive_motion": "...",

                "measurement": {
                    "before_raw": {},
                    "after_raw": {},
                    "delta_raw": {}
                },

                "motor_directions": {
                    "1": 1
                }
            },

            "limits": {
                "calibrated": true,
                "negative_limit_raw": {},
                "middle_raw": {},
                "positive_limit_raw": {}
            }
        }
    },

    "gripper": {
        "motor_id": 7,

        "reference": {
            "calibrated": true,
            "raw": 2362
        },

        "open_close": {
            "calibrated": true,
            "open_raw": 3000,
            "close_raw": 1000
        }
    }
}
```

The exact raw values depend on the real robot and are not fixed constants.

---

# HOME Calibration

HOME calibration defines the physical reference pose of the robot.

The operation is manual.

Sequence:

```text
Support robot mechanically
        |
        v
Check torque OFF
        |
        v
Move robot to chosen HOME pose
        |
        v
Read raw motor positions
        |
        v
Display measurements
        |
        v
Store HOME values
        |
        v
Auto Save
```

For a single-motor joint:

```text
joint1
    |
    +-- Motor 1 HOME raw
```

For the shoulder:

```text
joint2
    |
    +-- Motor 2 HOME raw
    |
    +-- Motor 3 HOME raw
```

The gripper also has a separate reference position.

HOME can be captured for the complete robot or repeated for one joint.

If HOME is intentionally changed, previously measured limits may no longer be valid and should be recalibrated.

---

# Direction Calibration

Direction calibration determines how each motor encoder changes when the physical joint moves in the defined positive direction.

The system does not guess the physical positive direction.

That direction comes from:

```text
robot_joints.json
        |
        v
positive_motion
```

Example:

```text
Joint 1 positive direction:
Rotate the base counter-clockwise when viewed from above.
```

The workflow is:

```text
Require HOME calibration
        |
        v
Check torque OFF
        |
        v
Read BEFORE position
        |
        v
User moves joint a small amount
in the defined positive direction
        |
        v
Read AFTER position
        |
        v
delta = AFTER - BEFORE
        |
        v
delta > 0  -> direction = +1
delta < 0  -> direction = -1
        |
        v
Validate
        |
        v
User accepts
        |
        v
Store + Auto Save
```

Direction calibration intentionally requires a small movement.

This prevents a large manual movement from being used only to determine the encoder sign.

The stored data includes:

- before position
- after position
- raw delta
- final motor direction

---

## Dual-Motor Shoulder

Joint 2 uses two motors:

```text
joint2
├── Motor 2
└── Motor 3
```

Both motors drive the same physical joint, but their encoder directions are opposite.

A valid result is conceptually:

```text
Motor 2 -> +1
Motor 3 -> -1
```

or the opposite pair, depending on the defined positive physical direction.

The important requirement is that the two directions are opposite.

---

# Joint Limit Calibration

Joint-limit calibration records **safe software limits**, not hard mechanical-stop positions.

The user should leave a safety margin before the physical hard stop.

The workflow is:

```text
Require HOME
        |
        v
Require Direction
        |
        v
Check torque OFF
        |
        v
Move to NEGATIVE safe limit
        |
        v
Read positions
        |
        v
Return near calibrated HOME
        |
        v
Read middle positions
        |
        v
Move to POSITIVE safe limit
        |
        v
Read positions
        |
        v
Validate direction and range
        |
        v
Store + Auto Save
```

Three points are stored:

```text
negative_limit_raw
middle_raw
positive_limit_raw
```

The middle measurement is used as a reference between the two sides of the joint range.

The validation checks that:

- the expected motors are present
- HOME was calibrated
- direction was calibrated
- the movement is large enough to be meaningful
- negative-to-middle movement agrees with the calibrated encoder direction
- middle-to-positive movement agrees with the calibrated encoder direction
- the middle position is close to the calibrated HOME pose

For manual calibration with torque OFF, raw position values may extend outside the simple `0..4095` single-turn range. Therefore movement delta is treated as:

```python
delta = after - before
```

instead of forcing every measurement into a 4096-count wrap.

A separate single-turn comparison can be used when checking whether two readings represent approximately the same physical HOME orientation.

---

# Gripper Calibration

The gripper is treated separately from the five arm joints.

It is an end-effector actuator and is not another revolute arm joint.

The gripper calibration can store:

```text
reference position
open position
close position
```

The process is manual:

```text
Check gripper torque OFF
        |
        v
Move gripper manually
        |
        v
Read raw position
        |
        v
Display
        |
        v
Accept
        |
        v
Store + Auto Save
```

The open and close positions must be sufficiently different.

---

# Automatic Saving

One of the main changes in Lesson 12 is automatic persistence.

The save sequence is:

```text
Measurement
      |
      v
Validation
      |
      v
User Accepts
      |
      v
Update JointCalibration state
      |
      v
_auto_save()
      |
      v
joint_calibration.json
```

This means calibration progress is not lost if the user exits later.

It also allows one joint to be repeated independently.

For example:

```text
Joint 1 direction -> saved
Joint 2 direction -> saved
Joint 3 direction -> saved
Joint 4 -> retry later
```

The previously accepted joints remain stored.

---

# Calibration Status

`get_status()` provides a simple high-level summary.

Example:

```text
joint1: HOME=True DIR=True LIMITS=True
joint2: HOME=True DIR=True LIMITS=True
joint3: HOME=True DIR=True LIMITS=True
joint4: HOME=True DIR=True LIMITS=True
joint5: HOME=True DIR=True LIMITS=True

Gripper: REF=True OPEN/CLOSE=True
```

Status answers:

> Has this calibration category been completed and stored?

It does not by itself prove that the physical calibration is correct.

---

# Calibration Verification

`verify()` performs logical and structural checks on the stored calibration data.

The verification can check:

- all expected joints exist
- motor IDs match `RobotConfig`
- HOME data exists
- direction data exists
- each direction is `+1` or `-1`
- the stored positive-motion definition matches configuration
- shoulder motor directions are opposite
- negative, middle, and positive limit data contain the expected motors
- limit directions are logically consistent
- middle positions are near HOME
- gripper motor mapping is correct
- gripper reference exists
- gripper open and close positions exist
- gripper open and close positions are not too close

The verification result is a **stored-data verification**.

It is not the same as a live motion-safety test.

```text
Stored data verification PASS
        !=
Robot is automatically safe to move
```

A later motion-safety layer can use verified calibration data before enabling robot motion.

---

# Manual Calibration and Safety

All calibration movement in this lesson is manual.

The calibration code does not command automatic joint motion.

During manual calibration:

- the target motor torque must be OFF
- all motors of a multi-motor joint must be OFF
- the arm must be mechanically supported
- the user moves only the requested joint
- joints must never be forced against hard stops
- joint limits are safe software limits with mechanical margin
- direction calibration uses a small movement
- accepted data is saved only after validation

The calibration system checks torque state but does not automatically turn torque OFF.

This is intentional because automatically removing torque from a loaded robot arm can cause links to fall.

---

# OOP Concepts Used in Lesson 12

This refactor applies several OOP concepts already introduced in the project.

## Separation of Responsibilities

```text
calibrate_robot.py
    -> application startup

CalibrationMenu
    -> user interaction and workflow

JointCalibration
    -> calibration state and logic

DynamixelMotor
    -> low-level motor access
```

## Dependency Injection

`JointCalibration` receives its dependencies:

```text
DynamixelConnection
HardwareInventory
RobotConfig
```

instead of creating them internally.

## Composition

```text
CalibrationMenu
    HAS-A
JointCalibration
```

and:

```text
JointCalibration
    HAS
DynamixelMotor objects
```

## Stateful Service Object

`JointCalibration` keeps the active calibration data in memory:

```python
self.calibration
```

The object can transition through states such as:

```text
Not loaded
    |
    v
Loaded / Created
    |
    v
HOME calibrated
    |
    v
Direction calibrated
    |
    v
Limits calibrated
```

## Configuration-Driven Design

The robot mapping and positive-motion conventions come from configuration instead of being duplicated throughout the calibration code.

---

# Refactor Result

Before Lesson 12, calibration responsibilities were separated across individual scripts.

Conceptually:

```text
calibrate_joints.py
calibrate_directions.py
```

The new design is:

```text
calibrate_robot.py
calibration_menu.py
joint_calibration.py
        |
        v
config/joint_calibration.json
```

All calibration categories now work through the same `JointCalibration` object and the same stored schema.

This gives the project:

- one calibration data model
- one interactive calibration interface
- one persistent calibration file
- reusable calibration methods
- per-joint repeat support
- automatic saving
- stronger verification
- cleaner separation between UI, calibration logic, and motor communication

---

# Final Lesson 12 Architecture

```text
User
 |
 v
CalibrationMenu
 |
 |  HOME
 |  Direction
 |  Limits
 |  Gripper
 |  Status
 |  Verify
 |
 v
JointCalibration
 |
 +-- RobotConfig
 |
 +-- HardwareInventory
 |
 +-- DynamixelMotor objects
 |
 v
DYNAMIXEL Connection
 |
 v
CM-550
 |
 v
Physical Robot
```

Persistent data:

```text
RobotConfig
    |
    +--> robot_joints.json

HardwareInventory
    |
    +--> hardware_inventory.json

JointCalibration
    |
    +--> joint_calibration.json
```

---

# Lesson 12 Checkpoint

At the end of this lesson, ARMPy has a unified manual calibration framework capable of:

```text
HOME calibration            ✓
Motor direction calibration ✓
Joint safe-limit calibration ✓
Gripper calibration         ✓
Per-joint repeat             ✓
Automatic save               ✓
Calibration status           ✓
Stored-data verification     ✓
```

The next project stages can use this calibration data to finish the `Joint` abstraction, build the complete robot object, and later add safe commanded motion.
