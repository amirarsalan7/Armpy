class RobotControlMenu:

    def __init__(self, robot):

        self.robot = robot


    def show(self):

        while True:

            print("\n========================")
            print("ARMPy Control")
            print("========================")
            print("1. Read Robot State")
            print("2. Move One Joint")
            print("3. Show Joint Limits")
            print("4. Hold Joint Position")
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
                suffix = " [synchronized motion required]"

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

        if len(joint.motors) != 1:
            raise RuntimeError(
                f"{joint_key}: synchronized dual-motor "
                "motion is not implemented yet."
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

        plan = self.robot.preview_joint_move(
            joint_key,
            target_angle
        )

        print("\nMotion Plan")
        print(
            f"Current: {plan['current_angle_deg']:.2f} deg"
        )
        print(
            f"Target:  {plan['target_angle_deg']:.2f} deg"
        )
        print(
            f"Move:    {plan['movement_deg']:.2f} deg"
        )
        print(
            f"Raw:     {plan['current_raw']} "
            f"-> {plan['goal_raw']}"
        )

        answer = input(
            "Execute this motion? [y/n]: "
        ).strip().lower()

        if answer != "y":
            print("Motion cancelled.")
            return

        result = self.robot.move_joint(
            joint_key,
            target_angle
        )

        print(
            f"{joint_key} reached target. "
            f"Final raw: {result['final_raw']}"
        )


    def hold_joint(self, joint_key):

        joint = self._require_single_motor_joint(
            joint_key
        )

        motor_id = next(iter(joint.motors))
        motor = joint.motors[motor_id]

        torque = motor.read_torque_enabled()

        if torque is None:
            raise RuntimeError(
                f"{joint_key}: could not read torque state "
                f"from Motor {motor.motor_id}."
            )

        if torque != motor.TORQUE_ON:
            raise RuntimeError(
                f"{joint_key}: torque is not enabled."
            )

        present_raw = motor.read_present_position_raw()

        if present_raw is None:
            raise RuntimeError(
                f"{joint_key}: could not read Present Position "
                f"from Motor {motor.motor_id}."
            )

        motor.validate_goal_position_raw(
            present_raw
        )

        if not motor.set_goal_position_raw(
            present_raw
        ):
            raise RuntimeError(
                f"{joint_key}: could not hold current position."
            )

        return present_raw