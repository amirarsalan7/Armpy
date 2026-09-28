# Lesson 11 — Semi-Automatic Joint Home Calibration

## Goal

The goal of this lesson is to measure the real HOME encoder position of every robot actuator.

The program does not move the robot.

The user places the robot in a HOME pose, then the software reads and stores the current motor positions.

---

# Previous System

Before this lesson:

```text
Physical Robot
      ↓
Hardware Discovery
      ↓
hardware_inventory.json
```

The software already knows:

- Motor IDs
- Motor model
- Firmware
- Controller information
- Motor configuration

It also has manual robot mapping:

```text
Joint 1 → Motor 1

Joint 2 → Motor 2 + Motor 3

Joint 3 → Motor 4

Joint 4 → Motor 5

Joint 5 → Motor 6

Gripper → Motor 7
```

---

# What This Lesson Adds

```text
Known Joint Mapping
        ↓
Validate Hardware
        ↓
Read Real Encoder Positions
        ↓
Capture HOME
        ↓
joint_calibration.json
```

The HOME position is measured from the real robot.

It is not assumed to be exactly `2048`.

---

# OOP Concept — Stateful Service Object

`JointCalibration` is a Service Object.

Its job is to perform calibration operations.

Before HOME capture:

```text
JointCalibration
└── calibration = None
```

After HOME capture:

```text
JointCalibration
└── calibration = measured data
```

The object changes state during its lifetime.

---

# Dependency Injection

`JointCalibration` receives:

```text
Connection
HardwareInventory
RobotConfig
```

from outside.

```text
HardwareInventory ───┐
                     │
RobotConfig ─────────┼──→ JointCalibration
                     │
Connection ──────────┘
```

It does not create a second hardware connection.

---

# Object Invariant

When a `JointCalibration` object is created:

```text
Validate mapping
      ↓
Build motor objects
      ↓
Object is ready
```

If a configured motor does not exist in the Hardware Inventory, object creation stops with an error.

---

# Main Methods

## `_validate_mapping()`

Checks:

```text
robot_joints.json
        ↓
motor IDs
        ↓
hardware_inventory.json
```

Every configured motor must exist.

---

## `_build_motor_objects()`

Uses stored hardware identity:

```text
Motor ID
Model Number
Firmware
```

to recreate live `DynamixelMotor` objects.

---

## `_read_motor_position_raw()`

```text
Motor ID
   ↓
DynamixelMotor
   ↓
read_status()
   ↓
position_raw
```

Returns the current raw encoder position.

---

## `capture_home()`

For each Joint:

```text
Joint
  ↓
Motor IDs
  ↓
Read current positions
  ↓
Save home_raw
```

For Joint 2:

```text
Joint 2
├── Motor 2 HOME
└── Motor 3 HOME
```

Each Motor has its own HOME value.

---

## `save()`

```text
Calibration Dictionary
        ↓
JSON Serialization
        ↓
joint_calibration.json
```

---

# Data Flow

```text
┌─────────────────────────┐
│ hardware_inventory.json │
└────────────┬────────────┘
             ↓
      HardwareInventory

┌─────────────────────┐
│ robot_joints.json   │
└──────────┬──────────┘
           ↓
      RobotConfig

Physical Robot
      ↓
DynamixelConnection

           ↓
┌─────────────────────┐
│ JointCalibration    │
└──────────┬──────────┘
           ↓
┌─────────────────────────┐
│ joint_calibration.json  │
└─────────────────────────┘
```

---

# Calibration Status After Lesson 11

```text
Hardware Discovery       ✅
Motor Mapping            ✅
HOME position            ✅

Motor direction          ⬜
Mechanical limits        ⬜
Gripper open / close     ⬜
Calibration verification ⬜
```

---

# Safety

This lesson does not send:

```text
Goal Position      ❌
Torque Enable      ❌
Torque Disable     ❌
Automatic Motion   ❌
```

It only reads:

```text
Present Position   ✅
```

Do not manually force a motor while Torque is enabled.

Support heavy robot links before manually changing the robot pose.

---

# Result

After this lesson the software can:

- Validate the known Motor-to-Joint mapping.
- Recreate Motor objects from Hardware Inventory.
- Read current encoder positions.
- Capture the real HOME pose.
- Store one HOME position for each actuator.
- Support the dual-motor Shoulder Joint.
- Save calibration data for future robot software.

---

# Next Lesson

## Lesson 12 — Semi-Automatic Motor Direction Calibration

The system will:

```text
Read positions BEFORE
        ↓
Move one Joint manually in known positive direction
        ↓
Read positions AFTER
        ↓
Calculate delta
        ↓
Determine motor directions
        ↓
Save calibration
```

This is especially important for Joint 2:

```text
Motor 2  → one direction
Motor 3  → opposite direction
```