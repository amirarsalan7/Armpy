import sys
import termios

class RobotControlMenu:

    def __init__(
        self,
        robot,
        pose_controller,
        jog_controller,
        keyboard_controller,
        joystick_controller
    ):

        self.robot = robot

        self.pose_controller = pose_controller
        self.jog_controller = jog_controller
        self.keyboard_controller = keyboard_controller
        self.joystick_controller = joystick_controller

        self.default_velocity_deg_s = (
            robot.default_joint_velocity_deg_s
        )
        
    def show(self):

        while True:

            print(
                "\n========================"
            )

            print(
                "ARMPy Control"
            )

            print(
                "========================"
            )

            print(
                f"Robot: {self.robot.name}"
            )

            print(
                f"Velocity: "
                f"{self.default_velocity_deg_s:.2f} deg/s"
            )

            print(
                f"Jog Step: "
                f"{self.jog_controller.step_deg:.2f} deg"
            )

            print(
                "------------------------"
            )

            print(
                "1. Robot Status"
            )

            print(
                "2. Motion"
            )

            print(
                "3. Pose Manager"
            )

            print(
                "4. Jog / Teleoperation"
            )

            print(
                "5. Settings"
            )

            print(
                "6. Gripper Control"
            )

            print(
                "0. Exit"
            )

            choice = input(
                "\nSelect option: "
            ).strip()

            try:

                if choice == "1":
                    self.show_robot_state()

                elif choice == "2":
                    self.motion_menu()

                elif choice == "3":
                    self.pose_menu()

                elif choice == "4":
                    self.jog_menu()

                elif choice == "5":
                    self.settings_menu()

                elif choice == "6":
                    self.gripper_menu()

                elif choice == "0":

                    print(
                        "Exiting control menu. "
                        "Motor torque states are unchanged."
                    )

                    return

                else:
                    print(
                        "Invalid option."
                    )

            except (
                RuntimeError,
                ValueError,
                TimeoutError
            ) as error:

                print(
                    f"\nControl error: {error}"
                )

    def motion_menu(self):

        while True:

            print(
                "\n--- Motion ---"
            )

            print(
                "1. Move One Joint / Gripper"
            )

            print(
                "2. Move Multiple Joints"
            )

            print(
                "3. Move HOME"
            )

            print(
                "4. Hold Joint Position"
            )

            print(
                "5. Show Joint / Gripper Limits"
            )

            print(
                "6. Gripper Control"
            )

            print(
                "7. Save Current Position"
            )

            print(
                "0. Back"
            )

            choice = input(
                "Select: "
            ).strip()

            try:

                if choice == "1":

                    self.move_one_joint()

                elif choice == "2":

                    self.move_multiple_joints()

                elif choice == "3":

                    self.move_home()

                elif choice == "4":

                    self.hold_joint()

                elif choice == "5":

                    self.show_joint_limits()

                elif choice == "6":

                    self.gripper_menu()

                elif choice == "7":

                    self.save_current_pose()

                elif choice == "0":

                    return

                else:

                    print(
                        "Invalid option."
                    )

            except (
                RuntimeError,
                ValueError,
                TimeoutError
            ) as error:

                print(
                    f"\nMotion error: {error}"
                )

    def pose_menu(self):

        while True:

            print(
                "\n--- Pose Manager ---"
            )

            print(
                "1. Move to Pose"
            )

            print(
                "2. Save Current Position"
            )

            print(
                "3. Edit Pose"
            )

            print(
                "4. Rename Pose"
            )

            print(
                "5. Delete Pose"
            )

            print(
                "6. Show Pose Values"
            )

            print(
                "0. Back"
            )

            choice = input(
                "Select: "
            ).strip()

            if choice == "1":
                self.move_named_pose()

            elif choice == "2":
                self.save_current_pose()

            elif choice == "3":
                self.edit_pose()

            elif choice == "4":
                self.rename_pose()

            elif choice == "5":
                self.delete_pose()

            elif choice == "6":
                self.show_pose_values()

            elif choice == "0":
                return

            else:
                print(
                    "Invalid option."
                )

    def jog_menu(self):

        while True:

            print(
                "\n--- Jog / Teleoperation ---"
            )

            print(
                "1. Jog One Joint"
            )

            print(
                "2. Keyboard Jog"
            )

            print(
                "3. Joystick Jog"
            )

            print(
                "4. Gripper Jog"
            )

            print(
                "0. Back"
            )

            choice = input(
                "Select: "
            ).strip()

            if choice == "1":
                self.jog_joint()

            elif choice == "2":
                self.keyboard_controller.run()

            elif choice == "3":
                self.joystick_controller.run()

            elif choice == "4":
                self.jog_gripper()

            elif choice == "0":
                return

            else:
                print(
                    "Invalid option."
                )

    def settings_menu(self):

        while True:

            print(
                "\n--- Settings ---"
            )

            print(
                f"Velocity: "
                f"{self.default_velocity_deg_s:.2f} deg/s"
            )

            print(
                f"Jog Step: "
                f"{self.jog_controller.step_deg:.2f} deg"
            )

            print()

            print(
                "1. Set Default Velocity"
            )

            print(
                "2. Set Jog Step"
            )

            print(
                "0. Back"
            )

            choice = input(
                "Select: "
            ).strip()

            if choice == "1":
                self.set_default_velocity()

            elif choice == "2":
                self.set_jog_step()

            elif choice == "0":
                return

            else:
                print(
                    "Invalid option."
                )

    def gripper_menu(self):

        while True:

            print(
                "\n--- Gripper Control ---"
            )

            print(
                "1. Read Gripper State"
            )

            print(
                "2. Open Gripper"
            )

            print(
                "3. Close Gripper"
            )

            print(
                "4. Set Opening Percentage"
            )

            print(
                "5. Hold Gripper"
            )

            print(
                "6. Set Gripper Velocity"
            )

            print(
                "0. Back"
            )

            choice = input(
                "Select: "
            ).strip()

            if choice == "1":
                self.show_gripper_state()

            elif choice == "2":
                self.open_gripper()

            elif choice == "3":
                self.close_gripper()

            elif choice == "4":
                self.set_gripper_opening()

            elif choice == "5":
                self.hold_gripper()

            elif choice == "6":
                self.set_gripper_velocity()

            elif choice == "0":
                return

            else:

                print(
                    "Invalid option."
                )

    def _choose_joint(self):

        joint_keys = self.robot.get_joint_names()

        print("\nSelect Joint:")

        for index, joint_key in enumerate(
            joint_keys,
            start=1
        ):

            joint = self.robot.get_joint(
                joint_key
            )

            suffix = ""

            if len(joint.motors) > 1:
                suffix = " [synchronized]"

            print(
                f"{index}. {joint_key} - "
                f"{joint.name}{suffix}"
            )

        print("0. Back")

        choice = input("Select: ").strip()

        if choice == "0":
            return None

        try:
            index = int(choice) - 1
            return joint_keys[index]

        except (ValueError, IndexError):
            raise ValueError(
                "Invalid joint selection."
            )

    def _choose_joint_or_gripper(self):

        joint_keys = (
            self.robot
            .get_joint_names()
        )

        print(
            "\nSelect Motion Target:"
        )

        for index, joint_key in enumerate(
            joint_keys,
            start=1
        ):

            joint = (
                self.robot
                .get_joint(
                    joint_key
                )
            )

            suffix = ""

            if len(joint.motors) > 1:

                suffix = (
                    " [synchronized]"
                )

            print(
                f"{index}. "
                f"{joint_key} - "
                f"{joint.name}"
                f"{suffix}"
            )

        gripper_index = (
            len(joint_keys)
            + 1
        )

        print(
            f"{gripper_index}. "
            "gripper - end effector"
        )

        print(
            "0. Back"
        )

        choice = input(
            "Select: "
        ).strip()

        if choice == "0":

            return None, None

        try:

            selected_index = int(
                choice
            )

        except ValueError:

            raise ValueError(
                "Invalid motion target selection."
            )

        if (
            selected_index
            == gripper_index
        ):

            return (
                "gripper",
                "gripper"
            )

        joint_index = (
            selected_index
            - 1
        )

        if not (
            0
            <= joint_index
            < len(joint_keys)
        ):

            raise ValueError(
                "Invalid motion target selection."
            )

        return (
            "joint",
            joint_keys[
                joint_index
            ]
        )

    def _choose_pose(
        self,
        allow_home=True
    ):

        names = (
            self.pose_controller
            .get_pose_names()
        )

        if not allow_home:

            names = [
                name
                for name in names
                if name != "home"
            ]

        if not names:

            print(
                "No poses are available."
            )
            return None

        print(
            "\nSelect Pose:"
        )

        for index, name in enumerate(
            names,
            start=1
        ):

            print(
                f"{index}. {name}"
            )

        print(
            "0. Back"
        )

        choice = input(
            "Select: "
        ).strip()

        if choice == "0":
            return None

        try:

            index = int(choice) - 1

            return names[
                index
            ]

        except (
            ValueError,
            IndexError
        ):

            raise ValueError(
                "Invalid pose selection."
            )

    def _confirm(
        self,
        message
    ):

        while True:

            answer = input(
                f"{message} "
                "[Enter=yes / n=no]: "
            ).strip().lower()

            if answer in (
                "",
                "y",
                "yes"
            ):

                return True

            if answer in (
                "n",
                "no"
            ):

                return False

            print(
                "Invalid confirmation. "
                "Press Enter for Yes "
                "or type n for No."
            )

    def show_robot_state(self):

        state = self.robot.read_state()

        print(
            f"\nRobot: {state['robot_name']}"
        )

        for joint_key, joint_state in state["joints"].items():

            print(
                f"{joint_key}: "
                f"{joint_state['angle_deg']:.2f} deg "
                f"{joint_state['raw_positions']}"
            )

        print(
            "Gripper raw:",
            state["gripper"]["raw_position"]
        )

    def show_gripper_state(self):

        state = (
            self.robot
            .read_gripper_state()
        )

        print(
            "\nGripper State"
        )

        print(
            f"Motor ID: "
            f"{state['motor_id']}"
        )

        print(
            f"Raw Position: "
            f"{state['raw_position']}"
        )

        print(
            f"Torque: "
            f"{state['torque_enabled']}"
        )

        print(
            f"Calibrated: "
            f"{state['motion_calibrated']}"
        )

        if (
            state[
                "opening_percent"
            ]
            is not None
        ):

            print(
                f"Opening: "
                f"{state['opening_percent']:.1f}%"
            )

            print(
                f"Open Raw: "
                f"{state['open_raw']}"
            )

            print(
                f"Closed Raw: "
                f"{state['closed_raw']}"
            )

        else:

            print(
                "Opening: unavailable "
                "(gripper is not calibrated)"
            )

        print(
            f"Velocity: "
            f"{state['velocity_rpm']:.2f} RPM"
        )

    def open_gripper(self):

        if not self._confirm(
            "Open Gripper?"
        ):

            print(
                "Open Gripper cancelled."
            )

            return

        result = (
            self.robot
            .open_gripper()
        )

        print(
            "Gripper opened."
        )

        print(
            f"Final raw: "
            f"{result['final_raw']}"
        )

    def close_gripper(self):

        if not self._confirm(
            "Close Gripper?"
        ):

            print(
                "Close Gripper cancelled."
            )

            return

        result = (
            self.robot
            .close_gripper()
        )

        print(
            "Gripper closed."
        )

        print(
            f"Final raw: "
            f"{result['final_raw']}"
        )

    def set_gripper_opening(self):

        current_state = (
            self.robot
            .read_gripper_state()
        )

        if (
            current_state[
                "opening_percent"
            ]
            is not None
        ):

            print(
                f"\nCurrent opening: "
                f"{current_state['opening_percent']:.1f}%"
            )

        opening_percent = float(
            input(
                "Target opening [0-100 %]: "
            )
        )

        goal_raw = (
            self.robot
            .gripper
            .calculate_goal_raw(
                opening_percent
            )
        )

        print(
            f"Goal raw: {goal_raw}"
        )

        if not self._confirm(
            "Execute Gripper motion?"
        ):

            print(
                "Gripper motion cancelled."
            )

            return

        result = (
            self.robot
            .set_gripper_opening(
                opening_percent
            )
        )

        print(
            f"Gripper opening set to "
            f"{opening_percent:.1f}%."
        )

        print(
            f"Final raw: "
            f"{result['final_raw']}"
        )

    def hold_gripper(self):

        raw_position = (
            self.robot
            .hold_gripper()
        )

        print(
            f"Gripper holding at "
            f"raw {raw_position}."
        )

    def set_gripper_velocity(self):

        current = (
            self.robot
            .gripper
            .default_velocity_rpm
        )

        print(
            f"\nCurrent Gripper velocity: "
            f"{current:.2f} RPM"
        )

        velocity_rpm = float(
            input(
                "New Gripper velocity [RPM]: "
            )
        )

        updated = (
            self.robot
            .set_default_gripper_velocity(
                velocity_rpm
            )
        )

        print(
            f"Gripper velocity set to "
            f"{updated:.2f} RPM."
        )

    def show_joint_limits(self):

        print(
            "\n--- Joint / Gripper Limits ---"
        )

        for joint_key in (
            self.robot
            .get_joint_names()
        ):

            joint = (
                self.robot
                .get_joint(
                    joint_key
                )
            )

            print(
                f"{joint_key}: "
                f"{joint.min_angle_deg:.2f} "
                f"to "
                f"{joint.max_angle_deg:.2f} deg"
            )

        print(
            "\nGripper:"
        )

        state = (
            self.robot
            .read_gripper_state()
        )

        if not state[
            "motion_calibrated"
        ]:

            print(
                "gripper: NOT CALIBRATED"
            )

            print(
                "Opening limits unavailable."
            )

            return

        print(
            "gripper: "
            "0.00 to 100.00 %"
        )

        print(
            "  0.00%   = Fully Closed"
        )

        print(
            "  100.00% = Fully Open"
        )

        print(
            f"  Closed raw: "
            f"{state['closed_raw']}"
        )

        print(
            f"  Open raw:   "
            f"{state['open_raw']}"
        )

    def move_one_joint(self):

        while True:

            target_type, target_key = (
                self._choose_joint_or_gripper()
            )

            if target_type is None:

                return

            try:

                if target_type == "gripper":

                    self._move_gripper_as_single_target()

                    continue

                joint_key = target_key

                joint = (
                    self.robot
                    .get_joint(
                        joint_key
                    )
                )

                current_angle = (
                    self.robot
                    .read_joint_angle(
                        joint_key
                    )
                )

                print(
                    f"\nCurrent angle: "
                    f"{current_angle:.2f} deg"
                )

                print(
                    f"Safe limits: "
                    f"{joint.min_angle_deg:.2f} "
                    f"to "
                    f"{joint.max_angle_deg:.2f} deg"
                )

                target_angle = float(
                    input(
                        "Target angle [deg]: "
                    )
                )

                velocity_text = input(
                    f"Velocity [deg/s] "
                    f"[Enter = "
                    f"{self.default_velocity_deg_s:.2f}]: "
                ).strip()

                if velocity_text:

                    velocity_deg_s = float(
                        velocity_text
                    )

                else:

                    velocity_deg_s = (
                        self.default_velocity_deg_s
                    )

                plan = (
                    self.robot
                    .preview_joint_move(
                        joint_key,
                        target_angle,
                        velocity_deg_s
                    )
                )

                print(
                    "\nMotion Plan"
                )

                print(
                    f"Target: {joint_key}"
                )

                print(
                    f"Current: "
                    f"{plan['current_angle_deg']:.2f} deg"
                )

                print(
                    f"Target: "
                    f"{plan['target_angle_deg']:.2f} deg"
                )

                print(
                    f"Move: "
                    f"{plan['movement_deg']:.2f} deg"
                )

                print(
                    f"Velocity: "
                    f"{plan['velocity_deg_s']:.2f} deg/s"
                )

                print(
                    f"Raw current: "
                    f"{plan['current_raw']}"
                )

                print(
                    f"Raw goals: "
                    f"{plan['goal_raw']}"
                )

                if not self._confirm(
                    "Execute this motion?"
                ):

                    print(
                        "Motion cancelled."
                    )

                    continue

                result = (
                    self.robot
                    .move_joint(
                        joint_key,
                        target_angle,
                        velocity_deg_s
                    )
                )

                print(
                    f"{joint_key} reached target."
                )

                print(
                    f"Final raw: "
                    f"{result['final_raw']}"
                )

            except (
                RuntimeError,
                ValueError,
                TimeoutError
            ) as error:

                print(
                    f"\nMotion error: {error}"
                )

            finally:

                self._flush_pending_input()

    def move_multiple_joints(self):

        while True:

            command = input(
                "\nPress Enter for a new "
                "Multi-Joint motion, "
                "or B to go back: "
            ).strip().lower()

            if command == "b":
                return

            targets = {}

            print(
                "\nEnter target angle "
                "or press Enter to skip."
            )

            for joint_key in (
                self.robot
                .get_joint_names()
            ):

                current = (
                    self.robot
                    .read_joint_angle(
                        joint_key
                    )
                )

                value = input(
                    f"{joint_key} "
                    f"[current "
                    f"{current:.2f} deg]: "
                ).strip()

                if not value:
                    continue

                targets[
                    joint_key
                ] = float(
                    value
                )

            gripper_text = input(
                "Gripper opening "
                "[0-100 %, Enter = skip]: "
            ).strip()

            gripper_target = None

            if gripper_text:

                gripper_target = float(
                    gripper_text
                )

                self.robot.gripper.calculate_goal_raw(
                    gripper_target
                )

            if (
                not targets
                and gripper_target is None
            ):

                print(
                    "No targets selected."
                )

                continue

            if targets:

                preview = (
                    self.robot
                    .preview_multi_joint_move(
                        targets,
                        self.default_velocity_deg_s
                    )
                )

                print(
                    "\nMulti-Joint Motion Plan"
                )

                for (
                    joint_key,
                    plan
                ) in (
                    preview[
                        "joint_plans"
                    ].items()
                ):

                    print(
                        f"{joint_key}: "
                        f"{plan['current_angle_deg']:.2f} "
                        f"→ "
                        f"{plan['target_angle_deg']:.2f} deg"
                    )

            if gripper_target is not None:

                print(
                    f"Gripper → "
                    f"{gripper_target:.1f}%"
                )

            if not self._confirm(
                "Execute this multi-joint motion?"
            ):

                print(
                    "Multi-joint motion cancelled."
                )

                continue

            try:

                if targets:

                    self.robot.move_joints(
                        targets,
                        self.default_velocity_deg_s
                    )

                if gripper_target is not None:

                    self.robot.set_gripper_opening(
                        gripper_target
                    )

                print(
                    "Motion completed."
                )

            finally:

                self._flush_pending_input()

    def move_named_pose(self):

        while True:

            pose_name = (
                self._choose_pose(
                    allow_home=True
                )
            )

            if pose_name is None:
                return

            print(
                f"\nSelected pose: "
                f"{pose_name}"
            )

            print(
                f"Velocity: "
                f"{self.default_velocity_deg_s:.2f} deg/s"
            )

            if not self._confirm(
                f"Execute pose '{pose_name}'?"
            ):

                print(
                    "Pose motion cancelled."
                )

                continue

            try:

                self.pose_controller.move_pose(
                    pose_name,
                    self.default_velocity_deg_s
                )

                print(
                    f"Pose '{pose_name}' completed."
                )

            except (
                RuntimeError,
                ValueError,
                TimeoutError
            ) as error:

                print(
                    f"\nPose error: {error}"
                )

            finally:

                self._flush_pending_input()

    def _move_gripper_as_single_target(
        self
    ):

        state = (
            self.robot
            .read_gripper_state()
        )

        if not state[
            "motion_calibrated"
        ]:

            raise RuntimeError(
                "Gripper is not calibrated. "
                "Calibrate open and closed "
                "positions first."
            )

        current_percent = (
            state[
                "opening_percent"
            ]
        )

        print(
            "\nGripper Motion"
        )

        print(
            f"Current opening: "
            f"{current_percent:.2f}%"
        )

        print(
            "Safe limits: "
            "0.00% to 100.00%"
        )

        print(
            f"Closed raw: "
            f"{state['closed_raw']}"
        )

        print(
            f"Open raw: "
            f"{state['open_raw']}"
        )

        target_percent = float(
            input(
                "Target opening [%]: "
            )
        )

        goal_raw = (
            self.robot
            .gripper
            .calculate_goal_raw(
                target_percent
            )
        )

        velocity_text = input(
            f"Velocity [RPM] "
            f"[Enter = "
            f"{self.robot.gripper.default_velocity_rpm:.2f}]: "
        ).strip()

        if velocity_text:

            velocity_rpm = float(
                velocity_text
            )

        else:

            velocity_rpm = (
                self.robot
                .gripper
                .default_velocity_rpm
            )

        print(
            "\nGripper Motion Plan"
        )

        print(
            f"Current: "
            f"{current_percent:.2f}%"
        )

        print(
            f"Target: "
            f"{target_percent:.2f}%"
        )

        print(
            f"Goal raw: "
            f"{goal_raw}"
        )

        print(
            f"Velocity: "
            f"{velocity_rpm:.2f} RPM"
        )

        if not self._confirm(
            "Execute this Gripper motion?"
        ):

            print(
                "Gripper motion cancelled."
            )

            return

        result = (
            self.robot
            .set_gripper_opening(
                target_percent,
                velocity_rpm=velocity_rpm
            )
        )

        print(
            "Gripper reached target."
        )

        print(
            f"Final raw: "
            f"{result['final_raw']}"
        )

    def hold_joint(self):

        joint_key = self._choose_joint()

        if joint_key is None:
            return

        positions = self.robot.hold_joint(
            joint_key
        )

        print(
            f"{joint_key} holding at "
            f"{positions}."
        )

    def set_default_velocity(self):

        print(
            f"\nCurrent velocity: "
            f"{self.default_velocity_deg_s:.2f} deg/s"
        )

        velocity = float(
            input(
                "New joint velocity [deg/s]: "
            )
        )

        updated_velocity = (
            self.jog_controller.set_velocity(
                velocity
            )
        )

        self.default_velocity_deg_s = (
            updated_velocity
        )

        print(
            f"Default velocity set to "
            f"{updated_velocity:.2f} deg/s."
        )

    def set_jog_step(self):

        print(
            f"\nCurrent Jog step: "
            f"{self.jog_controller.step_deg:.2f} deg"
        )

        step_deg = float(
            input(
                "New Jog step [deg]: "
            )
        )

        if step_deg <= 0:
            raise ValueError(
                "Jog step must be greater than zero."
            )

        self.jog_controller.step_deg = (
            step_deg
        )

        print(
            f"Jog step set to "
            f"{step_deg:.2f} deg."
        )

    def move_home(self):

        print(
            "\nHOME will move all joints "
            "to calibrated zero."
        )

        print(
            f"Velocity: "
            f"{self.default_velocity_deg_s:.2f} deg/s"
        )

        if not self._confirm(
            "Move robot to HOME?"
        ):

            print(
                "HOME motion cancelled."
            )

            return

        try:

            self.pose_controller.home(
                self.default_velocity_deg_s
            )

            print(
                "Robot reached HOME."
            )

        finally:

            self._flush_pending_input()

    def jog_joint(self):

        joint_key = self._choose_joint()

        if joint_key is None:
            return

        direction_text = input(
            "Direction [+/-]: "
        ).strip()

        if direction_text == "+":
            direction = 1

        elif direction_text == "-":
            direction = -1

        else:
            raise ValueError(
                "Invalid Jog direction."
            )

        step_deg = float(
            input(
                f"Step [deg] "
                f"[default {self.jog_controller.step_deg}]: "
            )
            or self.jog_controller.step_deg
        )

        self.jog_controller.jog(
            joint_key,
            direction,
            step_deg,
            self.default_velocity_deg_s
        )    

    def jog_gripper(self):

        default_step_percent = 5.0

        while True:

            state = (
                self.robot
                .read_gripper_state()
            )

            current = (
                state[
                    "opening_percent"
                ]
            )

            if current is None:

                raise RuntimeError(
                    "Gripper must be calibrated "
                    "before Jog control."
                )

            print(
                f"\nCurrent Gripper opening: "
                f"{current:.1f}%"
            )

            print(
                "O = Open more"
            )

            print(
                "C = Close more"
            )

            print(
                "0 = Back"
            )

            command = input(
                "Command: "
            ).strip().lower()

            if command == "0":
                return

            if command not in (
                "o",
                "c"
            ):

                print(
                    "Invalid command."
                )

                continue

            step_text = input(
                f"Step [%] "
                f"[Enter = "
                f"{default_step_percent:.1f}]: "
            ).strip()

            if step_text:

                step_percent = float(
                    step_text
                )

            else:

                step_percent = (
                    default_step_percent
                )

            if step_percent <= 0:

                raise ValueError(
                    "Gripper Jog step must "
                    "be greater than zero."
                )

            if command == "o":

                target = (
                    current
                    + step_percent
                )

            else:

                target = (
                    current
                    - step_percent
                )

            target = max(
                0.0,
                min(
                    100.0,
                    target
                )
            )

            self.robot.set_gripper_opening(
                target
            )

            print(
                f"Gripper → "
                f"{target:.1f}%"
            )

    def save_current_pose(self):

        print(
            "\nSave Current Robot Pose"
        )

        pose_name = input(
            "Pose name: "
        ).strip()

        if not pose_name:
            raise ValueError(
                "Pose name cannot be empty."
            )

        current_state = (
            self.robot.read_all_joint_angles()
        )

        print(
            "\nCurrent Joint Angles:"
        )

        for joint_key, angle_deg in (
            current_state.items()
        ):

            print(
                f"{joint_key}: "
                f"{angle_deg:.2f} deg"
            )

        warnings = (
            self.pose_controller
            .get_limit_warnings(
                current_state
            )
        )

        if warnings:

            print(
                "\nWARNING: "
                "Pose is close to joint limits:"
            )

            for warning in warnings:
                print(
                    f"- {warning}"
                )

        if not self._confirm(
            f"Save current position as '{pose_name}'?"
        ):

            print(
                "Pose was not saved."
            )

            return

        try:

            saved = (
                self.pose_controller
                .pose_library
                .save_pose(
                    pose_name,
                    current_state
                )
            )

        except ValueError as error:

            if "already exists" not in str(error):
                raise

            if not self._confirm(
                "Pose already exists. Overwrite?"
            ):

                print(
                    "Existing pose was not changed."
                )

                return

            saved = (
                self.pose_controller
                .pose_library
                .save_pose(
                    pose_name,
                    current_state,
                    overwrite=True
                )
            )

        print(
            f"Pose '{pose_name}' saved."
        )

        print(
            saved
        )

    def edit_pose(self):

        pose_name = self._choose_pose(
            allow_home=False
        )

        if pose_name is None:
            return

        while True:

            pose = (
                self.pose_controller.get_pose(
                    pose_name
                )
            )

            print(
                f"\nEdit Pose: {pose_name}"
            )

            for joint_key, angle_deg in (
                pose.items()
            ):

                print(
                    f"{joint_key}: "
                    f"{angle_deg:.2f} deg"
                )

            print()
            print(
                "1. Replace entire pose "
                "with current robot position"
            )
            print(
                "2. Edit one joint manually"
            )
            print(
                "3. Capture one joint "
                "from current robot"
            )
            print(
                "0. Back"
            )

            choice = input(
                "Select: "
            ).strip()

            if choice == "0":
                return

            if choice == "1":

                if self._confirm(
                    "Replace complete pose "
                    "with current robot position?"
                ):

                    self.pose_controller.update_pose_from_current(
                        pose_name
                    )

                    print(
                        "Pose updated."
                    )

                    print(
                        "Pose updated."
                    )

            elif choice in ("2", "3"):

                joint_key = (
                    self._choose_joint()
                )

                if joint_key is None:
                    continue

                if choice == "2":

                    angle_deg = float(
                        input(
                            "New angle [deg]: "
                        )
                    )

                    self.pose_controller.update_pose_joint(
                        pose_name,
                        joint_key,
                        angle_deg
                    )

                else:

                    self.pose_controller.capture_current_joint(
                        pose_name,
                        joint_key
                    )

                print(
                    "Pose updated."
                )

            else:

                print(
                    "Invalid option."
                )

    def rename_pose(self):

        pose_name = self._choose_pose(
            allow_home=False
        )

        if pose_name is None:
            return

        new_name = input(
            "New pose name: "
        ).strip()

        renamed = (
            self.pose_controller.rename_pose(
                pose_name,
                new_name
            )
        )

        print(
            f"Pose renamed to '{renamed}'."
        )

    def delete_pose(self):

        pose_name = self._choose_pose(
            allow_home=False
        )

        if pose_name is None:
            return

        if not self._confirm(
            f"Delete pose '{pose_name}'?"
        ):

            print(
                "Delete cancelled."
            )

            return

        self.pose_controller.delete_pose(
            pose_name
        )

        print(
            f"Pose '{pose_name}' deleted."
        )

    def show_pose_values(self):

        pose_name = self._choose_pose()

        if pose_name is None:
            return

        pose = (
            self.pose_controller.get_pose(
                pose_name
            )
        )

        print(
            f"\nPose: {pose_name}"
        )

        for joint_key, angle_deg in (
            pose.items()
        ):

            print(
                f"{joint_key}: "
                f"{angle_deg:.2f} deg"
            )

    def _flush_pending_input(self):

        try:

            if not sys.stdin.isatty():
                return

            fd = sys.stdin.fileno()

            termios.tcflush(
                fd,
                termios.TCIFLUSH
            )

        except (
            OSError,
            AttributeError,
            termios.error
        ):

            pass