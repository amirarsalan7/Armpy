Lesson 7 — Motor Configuration and Safety
OOP Review

A Class defines the structure and behavior of Objects.

An Object contains state and behavior.

Instance Variables belong to individual Objects:

self.motor_id
self.connection
self.model_number

Class Variables contain information shared by Objects:

ADDR_TORQUE_ENABLE = 64
ADDR_GOAL_POSITION = 116

Methods represent Object behavior:

motor.read_temperature()
motor.read_configuration()

Composition allows one Object to use another Object.

A DynamixelMotor uses a shared DynamixelConnection.

Dependency Injection provides the Connection Object to the Motor through its constructor.

Encapsulation keeps hardware implementation details inside the Motor and Connection Classes.

Abstraction separates the software into layers.

Current Architecture
main.py
   |
   v
DynamixelMotor
   |
   v
DynamixelConnection
   |
   v
DYNAMIXEL SDK
   |
   v
CM-550
   |
   v
Physical Motor
XL430-W250 Configuration Addresses
Drive Mode          10
Operating Mode      11

Max Position Limit  48
Min Position Limit  52

Torque Enable       64

Goal Position       116
Present Position    132
Operating Modes

Important XL430-W250 operating modes:

1  = Velocity Control Mode
3  = Position Control Mode
4  = Extended Position Control Mode
16 = PWM Control Mode

Position Control Mode is normally appropriate for articulated robot joints that operate within one motor revolution.

Torque Enable
0 = Torque OFF
1 = Torque ON

Torque ON activates motor output and locks the EEPROM configuration area.

Operating Mode and Position Limits are EEPROM values and therefore should only be changed with Torque OFF.

For a robotic arm, disabling torque may allow gravity to move the mechanism. The robot should be mechanically supported before Torque is disabled.

Position Limits

Position Control Mode uses:

Min Position Limit
        <=
Goal Position
        <=
Max Position Limit

The XL430-W250 single-turn position range is:

0 ... 4095

These motor limits are not necessarily the safe mechanical limits of the robot joint.

Goal Position

Goal Position represents the desired actuator output position.

For Position Control Mode, Goal Position must remain between the configured Min and Max Position Limits.

Writing Goal Position while the motor is enabled can cause physical movement.

Therefore, Goal Position should only be written after validation.

Object Invariant

An Object Invariant is a condition that the Object protects from being violated.

The DynamixelMotor Object protects rules such as:

Valid Operating Mode
Valid Position Limits
Goal inside Min/Max limits
EEPROM configuration only with Torque OFF
Explicit Torque state before motion

The Motor Object should reject invalid commands rather than allowing unsafe raw register writes from main.py.

Private Helper Convention

Python methods beginning with _ are conventionally considered internal implementation methods.

Example:

def _require_torque_off(self):
    ...

This means the method is designed for use by other methods inside the Class.

Motor Position vs Joint Position

Motor Position describes the actuator output shaft.

Joint Position describes the robot's mechanical joint.

They may differ because of:

Zero offset
Direction
Mechanical transmission
External gear ratio
Joint limits

A conceptual conversion is:

joint_angle
=
direction
*
(motor_angle - zero_offset)
/
gear_ratio

Therefore DynamixelMotor should represent motor coordinates, while the future Joint Class will represent robot joint coordinates.

Safety Algorithm

Before motion:

Read Operating Mode
        ↓
Read Position Limits
        ↓
Validate Goal Position
        ↓
Check Drive Mode
        ↓
Explicitly enable Torque
        ↓
Write Goal Position

Before changing EEPROM configuration:

Mechanically support robot
        ↓
Torque OFF
        ↓
Write configuration
        ↓
Read configuration back
        ↓
Verify values
Current Project Stage
Connection        DONE
Discovery         DONE
Motor Object      DONE
Motor Monitoring  DONE
Motor Safety      CURRENT
Joint Model       NEXT
Robot Model       LATER
Control           LATER

No deliberate motor motion is required to complete Lesson 7.