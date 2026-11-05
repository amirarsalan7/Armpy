import sys
import termios
import tty


class KeyboardJogController:

    KEY_MAP = {
        "q": ("joint1", 1),
        "a": ("joint1", -1),

        "w": ("joint2", 1),
        "s": ("joint2", -1),

        "e": ("joint3", 1),
        "d": ("joint3", -1),

        "r": ("joint4", 1),
        "f": ("joint4", -1),

        "t": ("joint5", 1),
        "g": ("joint5", -1),
    }


    def __init__(
        self,
        jog_controller,
        pose_controller
    ):

        self.jog_controller = jog_controller
        self.pose_controller = pose_controller


    def run(self):

        print("\nKeyboard Jog")
        print("Q/A → Joint1 +/-")
        print("W/S → Joint2 +/-")
        print("E/D → Joint3 +/-")
        print("R/F → Joint4 +/-")
        print("T/G → Joint5 +/-")
        print("H   → HOME")
        print("X   → Exit")

        fd = sys.stdin.fileno()

        old_settings = termios.tcgetattr(fd)

        self.jog_controller.reset_targets()

        try:

            termios.tcflush(
                fd,
                termios.TCIFLUSH
            )

            tty.setcbreak(
                fd
            )

            while True:

                key = (
                    sys.stdin.read(1)
                    .lower()
                )

                if not key:
                    return

                if key == "x":
                    return

                try:

                    if key == "h":

                        self.pose_controller.home(
                            self.jog_controller.velocity_deg_s()
                        )

                        self.jog_controller.reset_targets()

                        continue

                    command = self.KEY_MAP.get(
                        key
                    )

                    if command is None:
                        continue

                    joint_key, direction = command

                    self.jog_controller.jog(
                        joint_key,
                        direction,
                        wait=False
                    )

                except (
                    RuntimeError,
                    ValueError,
                    TimeoutError
                ) as error:

                    print(
                        f"\nJog error: {error}"
                    )

        finally:

            termios.tcsetattr(
                fd,
                termios.TCSADRAIN,
                old_settings
            )

            termios.tcflush(
                fd,
                termios.TCIFLUSH
            )
