from mimetypes import init
import numpy as np


class Magnet:
    def __init__(self) -> None:
        self.setpoint: float = 0


class TestStation:
    def __init__(self, field_limit) -> None:
        self.magnet_x: Magnet = Magnet()
        self.magnet_y: Magnet = Magnet()
        self.magnet_z: Magnet = Magnet()
        self.field_limit = field_limit

    def _check_field_setpoint(self, magnet, value):
        setpoints = {
            "x": self.magnet_x.setpoint,
            "y": self.magnet_y.setpoint,
            "z": self.magnet_z.setpoint,
        }
        setpoints[magnet] = value
        setpoint_values = [setpoints["x"], setpoints["y"], setpoints["z"]]
        answer = any(
            [limit_function(*setpoint_values) for limit_function in self.field_limit]
        )
        return answer

    def set_quantity(self, magnet, value):
        magnet_handle = self._magnet_translator[magnet]
        if self._check_field_setpoint(magnet, value):
            magnet_handle.setpoint = value
            print("This action is allowed")
            return
        else:
            raise Exception("The value is not allowed")

    @property
    def _magnet_translator(self):
        return {"x": self.magnet_x, "y": self.magnet_y, "z": self.magnet_z}


field_limit = (
    [  # If any of the field limit functions are satisfied we are in the safe zone.
        lambda x, y, z: np.abs(x) <= 1e-12
        and np.abs(y) <= 1e-12
        and z <= 6,  # We can have higher field along the z-axis if x and y are zero.
        lambda x, y, z: np.abs(x) <= 1e-12 and np.linalg.norm([y, z]) <= 3,
        lambda x, y, z: np.linalg.norm([x, y, z]) <= 1,
    ]
)


def main():
    # setpoint_values = (0,3/np.sqrt(2),3/np.sqrt(2))
    # print(check_field_setpoint(field_limit, setpoint_values))

    t = TestStation(field_limit)
    t.set_quantity("x", 1 / np.sqrt(3))
    t.set_quantity("y", 1 / np.sqrt(3))
    t.set_quantity("z", 1 / np.sqrt(3))


if __name__ == "__main__":
    main()
