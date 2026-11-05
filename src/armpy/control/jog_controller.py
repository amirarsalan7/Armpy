
import math


class JogController:

    def __init__(
        self,
        robot,
        step_deg=1.0,
    ):

        self.robot = robot

        self.step_deg = float(step_deg)

        if (
            not math.isfinite(self.step_deg)
            or self.step_deg <= 0
        ):
            raise ValueError(
                "Jog step must be a positive finite number."
            )

        self.target_angles = {}


    def velocity_deg_s(self):

        return (
            self.robot
            .default_joint_velocity_deg_s
        )


    def set_velocity(
        self,
        velocity_deg_s
    ):

        return (
            self.robot
            .set_default_joint_velocity(
                velocity_deg_s
            )
        )


    def jog(
        self,
        joint_key,
        direction,
        step_deg=None,
        velocity_deg_s=None,
        wait=False
    ):

        if (
            isinstance(direction, bool)
            or direction not in (-1, 1)
        ):
            raise ValueError(
                "Jog direction must be +1 or -1."
            )

        if step_deg is None:
            step_deg = self.step_deg

        try:

            step_deg = float(step_deg)

        except (TypeError, ValueError):

            raise ValueError(
                "Jog step must be numeric."
            )

        if (
            not math.isfinite(step_deg)
            or step_deg <= 0
        ):
            raise ValueError(
                "Jog step must be a positive finite number."
            )

        if velocity_deg_s is None:

            velocity_deg_s = (
                self.velocity_deg_s()
            )

        joint = self.robot.get_joint(
            joint_key
        )

        current_angle = (
            self.robot.read_joint_angle(
                joint_key
            )
        )

        base_target = self.target_angles.get(
            joint_key,
            current_angle
        )

        target_angle = (
            base_target
            + direction * step_deg
        )

        target_angle = max(
            joint.min_angle_deg,
            min(
                joint.max_angle_deg,
                target_angle
            )
        )

        result = self.robot.move_joint(
            joint_key=joint_key,
            target_angle_deg=target_angle,
            velocity_deg_s=velocity_deg_s,
            wait=wait
        )

        self.target_angles[joint_key] = (
            target_angle
        )

        return result


    def reset_targets(self):

        self.target_angles.clear()
