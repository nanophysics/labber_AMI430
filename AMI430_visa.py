import pathlib
import logging
from enum import Enum, IntEnum
from typing import Any, Iterable, Iterator, List, Dict

import pyvisa
import pyvisa.constants as vi_const
import pyvisa.resources

from AMI430_utils import Station, Magnet, Axis
from AMI430_driver_utils import EnumMixin

logger = logging.getLogger("LabberDriver")

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
FILENAME_VISA_SIM = DIRECTORY_OF_THIS_FILE / "AMI430_simulation.yaml"
assert FILENAME_VISA_SIM.exists()

_VISA_TERMINATOR = "\n"


class AMI430State(EnumMixin, IntEnum):
    RAMPING = 1
    HOLDING = 2
    PAUSED = 3
    MANUAL_UP = 4
    MANUAL_DOWN = 5
    ZEROING_CURRENT = 6
    QUENCH_DETECTED = 7
    AT_ZERO_CURRENT = 8
    HEATING_SWITCH = 9
    COOLING_SWITCH = 10

    @property
    def labber_state(self) -> "LabberState":
        return {
            AMI430State.RAMPING: LabberState.RAMPING,
            AMI430State.HOLDING: LabberState.HOLDING,
            AMI430State.PAUSED: LabberState.PAUSED,
            AMI430State.ZEROING_CURRENT: LabberState.IDLE,
            AMI430State.AT_ZERO_CURRENT: LabberState.IDLE,
        }.get(self, LabberState.ERROR)


class LabberState(EnumMixin, IntEnum):
    RAMPING = 1
    HOLDING = 2
    PAUSED = 3
    IDLE = 4
    # OFF = 5
    MISALIGNED = 6
    ERROR = 7

    @classmethod
    def set_by_labber(cls) -> List["LabberState"]:
        return [cls.RAMPING, cls.PAUSED, cls.OFF]

    @classmethod
    def set_by_magnet(cls) -> List["LabberState"]:
        return [cls.HOLDING, cls.IDLE]


class VisaStation:
    def __init__(self, station: Station):
        self.station = station
        self.visa_magnet_x: "VisaMagnet" = None
        self.visa_magnet_y: "VisaMagnet" = None
        self.visa_magnet_z: "VisaMagnet" = None

    @property
    def visa_magnets(self) -> Iterable["VisaMagnet"]:
        yield self.visa_magnet_x
        yield self.visa_magnet_y
        if self.visa_magnet_z is not None:
            yield self.visa_magnet_z

    @property
    def labber_state(self) -> LabberState:
        states = {magnet.get_visa_state() for magnet in self.visa_magnets}
        if len(states) > 1:
            logger.info(f"LabberState.MISALIGNED: {states}")
            return LabberState.MISALIGNED
        assert len(states) == 1
        state = states.pop()
        assert isinstance(state, AMI430State)
        return state.labber_state

    @labber_state.setter
    def labber_state(self, state) -> None:
        self._labber_state = state

    def open(self) -> None:
        def add_magnet(magnet: Magnet, name: str):
            assert magnet is not None
            assert isinstance(magnet, Magnet)
            assert isinstance(name, str)
            visa_magnet = VisaMagnet(visa_station=self, magnet=magnet, name=name)
            visa_magnet.open()
            return visa_magnet

        self.visa_magnet_x = add_magnet(self.station.x_axis, name="X")
        self.visa_magnet_y = add_magnet(self.station.y_axis, name="Y")
        if self.station.axis == Axis.AXIS3:
            self.visa_magnet_z = add_magnet(self.station.z_axis, name="Z")

    def close(self) -> None:
        for visa_magnet in self.visa_magnets:
            visa_magnet.close()

    def ramping(self) -> None:
        for visa_magnet in self.visa_magnets:
            visa_magnet.ramping()


