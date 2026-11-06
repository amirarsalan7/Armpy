class PoseController:

    def __init__(
        self,
        robot,
        pose_library
    ):

        self.robot = robot
        self.pose_library = pose_library


    def get_pose_names(self):

        return (
            self.pose_library.get_pose_names()
        )

    def preview_pose(
        self,
        pose_name,
        velocity_deg_s=None,
        motion_mode="synchronized",
        joint_order=None
    ):

        targets = (
            self.get_pose(
                pose_name
            )
        )

        return (
            self.robot
            .preview_multi_joint_move(
                targets=targets,
                velocity_deg_s=velocity_deg_s,
                motion_mode=motion_mode,
                joint_order=joint_order
            )
        )

    def move_pose(
        self,
        pose_name,
        velocity_deg_s=None,
        motion_mode="synchronized",
        joint_order=None
    ):

        targets = (
            self.get_pose(
                pose_name
            )
        )

        return (
            self.robot
            .move_joints(
                targets=targets,
                velocity_deg_s=velocity_deg_s,
                motion_mode=motion_mode,
                joint_order=joint_order
            )
        )

    def home(
        self,
        velocity_deg_s=None,
        motion_mode="synchronized",
        joint_order=None
    ):

        return (
            self.move_pose(
                pose_name="home",
                velocity_deg_s=velocity_deg_s,
                motion_mode=motion_mode,
                joint_order=joint_order
            )
        )

    def save_current_pose(
        self,
        pose_name,
        overwrite=False
    ):

        targets = (
            self.robot.read_all_joint_angles()
        )

        return self.pose_library.save_pose(
            pose_name,
            targets,
            overwrite=overwrite
        )

    def update_pose_joint(
        self,
        pose_name,
        joint_key,
        angle_deg
    ):

        if pose_name == "home":
            raise ValueError(
                "HOME pose cannot be edited."
            )

        poses = self.data["poses"]

        if pose_name not in poses:
            raise ValueError(
                f"Pose '{pose_name}' does not exist."
            )

        joint = self.robot.get_joint(
            joint_key
        )

        angle_deg = float(
            angle_deg
        )

        joint.check_angle_limits(
            angle_deg
        )

        poses[pose_name][joint_key] = round(
            angle_deg,
            3
        )

        self._save()

        return dict(
            poses[pose_name]
        )

    def update_pose(
        self,
        pose_name,
        targets
    ):

        if pose_name == "home":
            raise ValueError(
                "HOME pose cannot be edited."
            )

        return self.save_pose(
            pose_name,
            targets,
            overwrite=True
        )


    def update_pose_from_current(
        self,
        pose_name
    ):

        targets = (
            self.robot.read_all_joint_angles()
        )

        return self.pose_library.update_pose(
            pose_name,
            targets
        )

    def get_pose(
        self,
        pose_name
    ):

        return (
            self.pose_library.get_pose(
                pose_name
            )
        )


    def update_pose_from_current(
        self,
        pose_name
    ):

        targets = (
            self.robot.read_all_joint_angles()
        )

        return self.pose_library.update_pose(
            pose_name,
            targets
        )


    def update_pose_joint(
        self,
        pose_name,
        joint_key,
        angle_deg
    ):

        return (
            self.pose_library.update_pose_joint(
                pose_name,
                joint_key,
                angle_deg
            )
        )


    def capture_current_joint(
        self,
        pose_name,
        joint_key
    ):

        angle_deg = (
            self.robot.read_joint_angle(
                joint_key
            )
        )

        return (
            self.pose_library.update_pose_joint(
                pose_name,
                joint_key,
                angle_deg
            )
        )


    def rename_pose(
        self,
        old_name,
        new_name
    ):

        return (
            self.pose_library.rename_pose(
                old_name,
                new_name
            )
        )


    def delete_pose(
        self,
        pose_name
    ):

        return (
            self.pose_library.delete_pose(
                pose_name
            )
        )


    def get_limit_warnings(
        self,
        targets,
        margin_deg=3.0
    ):

        return (
            self.pose_library.get_limit_warnings(
                targets,
                margin_deg
            )
        )