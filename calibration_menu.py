class CalibrationMenu:

    MIN_MOVEMENT_COUNTS = 20

    def __init__(self,calibration,file_path):

        self.calibration = calibration
        self.file_path = file_path

    def _auto_save(self):

        path = self.calibration.save(self.file_path)
        
        print(f"Saved:{path}")

    def _choose_joint(self):

        joints = self.calibration.robot_config.get_all_joints()
        joint_keys = list(joints)

        while True:

            print("\nSelect Joint:")

            for index,joint_key in enumerate(joint_keys,start=1):
                print(f"{index}.{joint_key}-{joints[joint_key]['name']}")

            print("0.back")

            choice = input("Selec: ").strip()

            if choice == "0":
                return None

            if choice.isdigit() and 1 <= int (choice) <= len(joint_keys):
                return joint_keys[int(choice) - 1]

            print("Invalid selection.")

    def _accept(self):

        while True:

            answer = input("Accept?[y]Yes [r]Retry [s]Skip:").strip().lower()

            if answer in ("y","r","s"):
                return answer

            print("invalid selection.")

    def show(self):

        while True:
            print("\n========================")
            print("ARMPy Calibration ")
            print("========================\n")
            print("1.Home Calibration")
            print("2.Direction Calibration")
            print("3.Limit Calibration")
            print("4.Gripper Calibration")
            print("5.Calibration status")
            print("6.Verify Calibration")
            print("7.Exit")

            choice = input("\nSelect option:").strip()

            if choice == "7":
                print("Exiting. All accepted results were saved.")
                return

            try:

                if choice == "1":
                    self.home_calibration()

                elif choice == "2":
                    self.direction_calibration()

                elif choice == "3":
                    self.limit_calibration()

                elif choice == "4":
                    self.gripper_calibration()

                elif choice == "5":
                    self.show_status()

                elif choice == "6":
                    self.verify()


                else:
                    print("Invalid option.")

            except (RuntimeError,ValueError,KeyError,OSError)as error:
                print(f"\nCalibration error:{error}")
                print("Returning to main menu."
                      "Check robot support before retrying.")

    def home_calibration(self):

        while True:
                
            print("---Home/zero calibration---")
            print("1.Capture Complete Robot HOME.")
            print("2.Capture One Joint HOME.")
            print("3.Capture Grrpper Refrence.")
            print("0.Back")

            choice = input("Select: ").strip()

            if choice == "0":
                return

            if choice == "1":

                answer = input(
                    "This may invalidete existing limits.Continue?[y/n]"
                    ).strip().lower()

                if answer != "y":
                    continue

                self.calibration.check_all_torque_off()

                print("Support the robot and place all joints in the chosen Home pose.")

                input("Press Enter when ready...")

                self.calibration.check_all_torque_off()

                data = self.calibration.capture_home()

                self._auto_save()

                for joint_key,joint in data["joints"].items():
                    print(f"{joint_key}:{joint['home']['raw']}")

                print(f"Gripper reference:{data['gripper']['reference']['raw']}")

            elif choice == "2":

                joint_key = self._choose_joint()

                if joint_key is None:
                    continue

                self.calibration.check_joint_torque_off(joint_key)

                print(f"Support the robot."
                      "Place{joint_key} at the intended HOME pose.")

                input("Press Enter when ready...")

                self.calibration.check_joint_torque_off(joint_key)

                positions = self.calibration.read_joint_positions(joint_key)

                print(f"Measured HOME :{positions}")

                answer = input("Save this HOME?[y/n]")

                if answer == "y":
                    self.calibration.store_joint_home(joint_key,positions)
                    self._auto_save()

            elif choice == "3":

                self.calibration.check_gripper_torque_off()

                print("Support the gripper "
                      "and place it at the reference pose.")

                input("Press Enter when ready...")

                self.calibration.check_gripper_torque_off()

                position = self.calibration.read_gripper_position()

                print(f"Gripper reference:{position}")

                answer = input("Save this reference?[y/n]:").strip().lower()

                if answer == "y":
                    self.calibration.store_gripper_reference(position)
                    self._auto_save()

                else:
                    print("invalid selection.")

    def _run_direction(self,joint_key):

        config = (
            self.calibration.robot_config.get_joint_config(joint_key))

        positive_motion = config.get("positive_motion")

        if not positive_motion:
            raise ValueError(
                f"set a fixed positive_motion"
                f" for {joint_key} in robot_joints.json"
            )

        joint = self.calibration.calibration["joints"][joint_key]

        if not joint["home"]["calibrated"]:
            raise RuntimeError(f"Calibrate {joint_key} HOME first.")

        while True:

            self.calibration.check_joint_torque_off(joint_key)

            print(f"Joint:{joint_key}|Motors:{config["motor_ids"]}")
            print(f"Fixed POSITIVE motion:{positive_motion}")
            print("Support the robot. Move ONLY this joint without forcing it.")
            input("Place it at asafe starting pose,then press Enter...")

            self.calibration.check_joint_torque_off(joint_key)

            before = self.calibration.read_joint_positions(joint_key)

            print(f"BEFORE:{before}")

            input("Move a SMALL amount in the FIXED POSITIVE direction;"
                    "press Enter...")

            self.calibration.check_joint_torque_off(joint_key)

            after = self.calibration.read_joint_positions(joint_key)

            print(f"AFTER:{after}")

            try:

                directions,deltas = self.calibration.calculate_joint_directions(
                    before,after,self.MIN_MOVEMENT_COUNTS
                )

                if joint_key == "joint2" and directions.get("2") == directions.get("3"):
                    raise RuntimeError(
                        "Shoulder motor 2 and 3 mist have opposite signs."
                    )

                for motor_id in directions:
                    print(
                        f"Motor {motor_id}:{deltas[motor_id]},"
                        f"direction={directions[motor_id]}"
                    )

            except(RuntimeError,ValueError)as error:
                print("Rejected measurement:{error}")

                answer = input("Retry this joint?[y/n]:").strip().lower()

                if answer == "y":
                    continue

                return
            
            answer = self._accept()

            if answer == "s":
                return

            if answer == "r":
                continue

            self.calibration.store_joint_direction(
                joint_key,before,after,deltas,directions
            )

            self._auto_save()

            print(f"{joint_key} direction saved.")

            return
    
    def direction_calibration(self):

        self._joint_submenu("Direction",self._run_direction)

    def _run_limits(self,joint_key):

        config = self.calibration.robot_config.get_joint_config(joint_key)
        joint = self.calibration.calibration["joints"][joint_key]

        if not joint["home"]["calibrated"] or not joint["direction"]["calibrated"]:
            raise RuntimeError(
                f"Calibrated {joint_key} HOME and direction first."
            )

        positive_motion = config.get("positive_motion")

        if not positive_motion:
            raise ValueError(
                f"Set positive_motion for {joint_key} in robot_joints.json."
            )
        while True:

            self.calibration.check_joint_torque_off(joint_key)

            print(f"\nJoint: {joint_key}")
            print(f"Fixed POSITIVE motion: {positive_motion}")
            print("Record SAFE SOFTWARE limits with a margin BEFORE hard stops.")
            print("Support the arm. Never force a joint to a hard stop.")

            input("Place joint at NEGATIVE safe limit, then press Enter...")

            self.calibration.check_joint_torque_off(joint_key)

            negative = self.calibration.read_joint_positions(joint_key)

            print(f"NEGATIVE: {negative}")

            input("Return joint to calibrated HOME pose, then press Enter...")

            self.calibration.check_joint_torque_off(joint_key)

            middle = self.calibration.read_joint_positions(joint_key)

            print(f"MIDDLE / HOME: {middle}")

            input("Move joint to POSITIVE safe limit, then press Enter...")

            self.calibration.check_joint_torque_off(joint_key)

            positive = self.calibration.read_joint_positions(joint_key)

            print(f"POSITIVE: {positive}")

            answer = self._accept()

            if answer == "s":
                return

            if answer == "r":
                continue

            try:

                self.calibration.store_joint_limits(
                    joint_key, negative, middle, positive
                )

            except (RuntimeError, ValueError) as error:

                print(f"Limits rejected: {error}")

                retry = input("Retry this joint? [y/n]: ").strip().lower()

                if retry == "y":
                    continue

                return

            self._auto_save()

            print(f"{joint_key} limits saved.")

            return

    def limit_calibration(self):

        self._joint_submenu("Joint Limits", self._run_limits)


    def _joint_submenu(self, title, operation):

        while True:

            print(f"\n--- {title} ---")
            print("1. All Joints")
            print("2. One Joint / Repeat")
            print("0. Back")

            choice = input("Select: ").strip()

            if choice == "0":
                return

            if choice == "1":

                joints = self.calibration.robot_config.get_all_joints()

                for joint_key in joints:
                    operation(joint_key)

            elif choice == "2":

                joint_key = self._choose_joint()

                if joint_key is not None:
                    operation(joint_key)

            else:
                print("Invalid selection.")


    def gripper_calibration(self):

        while True:

            print("\n--- Gripper Calibration ---")
            print("1. Full Open / Close")
            print("2. Set Open")
            print("3. Set Close")
            print("4. Set Reference")
            print("0. Back")

            choice = input("Select: ").strip()

            if choice == "0":
                return

            if choice == "4":

                self.calibration.check_gripper_torque_off()

                print("Support the gripper and move it to its reference pose.")

                input("Press Enter when ready...")

                self.calibration.check_gripper_torque_off()

                position = self.calibration.read_gripper_position()

                print(f"REFERENCE: {position}")

                answer = input("Accept? [y/n]: ").strip().lower()

                if answer == "y":
                    self.calibration.store_gripper_reference(position)
                    self._auto_save()

                continue

            if choice not in ("1", "2", "3"):
                print("Invalid selection.")
                continue

            self.calibration.check_gripper_torque_off()

            if choice in ("1", "2"):

                input("Move gripper to SAFE OPEN pose, then press Enter...")

                self.calibration.check_gripper_torque_off()

                open_raw = self.calibration.read_gripper_position()

                print(f"OPEN: {open_raw}")

            if choice in ("1", "3"):

                input("Move gripper to SAFE CLOSE pose, then press Enter...")

                self.calibration.check_gripper_torque_off()

                close_raw = self.calibration.read_gripper_position()

                print(f"CLOSE: {close_raw}")

            answer = input("Accept? [y/n]: ").strip().lower()

            if answer != "y":
                continue

            if choice == "1":
                self.calibration.store_gripper_positions(open_raw, close_raw)

            elif choice == "2":
                self.calibration.store_gripper_open(open_raw)

            else:
                self.calibration.store_gripper_close(close_raw)

            self._auto_save()


    def show_status(self):

        status = self.calibration.get_status()

        print("\n--- Calibration Status ---")

        for joint_key, joint in status["joints"].items():

            print(
                f"{joint_key}: HOME={joint['home']} "
                f"DIR={joint['direction']} LIMITS={joint['limits']}"
            )

        gripper = status["gripper"]

        print(
            f"Gripper: REF={gripper['reference']} "
            f"OPEN/CLOSE={gripper['open_close']}"
        )


    def verify(self):

        print("\n--- Stored Calibration Data Verification ---")

        issues = self.calibration.verify()

        if issues:

            for issue in issues:
                print(f"FAIL: {issue}")

        else:
            print("PASS: Stored calibration passed the implemented data checks.")

        print("This is NOT a live mechanical safety or motion verification.")