class VisaMagnet:
    def __init__(self, visa_station: VisaStation, magnet: Magnet, name: str):
        self.visa_station = visa_station
        self.magnet = magnet
        self.name = name
        self.visa_handle: pyvisa.resources.MessageBasedResource = None
        self.visa_log = logger
        self.field_setpoint_Tesla: float = 0.0
        self.field_ramp_TeslaPers: float = 0.0

    @property
    def use_visa_simulation(self) -> bool:
        return self.visa_station.station.use_visa_simulation

    @property
    def visalib(self) -> str:
        """
        visalib: Visa backend to use when connecting to this instrument.
            This should be in the form of a string '<pathtofile>@<backend>'.
            Both parts can be omitted and pyvisa will try to infer the
            path to the visa backend file.
            By default the IVI backend is used if found, but '@py' will use the
            ``pyvisa-py`` backend. Note that QCoDeS does not install (or even require)
            ANY backends, it is up to the user to do that. see eg:
            http://pyvisa.readthedocs.org/en/stable/names.html
        """
        if self.use_visa_simulation:
            return f"{FILENAME_VISA_SIM}@sim"
        return "@py"

    def open(self) -> None:
        resource_manager = pyvisa.ResourceManager(self.visalib)
        resources = resource_manager.list_resources()

        self.visa_handle = resource_manager.open_resource(
            self.magnet.ip_address, read_termination="\n"
        )
        assert isinstance(self.visa_handle, pyvisa.resources.MessageBasedResource)

        self._visa_clear()
        self._visa_init()

    def close(self) -> None:
        if self.visa_handle is not None:
            self.visa_handle.close()
            self.visa_handle = None

    def _visa_clear(self) -> None:
        self.visa_handle.write_termination = _VISA_TERMINATOR
        self.visa_handle.read_termination = _VISA_TERMINATOR

        if self.use_visa_simulation:
            return

        self.visa_handle.clear()

    def _visa_init(self) -> None:
        """
        Initialize everything.
        For example the units we are going to use.
        """
        # self.ask_raw("IDN?")
        self.ask_raw("*IDN?")
        self.ask_raw("COIL?", astype=float)
        self.ask_raw("STATE?", astype=AMI430State.from_visa)
        # print(visa_handle.query("*IDN?"))
        # print(visa_handle.query("?FIELD:UNITS"))
        # print(f"{self.name}: " + self.visa_handle.query("COIL?"))
        # print(f"{self.name}: " + self.visa_handle.query("FIELD:MAG?"))
        # print(f"{self.name}: " + self.visa_handle.query("STATE?"))
        # print(f"{self.name}: " + self.visa_handle.query("?IDN"))

    def ramping(self) -> None:
        self.write_raw("RAMP")

    @property
    def visa_state(self) -> AMI430State:
        return self.ask_raw("STATE?", astype=AMI430State.from_visa)

    @property
    def visa_error(self) -> AMI430State:
        # TODO: What will be returned?
        return self.ask_raw("SYST:ERR?", astype=int)

    def write_raw(self, cmd: str) -> None:
        """
        Low-level interface to ``visa_handle.write``.

        Args:
            cmd: The command to send to the instrument.
        """
        self.debug(f"Writing: {cmd}")
        self.visa_handle.write(cmd)

    def ask_raw(self, cmd: str, astype=None) -> Any:
        """
        Low-level interface to ``visa_handle.ask``.

        Args:
            cmd: The command to send to the instrument.

        Returns:
            The instrument's response.
        """
        self.debug(f"Querying: {cmd}")
        response = self.visa_handle.query(cmd)
        if astype is None:
            self.debug(f"Response: '{response}'")
            return response
        response_type = astype(response)
        self.debug(f"Response: {repr(response_type)}")
        return response_type

    def debug(self, msg: str) -> None:
        self.visa_log.debug(f"{self.name} {msg}")


def main():
    from AMI430_driver_config_simulation import get_station

    logging.basicConfig()
    logger.setLevel(logging.DEBUG)

    station = get_station()
    visa_station = VisaStation(station=station)
    visa_station.open()
    visa_station.visa_magnet_x.field_setpoint = 2.0
    visa_station.visa_magnet_y.field_setpoint = 3.0
    visa_station.visa_magnet_z.field_setpoint = 4.0
    visa_station.ramping()


if __name__ == "__main__":
    main()
