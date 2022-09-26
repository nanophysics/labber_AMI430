from dataclasses import dataclass
from typing import Callable, Optional
import enum


class Axis(enum.IntEnum):
    AXIS2 = 2
    AXIS3 = 3


@dataclass(frozen=True)
class Magnet:
    ip_address: str
    current_limit: float
    field_limit: float
    ramp_rate_limit: float
    switchheater: bool


@dataclass(frozen=True)
class Station:
    name: str
    field_limit: Callable
    x_axis: Magnet
    y_axis: Magnet
    z_axis: Optional[Magnet] = None
    use_visa_simulation: bool = False

    @property
    def axis(self) -> Axis:
        return Axis.AXIS2 if self.z_axis is None else Axis.AXIS3
