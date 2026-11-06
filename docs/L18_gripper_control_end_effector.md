# ARMPy — Lesson 18
## Gripper Control and End-Effector Integration

> Project: **ARMPy / ARM 6R**  
> Lesson: **18**  
> Focus: **Gripper abstraction, calibration, control and integration**

---

<a id="toc"></a>
## Table of Contents

1. [Lesson Position](#lesson-position)
2. [Why the Gripper Needs Its Own Class](#why-class)
3. [Lesson Goals](#goals)
4. [OOP Concepts](#oop)
5. [Gripper Architecture](#architecture)
6. [Object Graph](#object-graph)
7. [Calibration Model](#calibration)
8. [Safe Calibration Flow](#safe-calibration)
9. [Opening Percentage Model](#percentage)
10. [Encoder Wrap-Around](#wrap)
11. [Velocity Model](#velocity)
12. [Safe Torque Preparation](#torque)
13. [Gripper Motion Flow](#motion-flow)
14. [Public API](#api)
15. [RobotBuilder Integration](#builder)
16. [Robot Integration](#robot)
17. [Control Menu Integration](#menu)
18. [Gripper in Motion Menu](#motion-menu)
19. [Gripper in Multi-Joint Workflow](#multi-joint)
20. [Gripper Jog](#jog)
21. [Keyboard Gripper Control](#keyboard)
22. [Joint and Gripper Limits](#limits)
23. [Confirmation UX](#confirm)
24. [Pose Integration Status](#pose-status)
25. [Testing Strategy](#testing)
26. [Hardware Validation](#hardware)
27. [Important Bugs and Corrections](#bugs)
28. [Files Added or Changed](#files)
29. [Pseudocode Summary](#pseudocode)
30. [Safety Rules](#safety)
31. [Project Roadmap](#roadmap)
32. [Where We Are Now](#where-now)
33. [Next Step](#next)

---

<a id="lesson-position"></a>
## 1. Lesson Position

Lesson 18 begins after ARMPy already has a working joint-space control layer.

At the start of this lesson the robot can:

- read logical joint angles,
- move one joint,
- move multiple joints,
- move to HOME,
- execute named poses,
- jog joints,
- accept keyboard commands,
- and manage runtime velocity.

But a robot arm is not yet a complete manipulator until it can interact with objects.

Lesson 18 adds the Gripper as a first-class runtime component.

[Back to Table of Contents](#toc)

---

<a id="why-class"></a>
## 2. Why the Gripper Needs Its Own Class

The Gripper is driven by a DYNAMIXEL motor, but the Gripper is not simply a motor.

```text
DynamixelMotor
= actuator hardware abstraction

Gripper
= end-effector behavior abstraction
```

The user should not need to know:

```text
motor ID
Goal Position register
raw encoder values
Torque Enable address
Profile Velocity raw value
```

The high-level interface should be:

```python
robot.open_gripper()
robot.close_gripper()
robot.set_gripper_opening(50)
```

This is why Lesson 18 introduces:

```text
src/armpy/robot/gripper.py
```

---

<a id="goals"></a>
## 3. Lesson Goals

The goals are:

- create a dedicated `Gripper` class,
- reuse the existing Gripper motor object,
- calibrate safe open and closed endpoints,
- use a 0–100% opening model,
- support Open and Close,
- support arbitrary opening percentage,
- support Gripper velocity,
- read Gripper state,
- hold the current position,
- enable torque safely,
- integrate Gripper with `RobotBuilder`,
- integrate Gripper with `Robot`,
- add Gripper to the CLI,
- add Gripper to Motion,
- add Gripper to Jog,
- add Gripper to keyboard teleoperation,
- show Gripper limits with joint limits,
- test all logic using fake hardware.

---

<a id="oop"></a>
## 4. OOP Concepts

### Composition

```text
Gripper HAS-A DynamixelMotor
```

not:

```text
Gripper IS-A DynamixelMotor
```

Example:

```python
class Gripper:

    def __init__(
        self,
        motor,
        config,
        calibration
    ):
        self.motor = motor
```

### Dependency Injection

`RobotBuilder` creates/reuses the existing motor object and injects it into `Gripper`.

### Encapsulation

Higher-level code uses:

```python
gripper.open()
gripper.close()
gripper.set_opening(...)
gripper.read_state()
```

The Gripper hides raw motor details.

### Single Responsibility

| Class | Responsibility |
|---|---|
| `DynamixelMotor` | Motor register I/O |
| `Gripper` | End-effector behavior |
| `RobotBuilder` | Construct runtime objects |
| `Robot` | Public robot API |
| `RobotControlMenu` | User interaction |

### Facade

`Robot` exposes Gripper commands so callers do not depend on Gripper internals.

---

<a id="architecture"></a>
## 5. Gripper Architecture

```text
RobotControlMenu
       │
       ▼
     Robot
       │
       ▼
    Gripper
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
   Motor 7
       │
       ▼
Physical Gripper
```

---

<a id="object-graph"></a>
## 6. Object Graph

The same Motor 7 object must be reused:

```text
Robot.motors["7"]
       │
       └──────── same object ────────┐
                                     ▼
                               Gripper.motor
```

This is an object-graph invariant.

`RobotBuilder` should not create a second motor object for the same physical actuator.

---

<a id="calibration"></a>
## 7. Calibration Model

The Gripper requires two physical endpoints:

```text
Fully Open Safe
Fully Closed Safe
```

The project stores:

```text
open_raw
closed_raw
```

Example:

```json
{
    "gripper": {
        "motor_id": 7,
        "reference": {
            "calibrated": true,
            "raw": 2029
        },
        "open_close": {
            "calibrated": true,
            "open_raw": 2553,
            "closed_raw": 2044
        }
    }
}
```

The real values come from hardware calibration, not from hard-coded assumptions.

---

<a id="safe-calibration"></a>
## 8. Safe Calibration Flow

### Pseudocode

```text
CONNECT to robot bus

READ Gripper configuration
READ hardware inventory
CREATE Motor 7 object

READ torque state
IF torque ON:
    disable torque
    verify torque OFF

ASK user to move Gripper to FULLY OPEN SAFE
READ Present Position
store open_raw

ASK user to move Gripper to FULLY CLOSED SAFE
READ Present Position
store closed_raw

VALIDATE open != closed

BACKUP calibration file
SAVE open/closed values

LEAVE torque OFF
```

### Important design correction

The runtime `RobotBuilder` can require valid Gripper calibration.

A calibration script cannot depend on a fully valid runtime Gripper, because calibration is exactly what is missing.

Therefore the calibration script directly creates the required motor object instead of requiring the complete runtime robot.

---

<a id="percentage"></a>
## 9. Opening Percentage Model

The project defines:

```text
0%   = fully closed
100% = fully open
```

Example:

```text
closed_raw = 1000
open_raw   = 2000
```

Then:

```text
0%   → 1000
25%  → 1250
50%  → 1500
100% → 2000
```

Conceptually:

```text
goal =
    closed_raw
    + percentage / 100
    × calibrated_span
```

This gives the operator a meaningful unit.

---

<a id="wrap"></a>
## 10. Encoder Wrap-Around

Single-turn encoder values are circular.

Example:

```text
closed = 4000
open   = 100
```

The shortest movement crosses:

```text
4095 → 0
```

A shortest-delta formula is therefore used:

```text
delta =
    ((position - reference + half_range)
     % counts_per_revolution)
    - half_range
```

This behavior is covered by unit tests.

---

<a id="velocity"></a>
## 11. Velocity Model

Joint and Gripper velocity use different units.

### Joint

```text
deg/s
```

### Gripper

```text
motor RPM
```

Typical Gripper constants:

```python
DEFAULT_VELOCITY_RPM = 5.0
MIN_VELOCITY_RPM = 0.5
MAX_VELOCITY_RPM = 30.0
```

Runtime setter:

```python
robot.set_default_gripper_velocity(...)
```

The units are intentionally kept separate.

---

<a id="torque"></a>
## 12. Safe Torque Preparation

Unsafe sequence:

```text
Torque OFF
→ Gripper moved manually
→ old Goal Position remains
→ Torque ON
→ unexpected motion
```

Safe sequence:

```text
READ current position
STAGE current position as goal
ENABLE torque
VERIFY torque
WRITE requested target
```

This mirrors the safety strategy already used for joint motion.

---

<a id="motion-flow"></a>
## 13. Gripper Motion Flow

### Pseudocode

```text
RECEIVE opening target %

REQUIRE calibration

VALIDATE percentage

CALCULATE goal raw

PREFLIGHT motor:
    validate goal
    check Position Mode
    check Drive Mode
    check Hardware Error

VALIDATE velocity
SET Profile Velocity

PREPARE torque safely

WRITE Goal Position

IF wait:
    poll Present Position
    compare raw error
    return when tolerance reached
    timeout if required
```

---

<a id="api"></a>
## 14. Public API

### Gripper API

```python
gripper.open()
gripper.close()
gripper.set_opening(50)
gripper.move_to_raw(...)
gripper.hold()
gripper.read_state()
gripper.set_default_velocity_rpm(...)
```

### Robot facade API

```python
robot.open_gripper()

robot.close_gripper()

robot.set_gripper_opening(
    50
)

robot.read_gripper_state()

robot.read_gripper_raw_position()

robot.hold_gripper()

robot.set_default_gripper_velocity(
    10
)
```

---

<a id="builder"></a>
## 15. RobotBuilder Integration

Before Lesson 18, Gripper information was represented as a dictionary:

```python
{
    "motor": ...,
    "config": ...,
    "calibration": ...
}
```

Lesson 18 changes this into a real object:

```python
Gripper(...)
```

This changes the Gripper from:

```text
data container
```

to:

```text
state + behavior
```

which is a better domain model.

---

<a id="robot"></a>
## 16. Robot Integration

`Robot` validates that:

- the Gripper is a `Gripper` object,
- its motor exists in `Robot.motors`,
- its motor object is the same object as the robot motor collection.

Then Robot delegates:

```python
def open_gripper(...):
    return self.gripper.open(...)
```

This keeps `Robot` as the public facade.

---

<a id="menu"></a>
## 17. Control Menu Integration

Dedicated Gripper menu:

```text
--- Gripper Control ---

1. Read Gripper State
2. Open Gripper
3. Close Gripper
4. Set Opening Percentage
5. Hold Gripper
6. Set Gripper Velocity
0. Back
```

The main menu includes:

```text
6. Gripper Control
```

But Lesson 18 also integrates the Gripper wherever joint control exists.

---

<a id="motion-menu"></a>
## 18. Gripper in Motion Menu

Current intended Motion structure:

```text
--- Motion ---

1. Move One Joint / Gripper
2. Move Multiple Joints
3. Move HOME
4. Hold Joint Position
5. Show Joint / Gripper Limits
6. Gripper Control
7. Save Current Position
0. Back
```

`Move One Joint / Gripper` shows:

```text
1. joint1 - base_rotation
2. joint2 - shoulder [synchronized]
3. joint3 - elbow
4. joint4 - wrist_pitch
5. joint5 - wrist_rotation
6. gripper - end effector
0. Back
```

The Gripper is shown beside joints in the UI, but it is not modeled as a `Joint`.

### Joint target

```text
target unit = degrees
velocity = deg/s
```

### Gripper target

```text
target unit = opening %
velocity = RPM
```

---

<a id="multi-joint"></a>
## 19. Gripper in Multi-Joint Workflow

Multi-Joint can optionally ask for Gripper opening:

```text
joint1 [current ...]:
joint2 [current ...]: 20
joint3 [current ...]: -40
joint4 [current ...]:
joint5 [current ...]:
Gripper opening [0-100 %, Enter = skip]: 50
```

At this stage this is not yet a true synchronized arm-plus-Gripper trajectory.

It may execute:

```text
arm movement
then
Gripper movement
```

True synchronized trajectory execution belongs to a later lesson.

---

<a id="jog"></a>
## 20. Gripper Jog

Gripper Jog changes opening by percentage steps.

Example:

```text
Current = 50%
Step = 5%

Open more  → 55%
Close more → 45%
```

Targets are clamped:

```text
0% ≤ target ≤ 100%
```

Typical menu:

```text
Current Gripper opening: 50.0%

O = Open more
C = Close more
0 = Back
```

---

<a id="keyboard"></a>
## 21. Keyboard Gripper Control

Lesson 18 extends keyboard control.

| Key | Action |
|---|---|
| `Q/A` | joint1 +/- |
| `W/S` | joint2 +/- |
| `E/D` | joint3 +/- |
| `R/F` | joint4 +/- |
| `T/G` | joint5 +/- |
| `O` | Open Gripper |
| `C` | Close Gripper |
| `H` | HOME |
| `X` | Exit |

The keyboard adapter only maps input. The Robot/Gripper layer still performs the actual motion.

---

<a id="limits"></a>
## 22. Joint and Gripper Limits

The limits view should show both joint limits and Gripper limits.

Example:

```text
joint1: -82.00 to 201.45 deg
joint2: -29.97 to 128.58 deg
joint3: -148.18 to 2.90 deg
joint4: -97.73 to 83.06 deg
joint5: -272.46 to 1.23 deg

Gripper:
0.00 to 100.00 %
0.00%   = Fully Closed
100.00% = Fully Open
Closed raw: 2044
Open raw:   2553
```

This makes calibrated end-effector limits visible to the operator.

---

<a id="confirm"></a>
## 23. Confirmation UX

Older prompts used:

```text
[y/n]
```

and empty Enter was interpreted as cancellation.

The improved standard is:

```text
[Enter=yes / n=no]
```

Behavior:

```text
Enter → Yes
y     → Yes
yes   → Yes
n     → No
no    → No
```

A central helper such as:

```python
_confirm(...)
```

should be used for:

- single-joint motion,
- multi-joint motion,
- pose execution,
- HOME,
- Gripper Open,
- Gripper Close,
- Gripper percentage motion,
- save pose,
- overwrite pose,
- replace pose,
- delete pose.

This avoids duplicated confirmation logic.

---

<a id="pose-status"></a>
## 24. Pose Integration Status

Current named poses primarily store joint angles:

```json
{
    "joint1": 20,
    "joint2": 30,
    "joint3": -40,
    "joint4": 10,
    "joint5": 0
}
```

A future schema can include the Gripper:

```json
{
    "joints": {
        "joint1": 20,
        "joint2": 30,
        "joint3": -40,
        "joint4": 10,
        "joint5": 0
    },
    "gripper": {
        "opening_percent": 50
    }
}
```

### Save Current Position issue discovered

The Save Current Position path called:

```text
PoseController.get_limit_warnings()
→ PoseLibrary.get_limit_warnings()
```

but `PoseLibrary.get_limit_warnings()` was missing.

This produced:

```text
AttributeError:
'PoseLibrary' object has no attribute 'get_limit_warnings'
```

The fix is to implement that contract in `PoseLibrary` and re-run the full test suite.

---

<a id="testing"></a>
## 25. Testing Strategy

Dedicated file:

```text
tests/test_gripper.py
```

The test suite uses fake motor/connection objects.

Important tests:

- motor reuse,
- calibration detection,
- 0% mapping,
- 100% mapping,
- 50% mapping,
- 25% mapping,
- invalid percentage,
- invalid velocity,
- Open,
- Close,
- arbitrary opening,
- profile velocity,
- state reading,
- Hold,
- missing calibration,
- partial calibration,
- equal open/closed rejection,
- motor ID mismatch,
- wrap-around,
- safe torque enable.

During development:

```text
28 Gripper tests
```

passed independently.

Later the full project suite reported:

```text
70 tests
OK
```

after Gripper integration.

---

<a id="hardware"></a>
## 26. Hardware Validation

One physical calibration session produced:

```text
Closed raw = 2044
Open raw   = 2553
```

A later real motion test reported:

```text
Current opening: 49.90%
Target opening: 100.00%
Goal raw: 2553
Velocity: 20 RPM
Final raw: 2545
```

This validates the complete path:

```text
percentage
→ raw goal
→ velocity
→ torque preparation
→ physical movement
→ final position
```

---

<a id="bugs"></a>
## 27. Important Bugs and Corrections

### Old tests still used dictionary Gripper

Old:

```python
gripper["motor"]
```

New:

```python
gripper.motor
```

### Robot expected `Gripper`, tests built `dict`

Many test failures came from one architectural mismatch.

### Calibration schema mismatch

Some code expected:

```text
open.raw
closed.raw
```

while project data used:

```text
open_close.open_raw
open_close.closed_raw
```

The reader was updated for compatibility.

### Calibration circular dependency

Runtime Builder required calibration before a calibration script could build the runtime robot.

The calibration script was changed to build only the required motor.

### Fake torque state

A fake motor originally always returned Torque ON.

It was changed to use mutable:

```python
self.torque_enabled
```

so Torque OFF safety could be tested.

### Missing PoseLibrary interface

`PoseController` delegated to a method missing from `PoseLibrary`.

This exposed an important rule:

> Delegation requires an explicit and implemented interface contract.

---

<a id="files"></a>
## 28. Files Added or Changed

| File | Purpose |
|---|---|
| `src/armpy/robot/gripper.py` | Gripper model |
| `src/armpy/robot/robot_builder.py` | Build Gripper object |
| `src/armpy/robot/robot.py` | Robot-level Gripper API |
| `src/armpy/control/control_menu.py` | CLI integration |
| `src/armpy/control/keyboard_jog.py` | Keyboard Gripper control |
| `src/armpy/control/jog_controller.py` | Shared teleoperation path |
| `scripts/calibrate_gripper_limits.py` | Gripper endpoint calibration |
| `data/joint_calibration.json` | Open/closed raw endpoints |
| `tests/test_gripper.py` | Gripper tests |
| `tests/test_robot.py` | Robot + Gripper tests |
| `tests/test_robot_builder.py` | Builder integration tests |

---

<a id="pseudocode"></a>
## 29. Pseudocode Summary

### Build Gripper

```text
READ config
READ calibration
GET existing Motor 7
CREATE Gripper
VALIDATE
RETURN Gripper
```

### Calibrate Gripper

```text
CONNECT
CREATE Motor 7
DISABLE torque
CAPTURE open raw
CAPTURE closed raw
VALIDATE
BACKUP file
SAVE calibration
```

### Open

```text
REQUIRE calibration
goal = open_raw
PREFLIGHT
SET velocity
PREPARE torque
WRITE goal
WAIT
RETURN result
```

### Percentage Control

```text
READ percentage
VALIDATE 0..100
CALCULATE raw
MOVE
```

### Read State

```text
READ raw
CALCULATE opening %
READ torque
RETURN state dictionary
```

### Motion Target Selection

```text
SHOW joint1..joint5 + gripper

IF joint:
    ask degrees

IF gripper:
    ask opening %
```

---

<a id="safety"></a>
## 30. Safety Rules

- never guess endpoints,
- keep torque OFF during manual calibration,
- do not calibrate against a hard mechanical stop,
- leave a small mechanical margin,
- start with low velocity,
- test intermediate percentages first,
- remove objects during initial Close tests,
- do not use Position Control as a fake force-control system,
- stop if there is abnormal heat, vibration or strain.

Lesson 18 is primarily **position control**, not force control.

---

<a id="roadmap"></a>
## 31. Project Roadmap

| Phase | Topic | Status |
|---|---|---|
| 1 | Python package structure | ✅ |
| 2 | DYNAMIXEL communication | ✅ |
| 3 | Hardware discovery | ✅ |
| 4 | Robot configuration | ✅ |
| 5 | Joint calibration | ✅ Core |
| 6 | Joint coordinate model | ✅ |
| 7 | RobotBuilder | ✅ |
| 8 | Robot runtime model | ✅ |
| 9 | Safe joint motion | ✅ |
| 10 | Velocity control | ✅ |
| 11 | Multi-joint motion | ✅ |
| 12 | Pose management | ✅ |
| 13 | Jog / keyboard control | ✅ |
| 14 | Joystick adapter | 🟡 Hardware validation pending |
| 17 | Joint-space control integration | ✅ |
| **18** | **Gripper / end-effector control** | **✅ Core complete, final UI cleanup ongoing** |
| 19 | Coordinated joint trajectory | ⬜ |
| 20 | Forward kinematics | ⬜ |
| 21 | Inverse kinematics | ⬜ |
| 22 | Cartesian control | ⬜ |
| 23 | Trajectory planning | ⬜ |
| 24 | Feedback tracking | ⬜ |
| 25 | Advanced safety | ⬜ |
| 26 | ROS 2 | ⬜ |
| 27 | Simulation | ⬜ |
| 28 | Pick and Place | ⬜ |

---

<a id="where-now"></a>
## 32. Where We Are Now

At the end of the current Lesson 18 work, ARMPy has:

### Software

- dedicated `Gripper` class,
- calibrated open/closed model,
- percentage opening,
- safe torque preparation,
- Gripper velocity,
- state reading,
- RobotBuilder integration,
- Robot facade API,
- dedicated Gripper menu,
- Gripper inside Motion,
- Gripper beside joints in target selection,
- Gripper limits beside joint limits,
- Gripper Jog design,
- keyboard Open/Close controls,
- fake-hardware unit tests.

### Hardware

Basic physical Gripper motion has been verified.

The project successfully moved the Gripper from about 50% to 100% in a real run.

### Test status

The latest full project run before the newest UI/pose-helper changes reported:

```text
Ran 70 tests
OK
ALL TESTS PASSED
```

### Current cleanup items

These should be revalidated after the latest changes:

- `PoseLibrary.get_limit_warnings()`,
- centralized Enter-as-Yes confirmation,
- Save Current Position,
- Gripper Jog,
- keyboard Open/Close,
- optional Gripper value inside named poses.

Core Gripper control is implemented; final UI and pose integration are the current cleanup phase.

---

<a id="next"></a>
## 33. Next Step

After Lesson 18 the robot can control both:

```text
arm joints
+
end effector
```

The next major layer should be coordinated trajectory control.

### Lesson 19 — Coordinated Joint Trajectory

Topics:

- synchronized arrival time,
- Profile Acceleration,
- waypoint representation,
- interpolation,
- non-blocking motion state,
- trajectory execution,
- cancellation,
- feedback.

After that:

```text
Lesson 20 → Forward Kinematics
Lesson 21 → Inverse Kinematics
Lesson 22 → Cartesian Control
Lesson 23 → Trajectory Planning
Lesson 24 → Feedback Tracking
Lesson 25 → Advanced Safety
Lesson 26 → ROS 2
Lesson 27 → Simulation
Lesson 28 → Pick and Place
```

The future manipulation pipeline becomes:

```text
Target object
    ↓
Cartesian target
    ↓
Inverse Kinematics
    ↓
Joint trajectory
    ↓
Arm movement
    ↓
Gripper close
    ↓
Transport
    ↓
Gripper open
```

---

## End of Lesson 18

Lesson 18 changes the Gripper from a raw motor entry into a real software component:

```text
Robot
├── Joints
└── Gripper
```

Both are controlled through high-level APIs while the low-level DYNAMIXEL details remain behind the hardware abstraction layer.
