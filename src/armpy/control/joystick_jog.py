
class JoystickJogController:

    def __init__(
        self,
        jog_controller,
        pose_controller,
        axis_map,
        deadzone=0.35,
        home_button=0,
        exit_button=1
    ):

        if not 0 <= deadzone < 1:
            raise ValueError(
                "Deadzone must be between 0 and 1."
            )

        self.jog_controller = jog_controller
        self.pose_controller = pose_controller

        self.axis_map = axis_map
        self.deadzone = float(deadzone)

        self.home_button = home_button
        self.exit_button = exit_button

        for axis, mapping in self.axis_map.items():

            if (
                not isinstance(axis, int)
                or len(mapping) != 2
            ):
                raise ValueError(
                    "Invalid joystick axis mapping."
                )

            joint_key, axis_direction = mapping

            if axis_direction not in (-1, 1):
                raise ValueError(
                    "Axis direction must be +1 or -1."
                )


    def _calculate_velocity(self, axis_value):

        magnitude = abs(axis_value)

        if magnitude <= self.deadzone:
            return None

        normalized = (
            (magnitude - self.deadzone)
            / (1.0 - self.deadzone)
        )

        minimum_velocity = (
            self.jog_controller.robot
            .MIN_JOINT_VELOCITY_DEG_S
        )

        maximum_velocity = (
            self.jog_controller.velocity_deg_s()
        )

        velocity = (
            minimum_velocity
            + normalized
            * (maximum_velocity - minimum_velocity)
        )

        return velocity


    def run(self):

        try:
            import pygame

        except ImportError as error:

            raise RuntimeError(
                "Joystick control requires pygame."
            ) from error

        joystick = None

        pygame.init()
        pygame.joystick.init()

        try:

            if pygame.joystick.get_count() == 0:

                raise RuntimeError(
                    "No joystick was detected."
                )

            if not self.axis_map:

                raise RuntimeError(
                    "Joystick axis map is empty. "
                    "Configure JOYSTICK_AXIS_MAP first."
                )

            joystick = pygame.joystick.Joystick(0)

            joystick.init()

            print(
                f"\nJoystick: {joystick.get_name()}"
            )

            print(
                f"Axes: {joystick.get_numaxes()}"
            )

            print(
                f"Buttons: {joystick.get_numbuttons()}"
            )

            for axis, mapping in self.axis_map.items():

                if axis >= joystick.get_numaxes():

                    raise RuntimeError(
                        f"Axis {axis} does not exist "
                        "on this joystick."
                    )

                joint_key, _ = mapping

                self.jog_controller.robot.get_joint(
                    joint_key
                )

            self.jog_controller.reset_targets()

            print("\nJoystick Jog Active")
            print("Move joystick to control joints.")
            print("HOME button → Robot HOME")
            print("Exit button → Return to menu")

            running = True

            while running:

                event = pygame.event.wait()

                if event.type == pygame.QUIT:
                    break

                if event.type == pygame.JOYBUTTONDOWN:

                    if event.button == self.exit_button:

                        running = False

                    elif event.button == self.home_button:

                        self.pose_controller.home(
                            self.jog_controller.velocity_deg_s()
                        )

                        self.jog_controller.reset_targets()

                elif event.type == pygame.JOYAXISMOTION:

                    if event.axis not in self.axis_map:
                        continue

                    value = float(event.value)

                    velocity = self._calculate_velocity(
                        value
                    )

                    if velocity is None:
                        continue

                    joint_key, axis_direction = (
                        self.axis_map[event.axis]
                    )

                    direction = (
                        1
                        if value * axis_direction > 0
                        else -1
                    )

                    self.jog_controller.jog(
                        joint_key,
                        direction,
                        velocity_deg_s=velocity,
                        wait=False
                    )

        finally:

            self.jog_controller.reset_targets()

            if joystick is not None:
                joystick.quit()

            pygame.joystick.quit()
            pygame.quit()
