import json

from datetime import datetime
from pathlib import Path

from dynamixel_motor import DynamixelMotor

class JointCalibration:

    def __init__(
            self,
            connection,
            hardware_inventory,
            robot_config
     ):

        self.connection = connection

        self.hardware_inventory = ( hardware_inventory )
        self.robot_config = robot_config
        self.motor_objects = {}
        self.calibration = None


        self._validate_mapping()
        self._build_motor_objects()


    def _validate_mapping(self):

        available_motor_ids = set(
            self.hardware_inventory.get_motor_ids() )

        joints = (
            self.robot_config.get_all_joints()
        )

        for(joint_key, joint_data )in joints.items():

            for motor_id in joint_data["motor_ids"]:

                if (motor_id not in available_motor_ids):
                    
                    raise ValueError(
                        f"{joint_key} uses "
                        f"Motor {motor_id},"
                        "but that motor does not "
                        "exist in hardware inventory"
                    )
            
        gripper = ( self.robot_config.get_gripper_config())

        gripper_motor_id = ( gripper["motor_id"])

        if( gripper_motor_id not in available_motor_ids ):
                
                raise ValueError(
                    f"gripper uses Motor "
                    f"{gripper_motor_id},"
                    "but that motor dose not "
                    "exist in hardware inventory."
                ) 

        return True

    def _build_motor_objects(self):

        for motor_id in ( self.hardware_inventory.get_motor_ids()):
            motor_info = (self.hardware_inventory.get_motor(motor_id))
            identity = (motor_info["identity"])

            motor = DynamixelMotor(
                connection=self.connection,

                motor_id = motor_id,

                model_number = identity["model_number"],

                firmware_version=identity["firmware_version"]
            )

            self.motor_objects[motor_id] = motor

    def _read_motor_position_raw(
            self,
            motor_id
    ):
        motor = self.motor_objects[motor_id]

        status = motor.read_status()

        position_raw = (status["position_raw"])

        if position_raw is None:
            raise RuntimeError(
                f"Could not read position from motor {motor_id}."
            )
        return position_raw

    def capture_home(self):

        joints = self.robot_config.get_all_joints()

        joint_calibrations = {}

        for joint_key,joint_data in joints.items():
            
            home_raw = {}

            for motor_id in joint_data["motor_ids"]:

                position = self._read_motor_position_raw(motor_id)

                home_raw[str(motor_id)] = position

            joint_calibrations[joint_key] = {
                    
                "name":joint_data["name"],

                "motor_ids":joint_data["motor_ids"],

                "home_raw": home_raw,

                "direction_calibrated":False,

                "limits_calibrated":False
                }

        gripper_config = self.robot_config.get_gripper_config()

        gripper_motor_id = gripper_config["motor_id"]

        gripper_reference_raw = (
            self._read_motor_position_raw(gripper_motor_id)
        )

        self.calibration = {

            "schema_version":1,

            "calibrated_at":(
                datetime.now()
                .astimezone()
                .isoformat(
                    timespec="seconds"
                )
            ),
            "source_hardware_inventory":(
                str(self.hardware_inventory.file_path)),
                
            "joints":( joint_calibrations),

            "gripper":{

                "motor_id":(
                    gripper_motor_id
                ),
                "reference_raw":(
                    gripper_reference_raw
                ),
                "open_close_calibration": False

            }
        }

        return self.calibration

    def save( self,file_path):
        if self.calibration is None:

            raise RuntimeError(
                "Capture calibration before saving."
            )
        
        path = Path(file_path)

        path.parent.mkdir(
            parents=True,exist_ok=True
        )

        with path.open( "w",encoding= "utf-8") as file:

            json.dump( self.calibration,file,indent=4)

        return path