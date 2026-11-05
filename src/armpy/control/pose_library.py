import json

from pathlib import Path


class PoseLibrary:

    def __init__(self, file_path, robot):

        self.file_path = Path(
            file_path
        )

        self.robot = robot

        self.data = self._load()

        self._validate()


    def _load(self):

        with self.file_path.open(
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(
                file
            )

    def _save(self):

        temporary_file = (
            self.file_path.parent
            / f"{self.file_path.name}.tmp"
        )

        with temporary_file.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.data,
                file,
                indent=4
            )

            file.write("\n")

        temporary_file.replace(
            self.file_path
        )

    def save_pose(
        self,
        pose_name,
        targets,
        overwrite=False
    ):

        pose_name = (
            self._normalize_pose_name(
                pose_name
            ) 
        )

        if not pose_name:
            raise ValueError(
                "Pose name cannot be empty."
            )

        if pose_name == "home":
            raise ValueError(
                "HOME is calibration-defined "
                "and cannot be overwritten."
            )

        expected_joints = set(
            self.robot.get_joint_names()
        )

        if set(targets) != expected_joints:
            raise ValueError(
                "A named pose must contain "
                "all robot joints."
            )

        clean_targets = {}

        for joint_key, angle_deg in targets.items():

            angle_deg = float(
                angle_deg
            )

            joint = self.robot.get_joint(
                joint_key
            )

            joint.check_angle_limits(
                angle_deg
            )

            clean_targets[joint_key] = round(
                angle_deg,
                3
            )

        poses = self.data["poses"]

        if (
            pose_name in poses
            and not overwrite
        ):
            raise ValueError(
                f"Pose '{pose_name}' already exists."
            )

        poses[pose_name] = clean_targets

        self._save()

        return dict(
            clean_targets
        )

    def update_pose_joint(
        self,
        pose_name,
        joint_key,
        angle_deg
    ):

        pose_name = (
            self._normalize_pose_name(
                pose_name
            )
        )

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
    
    def _validate(self):

        if self.data.get("robot_name") != self.robot.name:
            raise ValueError(
                "Pose library belongs to another robot."
            )

        poses = self.data.get(
            "poses"
        )

        if not isinstance(poses, dict) or not poses:
            raise ValueError(
                "Pose library contains no poses."
            )

        expected_joints = set(
            self.robot.get_joint_names()
        )

        for pose_name, targets in poses.items():

            if set(targets) != expected_joints:
                raise ValueError(
                    f"Pose {pose_name} does not contain "
                    "all robot joints."
                )

            for joint_key, angle_deg in targets.items():

                joint = self.robot.get_joint(
                    joint_key
                )

                joint.check_angle_limits(
                    float(angle_deg)
                )

        return True


    def get_pose(self, pose_name):

        poses = self.data["poses"]

        if pose_name not in poses:
            raise ValueError(
                f"Pose {pose_name} does not exist."
            )

        return dict(
            poses[pose_name]
        )


    def get_pose_names(self):

        return list(
            self.data["poses"]
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

        pose_name = (
            self._normalize_pose_name(
                pose_name
            )
        )

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

    def _normalize_pose_name(
        self,
        pose_name
    ):

        return (
            pose_name
            .strip()
            .lower()
            .replace(" ", "_")
        )

    def rename_pose(
            
        self,
        old_name,
        new_name
    ):

        old_name = (
            self._normalize_pose_name(
                old_name
            )
        )

        new_name = (
            self._normalize_pose_name(
                new_name
            )
        )

        if old_name == "home":
            raise ValueError(
                "HOME pose cannot be renamed."
            )

        if not new_name:
            raise ValueError(
                "New pose name cannot be empty."
            )

        poses = self.data["poses"]

        if old_name not in poses:
            raise ValueError(
                f"Pose '{old_name}' does not exist."
            )

        if new_name in poses:
            raise ValueError(
                f"Pose '{new_name}' already exists."
            )

        poses[new_name] = poses.pop(
            old_name
        )

        self._save()

        return new_name

    def delete_pose(
        self,
        pose_name
    ):

        pose_name = (
            self._normalize_pose_name(
                pose_name
            )
        )

        if pose_name == "home":
            raise ValueError(
                "HOME pose cannot be deleted."
            )

        poses = self.data["poses"]

        if pose_name not in poses:
            raise ValueError(
                f"Pose '{pose_name}' does not exist."
            )

        removed = poses.pop(
            pose_name
        )

        self._save()

        return removed

def get_limit_warnings(
    self,
    targets,
    margin_deg=3.0
):

    warnings = []

    for joint_key, angle_deg in (
        targets.items()
    ):

        joint = self.robot.get_joint(
            joint_key
        )

        angle_deg = float(
            angle_deg
        )

        negative_distance = (
            angle_deg
            - joint.min_angle_deg
        )

        positive_distance = (
            joint.max_angle_deg
            - angle_deg
        )

        if negative_distance < 0:

            warnings.append(
                f"{joint_key} is "
                f"{abs(negative_distance):.2f} deg "
                "beyond its negative limit."
            )

        elif negative_distance <= margin_deg:

            warnings.append(
                f"{joint_key} is only "
                f"{negative_distance:.2f} deg "
                "from its negative limit."
            )

        if positive_distance < 0:

            warnings.append(
                f"{joint_key} is "
                f"{abs(positive_distance):.2f} deg "
                "beyond its positive limit."
            )

        elif positive_distance <= margin_deg:

            warnings.append(
                f"{joint_key} is only "
                f"{positive_distance:.2f} deg "
                "from its positive limit."
            )

    return warnings