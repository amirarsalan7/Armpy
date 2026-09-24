# Lesson 9
# Joint Mapping and Calibration


## Goal

Move robot information from Python code into configuration files.


## Why Configuration?

Hardware mapping changes.

Motor IDs, limits and calibration values should not be hard coded.

Bad:

joint.motor_id = 2


Better:

robot_joints.json
        |
        v
RobotConfig
        |
        v
Joint Object


---

# Robot Mapping


Current robot:


Joint 1:
Motor 1


Joint 2:
Motor 2 + Motor 3


Joint 3:
Motor 4


Joint 4:
Motor 5


Joint 5:
Motor 6


Gripper:
Motor 7


---

# OOP Concepts


## Separation of Data and Logic


Classes contain behavior.

Configuration files contain data.


## Object Creation From Configuration


Objects can be created using external configuration.


Flow:


JSON

↓

RobotConfig

↓

Joint Objects

↓

Robot Object



## RobotConfig Responsibility


RobotConfig only manages:

- Loading JSON
- Providing joint configuration
- Providing gripper configuration


It does not:

- Control motors
- Move robot
- Create hardware communication


---

# Current Architecture


DynamixelConnection

        |

        v

DynamixelMotor

        |

        v

Joint

        |

        v

RobotConfig

        |

        v

JSON Configuration


---

# Calibration Data


Future calibration parameters:


- Home position
- Zero offset
- Direction
- Gear ratio
- Mechanical limits


These values belong in configuration files, not Python code.