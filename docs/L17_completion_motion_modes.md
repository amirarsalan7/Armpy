# ARMPy — Lesson 17 Completion
## Coordinated Multi-Joint Motion, Ordered Motion, Pose Modes, HOME Modes, and Physical Validation

> Project: **ARMPy / ARM 6R**  
> Lesson: **17 — Completion Phase**  
> Status before this phase: synchronized Multi-Joint motion already works.  
> Goal of this phase: add coordinated arrival, sequential orders, custom order, selectable motion mode for Pose/HOME, and complete physical validation.

---

<a id="toc"></a>
## Table of Contents

1. [Current Position in the Roadmap](#roadmap-position)
2. [Completion Goals](#completion-goals)
3. [Why This Change Is Needed](#why)
4. [Simultaneous Start vs Simultaneous Arrival](#start-vs-arrival)
5. [Motion Modes](#motion-modes)
6. [OOP Design](#oop-design)
7. [Robot API Changes](#robot-api)
8. [Motion Mode Validation](#mode-validation)
9. [Motion Order Resolution](#order-resolution)
10. [Coordinated Arrival Velocity](#coordinated-arrival)
11. [Multi-Joint Preview Changes](#preview)
12. [Multi-Joint Execution Changes](#execution)
13. [Sequential Forward](#forward)
14. [Sequential Reverse](#reverse)
15. [Custom Joint Order](#custom)
16. [PoseController Integration](#pose-controller)
17. [Named Pose Motion Mode](#named-pose)
18. [HOME Motion Mode](#home)
19. [CLI / Control Menu Changes](#cli)
20. [Gripper Interaction](#gripper)
21. [Unit Tests](#unit-tests)
22. [Physical Test Plan](#physical-tests)
23. [Keyboard Jog Test](#keyboard-test)
24. [Joint2 Dual-Motor Test](#joint2-test)
25. [Collision Avoidance Limitations](#collision)
26. [Validation Commands](#validation)
27. [Final Lesson 17 Checklist](#final-checklist)
28. [Updated Roadmap](#updated-roadmap)
29. [What Comes Next](#next)

---

<a id="roadmap-position"></a>
## 1. Current Position in the Roadmap

Before this completion phase, ARMPy already has:

```text
Single-Joint Motion
        ✅
Joint Velocity
        ✅
Synchronized Multi-Joint Goal Write
        ✅
Named Poses
        ✅
HOME
        ✅
Jog
        ✅
Keyboard Control
        ✅
Gripper Control
        ✅
```

The missing Lesson 17 work is the **motion strategy layer**:

```text
Multi-Joint Target
        ↓
How should the target be executed?
        ↓
Synchronized / Coordinated / Sequential / Custom
```

[Back to Table of Contents](#toc)

---

<a id="completion-goals"></a>
## 2. Completion Goals

```text
1. Synchronized Multi-Joint Motion
   ✅ Existing

2. Coordinated Arrival Velocity
   → Add

3. Sequential Multi-Joint Motion
   → Add

4. Forward Order
   joint1 → joint5

5. Reverse Order
   joint5 → joint1

6. Custom Joint Order
   user-defined

7. Named Pose with selectable motion mode

8. HOME with selectable motion mode

9. Keyboard Jog physical test

10. Joint2 dual-motor synchronization test
```

---

<a id="why"></a>
## 3. Why This Change Is Needed

The existing `Robot.move_joints()` already sends Multi-Joint Goal Position values using synchronized bus writes.

That gives an approximately simultaneous command start.

However, all joints currently receive the same logical `velocity_deg_s`.

If two joints travel different angular distances, they do not finish together.

Example:

```text
joint1 movement = 80 deg
joint2 movement = 40 deg
velocity for both = 40 deg/s

joint1 time ≈ 2 s
joint2 time ≈ 1 s
```

We therefore need two separate concepts:

```text
Synchronized Start
and
Coordinated Arrival
```

We also need ordered motion for manually designed safe sequences.

---

<a id="start-vs-arrival"></a>
## 4. Simultaneous Start vs Simultaneous Arrival

### Synchronized Start

```text
joint1 ───────────────►
joint2 ───────►
joint3 ─────────────────────►
```

All commands start together, but completion times differ.

### Coordinated Arrival

```text
joint1 ───────────────►
joint2 ───────────────►
joint3 ───────────────►
                       ↑
                 similar arrival time
```

This requires different velocities for different joints.

---

<a id="motion-modes"></a>
## 5. Motion Modes

The final Lesson 17 motion modes are:

```python
MOTION_MODE_SYNCHRONIZED = "synchronized"

MOTION_MODE_COORDINATED_ARRIVAL = (
    "coordinated_arrival"
)

MOTION_MODE_SEQUENTIAL_FORWARD = (
    "sequential_forward"
)

MOTION_MODE_SEQUENTIAL_REVERSE = (
    "sequential_reverse"
)

MOTION_MODE_CUSTOM = "custom"
```

Meaning:

| Mode | Behavior |
|---|---|
| `synchronized` | All target joints receive goals together with the same requested joint velocity |
| `coordinated_arrival` | All target joints start together, but velocities are scaled for similar arrival time |
| `sequential_forward` | Move selected target joints in robot order |
| `sequential_reverse` | Move selected target joints in reverse robot order |
| `custom` | Move joints one by one using a user-defined order |

---

<a id="oop-design"></a>
## 6. OOP Design

The target pose and the movement strategy are separate responsibilities.

```text
Targets
= WHERE the robot should go

Motion Mode
= HOW the robot should go there
```

Example:

```python
targets = {
    "joint1": 30.0,
    "joint2": 20.0,
    "joint3": -40.0
}
```

The same target can be executed using different strategies:

```python
robot.move_joints(
    targets,
    motion_mode="synchronized"
)
```

or:

```python
robot.move_joints(
    targets,
    motion_mode="sequential_reverse"
)
```

This is an important step toward a future Motion Strategy / Trajectory layer.

---

<a id="robot-api"></a>
## 7. Robot API Changes

The public API becomes:

```python
robot.move_joints(
    targets,
    velocity_deg_s=None,
    motion_mode="synchronized",
    joint_order=None
)
```

Preview becomes:

```python
robot.preview_multi_joint_move(
    targets,
    velocity_deg_s=None,
    motion_mode="synchronized",
    joint_order=None
)
```

Backward compatibility is preserved because:

```python
robot.move_joints(
    targets,
    velocity_deg_s
)
```

still defaults to:

```text
synchronized
```

---

<a id="mode-validation"></a>
## 8. Motion Mode Validation

Add motion-mode constants to `Robot`.

```python
MOTION_MODE_SYNCHRONIZED = (
    "synchronized"
)

MOTION_MODE_COORDINATED_ARRIVAL = (
    "coordinated_arrival"
)

MOTION_MODE_SEQUENTIAL_FORWARD = (
    "sequential_forward"
)

MOTION_MODE_SEQUENTIAL_REVERSE = (
    "sequential_reverse"
)

MOTION_MODE_CUSTOM = (
    "custom"
)

SUPPORTED_MOTION_MODES = {
    MOTION_MODE_SYNCHRONIZED,
    MOTION_MODE_COORDINATED_ARRIVAL,
    MOTION_MODE_SEQUENTIAL_FORWARD,
    MOTION_MODE_SEQUENTIAL_REVERSE,
    MOTION_MODE_CUSTOM,
}
```

Validation pseudocode:

```text
IF motion_mode is not a string:
    reject

IF motion_mode not in supported modes:
    reject
```

---

<a id="order-resolution"></a>
## 9. Motion Order Resolution

### Synchronized / Coordinated

The execution order is informational only because joints are started together.

Use normal robot order for display.

### Forward

```text
robot joint order
filtered to requested targets
```

### Reverse

```text
reverse robot joint order
filtered to requested targets
```

### Custom

The custom order must:

- be a list or tuple,
- contain no duplicates,
- contain only valid robot joints,
- contain exactly the same joints as the target dictionary.

This prevents a target from being silently skipped.

---

<a id="coordinated-arrival"></a>
## 10. Coordinated Arrival Velocity

Let:

```text
Dmax = largest requested angular movement
Vmax = requested maximum velocity
```

The theoretical common time is:

```text
T = Dmax / Vmax
```

For every moving joint:

```text
Vi = Di / T
```

Equivalent:

```text
Vi = Vmax × Di / Dmax
```

Example:

```text
joint1 distance = 80 deg
joint2 distance = 40 deg
Vmax = 40 deg/s

joint1 velocity = 40 deg/s
joint2 velocity = 20 deg/s
```

### Minimum velocity

If the calculated velocity is below the configured minimum joint velocity, clamp it:

```text
Vi = max(MIN_JOINT_VELOCITY, Vi)
```

That means arrival is approximate, not mathematically perfect.

### Important physical limitation

Actual arrival time also depends on:

- load,
- friction,
- motor controller behavior,
- mechanical coupling,
- available torque,
- settling tolerance.

So this feature is **velocity coordination**, not closed-loop trajectory synchronization.

---

<a id="preview"></a>
## 11. Multi-Joint Preview Changes

`preview_multi_joint_move()` should now return:

```python
{
    "targets": ...,
    "velocity_deg_s": ...,
    "motion_mode": ...,
    "execution_order": ...,
    "coordinated_duration_s": ...,
    "joint_plans": ...
}
```

Each `joint_plan` still contains:

```text
current angle
target angle
movement
velocity
current raw
goal raw
profile velocity raw
torque state
```

For `coordinated_arrival`, the per-joint `velocity_deg_s` values are different.

---

<a id="execution"></a>
## 12. Multi-Joint Execution Changes

### Synchronized / Coordinated

The existing Multi-Joint pipeline remains:

```text
Preview all targets
        ↓
Set all Profile Velocities
        ↓
Prepare torque
        ↓
Collect all motor goals
        ↓
SyncWrite Goal Position
        ↓
Wait for all target joints
```

### Sequential

Before moving anything:

```text
Preview and preflight ALL targets
```

Then:

```text
FOR joint in execution_order:
    move_joint(...)
    wait until complete
```

This is important because it prevents:

```text
joint1 moved
joint2 moved
joint3 target invalid
```

All targets must be valid before the first physical movement.

---

<a id="forward"></a>
## 13. Sequential Forward

Example target dictionary:

```python
{
    "joint1": 30,
    "joint3": -20,
    "joint5": -10
}
```

Robot order:

```text
joint1
joint2
joint3
joint4
joint5
```

Resolved order:

```text
joint1
joint3
joint5
```

Only requested joints are executed.

---

<a id="reverse"></a>
## 14. Sequential Reverse

For the same target set:

```text
joint5
joint3
joint1
```

This can be useful when tool-side joints should move before base-side joints.

---

<a id="custom"></a>
## 15. Custom Joint Order

Example:

```python
joint_order = [
    "joint3",
    "joint5",
    "joint1"
]
```

Execution:

```text
joint3
WAIT
joint5
WAIT
joint1
WAIT
```

Custom order is useful for manually designed movement strategies.

It is not a full collision planner.

---

<a id="pose-controller"></a>
## 16. PoseController Integration

`PoseController` should pass the selected motion strategy to `Robot`.

Recommended API:

```python
def preview_pose(
    self,
    pose_name,
    velocity_deg_s=None,
    motion_mode="synchronized",
    joint_order=None
):
    ...
```

```python
def move_pose(
    self,
    pose_name,
    velocity_deg_s=None,
    motion_mode="synchronized",
    joint_order=None
):
    ...
```

```python
def home(
    self,
    velocity_deg_s=None,
    motion_mode="synchronized",
    joint_order=None
):
    ...
```

The PoseLibrary still stores the pose target.

PoseController decides how to execute it.

---

<a id="named-pose"></a>
## 17. Named Pose Motion Mode

Workflow:

```text
Select Pose
        ↓
Select Motion Mode
        ↓
Preview Motion
        ↓
Show order and per-joint velocity
        ↓
Confirm
        ↓
Execute
        ↓
Return to Pose list
```

The pose itself does not need to permanently store the motion mode yet.

The mode can be selected at execution time.

---

<a id="home"></a>
## 18. HOME Motion Mode

HOME should use the same strategy system.

Workflow:

```text
HOME target
    ↓
Select Motion Mode
    ↓
Preview
    ↓
Confirm
    ↓
Execute
```

Examples:

```text
HOME synchronized
HOME coordinated arrival
HOME sequential reverse
```

Use low velocity for first physical HOME tests.

---

<a id="cli"></a>
## 19. CLI / Control Menu Changes

Add a helper:

```text
Select Motion Mode

1. Synchronized
2. Coordinated Arrival
3. Sequential Forward
4. Sequential Reverse
5. Custom Order
0. Back
```

For Custom Order, show only the joints present in the target set.

Example:

```text
Target joints:
joint1, joint3, joint5

Custom order:
joint3, joint5, joint1
```

The CLI should display:

```text
Motion Mode
Execution Order
Current angle
Target angle
Movement
Per-joint velocity
```

Before execution.

---

<a id="gripper"></a>
## 20. Gripper Interaction

Lesson 18 already integrates the Gripper into Motion.

The arm motion strategy applies to arm joints.

If Multi-Joint input also includes a Gripper target:

```text
execute selected arm motion strategy
then
execute Gripper target
```

for now.

This is not a synchronized arm + Gripper trajectory.

True coordinated arm/end-effector timing belongs to the later trajectory layer.

---

<a id="unit-tests"></a>
## 21. Unit Tests

Add tests for:

```text
motion mode validation
forward order resolution
reverse order resolution
custom order resolution
duplicate custom joints
missing custom target joint
unknown custom joint
coordinated velocity scaling
zero-distance coordinated velocity
backward-compatible synchronized default
```

Important pure calculation example:

```text
movement = 40 deg
max movement = 80 deg
requested max velocity = 40 deg/s

expected coordinated velocity = 20 deg/s
```

Unit tests should not automatically perform real hardware movement.

---

<a id="physical-tests"></a>
## 22. Physical Test Plan

Do not begin with large full-arm movements.

Use:

```text
small angle changes
low velocity
clear workspace
no payload
```

Test order:

```text
1. Existing synchronized Multi-Joint
2. Coordinated Arrival
3. Sequential Forward
4. Sequential Reverse
5. Custom Order
6. Named Pose
7. HOME
8. Keyboard Jog
9. Joint2 synchronization
```

---

<a id="keyboard-test"></a>
## 23. Keyboard Jog Test

Use a small Jog Step.

Test:

```text
Q / A → joint1
W / S → joint2
E / D → joint3
R / F → joint4
T / G → joint5
H     → HOME
X     → Exit
```

Lesson 18 may also provide Gripper keys.

Confirm:

- one key press produces the expected direction,
- target remains inside calibrated limits,
- terminal restores correctly on Exit,
- errors do not leave the terminal in a broken mode.

---

<a id="joint2-test"></a>
## 24. Joint2 Dual-Motor Test

`joint2` uses:

```text
Motor 2
Motor 3
```

with opposite encoder directions.

Physical test:

```text
move joint2 by a small safe amount
read both raw positions
convert both to logical joint angle
calculate disagreement
```

Condition:

```text
alignment_error
<= MAX_COUPLED_ANGLE_ERROR_DEG
```

Do not test with large motion first.

If disagreement increases, stop and investigate mechanical or calibration problems.

---

<a id="collision"></a>
## 25. Collision Avoidance Limitations

Sequential ordering can reduce collision risk.

But:

```text
Sequential Motion
≠
Collision Avoidance
```

True collision avoidance requires:

```text
link geometry
forward kinematics
self-collision model
obstacle model
path sampling
collision checking
```

Those belong to later kinematics and planning lessons.

Use ordered motion only as a manually verified strategy.

---

<a id="validation"></a>
## 26. Validation Commands

Syntax:

```bash
python -m compileall -q src scripts tests && \
echo "=== SYNTAX OK ==="
```

Unit tests:

```bash
python -m unittest discover \
    -s tests \
    -p "test_*.py" \
    -v
```

Then:

```bash
./scripts/run_project.sh
```

Do not run physical motion until syntax and unit tests pass.

---

<a id="final-checklist"></a>
## 27. Final Lesson 17 Checklist

```text
[✓] Safe single-joint motion
[✓] Runtime velocity
[✓] Synchronized Multi-Joint
[ ] Coordinated Arrival
[ ] Sequential Forward
[ ] Sequential Reverse
[ ] Custom Order
[ ] Named Pose mode selection
[ ] HOME mode selection
[ ] Keyboard Jog physical validation
[ ] Joint2 dual-motor physical validation
```

After the software changes and physical checks are complete, all items can be marked complete.

---

<a id="updated-roadmap"></a>
## 28. Updated Roadmap

| Phase | Topic | Status |
|---|---|---|
| 1 | Project structure | ✅ |
| 2 | DYNAMIXEL communication | ✅ |
| 3 | Hardware inventory | ✅ |
| 4 | Robot configuration | ✅ |
| 5 | Calibration | ✅ Core |
| 6 | Joint coordinate model | ✅ |
| 7 | RobotBuilder | ✅ |
| 8 | Robot runtime model | ✅ |
| 9 | Safe Joint Motion | ✅ |
| 10 | Velocity Control | ✅ |
| 11 | Coupled Joint2 Control | ✅ Software |
| 12 | Synchronized Multi-Joint | ✅ |
| 13 | Named Pose / HOME | ✅ Basic |
| 14 | Jog | ✅ |
| 15 | Keyboard Teleoperation | ✅ Software |
| 16 | Joystick Adapter | 🟡 Hardware pending |
| **17A** | **Coordinated Arrival** | **Current work** |
| **17B** | **Sequential Motion Modes** | **Current work** |
| **17C** | **Pose/HOME Motion Modes** | **Current work** |
| **17D** | **Physical completion tests** | **Current work** |
| 18 | Gripper Control | ✅ Core |
| 19 | Coordinated Trajectory / Stages | ⬜ |
| 20 | Forward Kinematics | ⬜ |
| 21 | Inverse Kinematics | ⬜ |
| 22 | Cartesian Control | ⬜ |
| 23 | Trajectory Planning | ⬜ |
| 24 | Feedback Tracking | ⬜ |
| 25 | Advanced Safety | ⬜ |
| 26 | ROS 2 | ⬜ |
| 27 | Simulation | ⬜ |
| 28 | Pick and Place | ⬜ |

---

<a id="next"></a>
## 29. What Comes Next

Lesson 17 defines:

```text
HOW final joint targets are executed
```

Lesson 19 will define:

```text
HOW the robot moves through time between configurations
```

That includes:

```text
waypoints
stages
interpolation
acceleration
trajectory state
cancel/pause
feedback
```

Then kinematics can be added:

```text
Forward Kinematics
→ Inverse Kinematics
→ Cartesian Control
→ Collision-Aware Planning
```

---

## End of Lesson 17 Completion Document

The final Lesson 17 architecture is:

```text
Joint Targets
      ↓
Motion Strategy
 ├── Synchronized
 ├── Coordinated Arrival
 ├── Sequential Forward
 ├── Sequential Reverse
 └── Custom Order
      ↓
Robot
      ↓
Joint
      ↓
DynamixelMotor
      ↓
Hardware
```

This creates the clean bridge between basic joint-space commands and the future trajectory-planning layer.
