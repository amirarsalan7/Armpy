class RobotControlMenu:

    def __init__(self, robot):

        self.robot = robot

        self.default_velocity_deg_s = (
            robot.DEFAULT_JOINT_VELOCITY_DEG_S
        )

    def show(self):

        while True:

            print("\n========================")
            print("ARMPy Control")
            print("========================")
            print("1. Read Robot State")
            print("2. Move One Joint")
            print("3. Show Joint Limits")
            print("4. Hold Joint Position")
            print("5. Set Default Velocity")
            print("0. Exit")

            choice = input("\nSelect option: ").strip()

            try:

                if choice == "1":
                    self.show_robot_state()

                elif choice == "2":
                    self.move_one_joint()

                elif choice == "3":
                    self.show_joint_limits()

                elif choice == "4":
                    self.hold_joint()

                elif choice == "5":
                    self.set_default_velocity()

                elif choice == "0":
                    print(
                        "Exiting control menu. "
                        "Motor torque states are unchanged."
                    )
                    return

                else:
                    print("Invalid option.")

            except (
                RuntimeError,
                ValueError,
                TimeoutError
            ) as error:

                print(
                    f"\nControl error: {error}"
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


    def show_joint_limits(self):

        for joint_key in self.robot.get_joint_names():

            joint = self.robot.get_joint(
                joint_key
            )

            print(
                f"{joint_key}: "
                f"{joint.min_angle_deg:.2f} "
                f"to {joint.max_angle_deg:.2f} deg"
            )


    def move_one_joint(self):

        joint_key = self._choose_joint()

        if joint_key is None:
            return

        joint = self.robot.get_joint(
            joint_key
        )


        current_angle = self.robot.read_joint_angle(
            joint_key
        )

        print(
            f"\nCurrent angle: {current_angle:.2f} deg"
        )

        print(
            f"Safe limits: "
            f"{joint.min_angle_deg:.2f} "
            f"to {joint.max_angle_deg:.2f} deg"
        )

        target_angle = float(
            input("Target angle [deg]: ")
        )

        velocity_text = input(
            f"Velocity [deg/s] "
            f"[Enter = {self.default_velocity_deg_s:.2f}]: "
        ).strip()

        if velocity_text:

            velocity_deg_s = float(
                velocity_text
            )

        else:

            velocity_deg_s = (
                self.default_velocity_deg_s
            )

        plan = self.robot.preview_joint_move(
            joint_key,
            target_angle,
            velocity_deg_s
        )

        print("\nMotion Plan")

        print(
            f"Current:  "
            f"{plan['current_angle_deg']:.2f} deg"
        )

        print(
            f"Target:   "
            f"{plan['target_angle_deg']:.2f} deg"
        )

        print(
            f"Move:     "
            f"{plan['movement_deg']:.2f} deg"
        )

        print(
            f"Velocity: "
            f"{plan['velocity_deg_s']:.2f} deg/s"
        )

        print(
            f"Raw current: {plan['current_raw']}"
        )

        print(
            f"Raw goals:   {plan['goal_raw']}"
        )

        answer = input(
            "Execute this motion? [y/n]: "
        ).strip().lower()

        if answer != "y":
            print("Motion cancelled.")
            return

        result = self.robot.move_joint(
            joint_key,
            target_angle,
            velocity_deg_s
        )

        print(
            f"{joint_key} reached target. "
            f"Final raw: {result['final_raw']}"
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

        self.robot._validate_joint_velocity(
            velocity
        )

        self.default_velocity_deg_s = velocity

        print(
            f"Default velocity set to "
            f"{velocity:.2f} deg/s."
        )