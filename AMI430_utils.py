from dataclasses import dataclass
from typing import Callable, Optional
import enum


class FieldLimitViolation(Exception):
    pass


def check_smaller_than(value: float, limit: float, msg: str) -> None:
    if value >= limit:
        raise FieldLimitViolation(f"{value} >= {limit}: {msg}")


class Axis(enum.IntEnum):
    AXIS2 = 2
    AXIS3 = 3


@dataclass(frozen=True)
class Magnet:
    """
    This is the magnet configuration
    """

    ip_address: str
    current_limit_A: float
    field_limit_T: float
    ramp_rate_limit_Apers: float
    ramp_rate_initial_Apers: float
    inductance_H: float
    """
    Inductance...
    """

    has_switchheater: bool = False
    switchheater_heat_time_s: float = None
    switchheater_cool_time_s: float = None
    switchheater_current_A: float = None
    persisten_current_rampe_rate_Apers: float = None

    @property
    def coil_constant_TperA(self) -> float:
        return self.field_limit_T / self.current_limit_A

    @property
    def max_rampr_rate_Tpers(self) -> float:
        return self.coil_constant_TperA * self.ramp_rate_limit_Apers

    @property
    def stability_parameter(self) -> float:
        if self.has_switchheater:
            return 0.0
        return 100.0 - self.inductance_H

    @property
    def expected_current_ramptime_cold_switch_s(self) -> float:
        assert self.has_switchheater
        return self.current_limit_A / self.persisten_current_rampe_rate_Apers

    def consistency_check(self) -> None:
        if self.has_switchheater:
            assert isinstance(self.switchheater_heat_time_s, float)
            assert isinstance(self.switchheater_cool_time_s, float)
            assert isinstance(self.switchheater_current_A, float)
            assert isinstance(self.persisten_current_rampe_rate_Apers, float)


@dataclass(frozen=True)
class Station:
    name: str
    validate_field_limit: Callable
    z_axis: Magnet
    y_axis: Magnet
    x_axis: Optional[Magnet] = None
    use_visa_simulation: bool = False

    @property
    def axis(self) -> Axis:
        return Axis.AXIS2 if self.x_axis is None else Axis.AXIS3
