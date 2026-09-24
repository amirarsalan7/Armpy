import json


class RobotConfig:


    def __init__(
        self,
        file_path
    ):

        self.file_path = file_path

        self.data = self._load()


    def _load(self):

        with open(
            self.file_path,
            "r"
        ) as file:

            data = json.load(file)


        return data



    def get_robot_name(self):

        return self.data["robot_name"]



    def get_all_joints(self):

        return self.data["joints"]



    def get_joint_config(
        self,
        joint_name
    ):

        joints = self.data["joints"]


        if joint_name not in joints:

            raise ValueError(
                f"Joint {joint_name} "
                "does not exist."
            )


        return joints[joint_name]



    def get_gripper_config(self):

        return self.data["gripper"]