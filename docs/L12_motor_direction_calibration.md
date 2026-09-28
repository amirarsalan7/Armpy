# Lesson 12 - Semi-Automatic Motor Direction Calibration

## Goal

The goal of this lesson is to determine the encoder direction of each
motor relative to the positive direction of its Joint.

The robot does not move automatically.

The user manually moves one Joint a small distance.

The software compares motor positions before and after the movement.


# Previous State

After Lesson 11:

Physical Robot
      |
      v
HOME Calibration
      |
      v
joint_calibration.json


The software already knows:

- Motor IDs
- Motor-to-Joint mapping
- HOME position of every motor


It does not yet know the motor direction relative to Joint motion.


# Direction Calibration

The basic idea is:

BEFORE position
       |
       v
Move Joint in positive direction
       |
       v
AFTER position
       |
       v
delta = AFTER - BEFORE
       |
       +---- delta > 0 ----> direction = +1
       |
       +---- delta < 0 ----> direction = -1


# Example

Joint 2 uses two motors.

Before:

Motor 2 = 2040
Motor 3 = 2060


After positive Joint movement:

Motor 2 = 2140
Motor 3 = 1958


Delta:

Motor 2 = +100
Motor 3 = -102


Result:

Motor 2 direction = +1
Motor 3 direction = -1


This confirms that the two Shoulder motors move in opposite encoder
directions.


# OOP Concept - Method Contract

A Method can have:

Preconditions
      |
      v
Operation
      |
      v
Postconditions


For direction calibration:

Preconditions:

- HOME calibration exists
- Joint exists
- Motor objects exist
- Target motor torque is OFF
- The user knows the intended positive Joint direction


Operation:

Read BEFORE

↓

Manual positive movement

↓

Read AFTER

↓

Calculate delta


Postcondition:

motor_directions exists

and:

direction_calibrated = true


# OOP Concept - State Transition

Calibration progresses through states.

Before Lesson 11:

NO HOME


After Lesson 11:

HOME_CALIBRATED


After Lesson 12:

HOME_CALIBRATED
       |
       v
DIRECTION_CALIBRATED


The calibration object changes state during the calibration process.


# Torque Safety Check

Manual movement requires target motor torque to be OFF.

The software checks Torque Enable before asking the user to move a Joint.

Torque ON:

Calibration blocked


Torque OFF:

Manual calibration allowed


The program does not automatically disable torque.


# Reading Joint Positions

Single motor Joint:

Joint 1
   |
   v
Motor 1 position


Dual motor Joint:

Joint 2
   |
   +---- Motor 2 position
   |
   +---- Motor 3 position


The result is stored as a dictionary.


# Encoder Wraparound

DYNAMIXEL position values can cross the encoder boundary.

Example:

BEFORE = 4090

AFTER = 10


Simple subtraction gives:

10 - 4090 = -4080


But the real small movement is approximately:

+16 counts


The calibration code corrects this wraparound before determining
direction.


# Movement Threshold

Very small changes can be caused by encoder noise.

The lesson uses a small movement threshold.

Example:

MIN_MOVEMENT_COUNTS = 20


If movement is smaller than the threshold:

Direction is not accepted.


# Persistent Calibration

The result is stored in:

config/joint_calibration.json


Example:

motor_directions:

Motor 2 -> +1

Motor 3 -> -1


The measurement that produced this result is also stored:

BEFORE
AFTER
DELTA


This makes the calibration result easier to inspect later.


# Architecture

Physical Robot
      |
      v
BEFORE Positions
      |
      v
Manual Positive Movement
      |
      v
AFTER Positions
      |
      v
Delta Calculation
      |
      v
Motor Direction
      |
      v
JointCalibration
      |
      v
joint_calibration.json


# Current Calibration State

Hardware Discovery          [DONE]

Motor Mapping               [DONE]

HOME Calibration            [DONE]

Direction Calibration       [DONE]

Mechanical Limits           [NEXT]

Gripper Open / Close        [TODO]

Calibration Verification    [TODO]


# Safety

This lesson does not send:

Goal Position      [NO]

Automatic Motion   [NO]

Torque Disable     [NO]

Torque Enable      [NO]


The program only reads motor state and position.

Heavy robot links must be mechanically supported during manual
calibration.


# Result

After this lesson the system knows:

- The real HOME position of every motor
- The encoder direction of each motor
- Opposite motor directions for the dual-motor Shoulder Joint


# Next Lesson

Lesson 13 - Semi-Automatic Mechanical Joint Limit Calibration

The next goal is to measure safe minimum and maximum positions for
each mechanical Joint.