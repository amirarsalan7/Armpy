# ARMPy

ARMPy is an educational robotics project for learning Python, Object-Oriented Programming (OOP), and real robot control using a 6R robotic arm.

## Robot

The robot currently consists of:

* 6 revolute joints
* 7 DYNAMIXEL actuators
* ROBOTIS CM-550 controller
* External 12 V power supply
* USB connection between the CM-550 and the development computer

## Project Goals

The project is being developed step by step to study:

* Python programming
* Object-Oriented Programming
* Robot software architecture
* DYNAMIXEL communication
* Joint and motor control
* Robot safety and joint limits
* Hardware abstraction
* Robot state management

## Current Software Structure

```text
ARMPy/
|
|-- main.py
|-- joint.py
|-- robot.py
|-- dynamixel_connection.py
|-- requirements.txt
|-- docs/
|-- README.md
|-- LICENSE
|-- .gitignore
```

## Python Environment

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

## Current Development Stage

The current development stage focuses on establishing safe communication between Python, the CM-550 controller, and the connected DYNAMIXEL actuators before enabling motor motion.

## Safety

Motor torque and goal-position commands should only be enabled after communication, IDs, joint limits, and robot configuration have been verified.
