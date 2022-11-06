from decimal import DivisionByZero
import pathlib
import logging
import time
import enum
from typing import Any, Set, List, Optional
import os
from xmlrpc.client import Boolean
import pyvisa
import pyvisa.resources

from AMI430_utils import Station, Magnet, Axis
from AMI430_driver_utils import EnumLogging, EnumMixin
from AMI430_driver_utils import Quantity

logger = logging.getLogger("LabberDriver")

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
FILENAME_VISA_SIM = DIRECTORY_OF_THIS_FILE / "AMI430_simulation.yaml"
assert FILENAME_VISA_SIM.exists()

_VISA_TERMINATOR = "\n"


class LoggerTags(EnumMixin, enum.Enum):
    MAGNET_FIELD = enum.auto()
    MAGNET_STATE = enum.auto()
    LABBER_STATE = enum.auto()
    AMI430State = enum.auto()
    MAGNET_RAMPING_STATE = enum.auto()
    LABBER_SET = enum.auto()
    STATION_RAMPING_STATE = enum.auto()
    RAMPING_DURATION_S = enum.auto()

    @classmethod
    def general_properties(cls) -> Set["LoggerTags"]:
        return {
            cls.LABBER_SET,
            cls.LABBER_STATE,
            cls.STATION_RAMPING_STATE,
            cls.RAMPING_DURATION_S,
        }


# class SwitchHeaterState(EnumMixin, enum.IntEnum):
#     OFF = 0
#     ON = 1

# @classmethod
# def from_text(cls, vlaue: str) -> int:
#     'Function to translate txt to number'
#     return SwitchHeaterState.te


class AMI430State(EnumMixin, enum.Enum):
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


class LabberState(EnumMixin, enum.Enum):
    RAMPING = 1
    HOLDING = 2
    PAUSED = 3
    IDLE = 4
    MISALIGNED = 5
    ERROR = 6

    @classmethod
    def valid_set_by_labber(cls) -> Set["LabberState"]:
        return {cls.RAMPING, cls.PAUSED, cls.OFF}


class ControlMode(EnumMixin, enum.Enum):
    # ATTENTION: These values HAVE TO correspond with the
    # values in AMI430_driver.ini, but -1
    PASSIVE = 0
    RAMPING_WAIT = 1


class MagnetRampingState(enum.Enum):
    INIT = 1
    WAITFOR_CURRENT = 2
    WAITFOR_SWITCH_WARM = 3
    WAITFOR_HOLDING = 4
    WAITFOR_SWITCH_COLD = 5
    WAITFOR_ZERO_CURRENT = 6
    DONE = 7


class RampingStatemachineMagnet:
    def __init__(self, visa_magnet: "VisaMagnet"):
        self._visa_magnet = visa_magnet
        self._state: MagnetRampingState = MagnetRampingState.INIT
        self._timeout = time.time()

        logger.debug(
            self.prefix(
                f"Magnet {self._visa_magnet.name}: Start ramping to {self._visa_magnet.field_setpoint_Tesla} T"
            )
        )
        if self._visa_magnet.field_actual_Tesla is not None:
            if (
                abs(
                    self._visa_magnet.field_setpoint_Tesla
                    - self._visa_magnet.field_actual_Tesla
                )
                < 1e-12
            ):
                # if self._visa_magnet.visa_state == AMI430State.HOLDING:
                #     logger.info(self.prefix("Field already at setpoint: Skip ramp"))
                #     self._state = MagnetRampingState.DONE
                #     return
                # if self._visa_magnet.magnet.has_switchheater:

                #     if self._visa_magnet.visa_station.holding_current:
                #         logger.info(
                #             self.prefix(
                #                 "Field already at setpoint with switch warm and holding current: Skip ramp"
                #             )
                #         )
                #         self._state = MagnetRampingState.DONE
                #         return
                #     if not self._visa_magnet.visa_station.holding_switchheater_on:
                #         if self._visa_magnet.visa_state == AMI430State.AT_ZERO_CURRENT:
                #             logger.info(
                #                 self.prefix(
                #                     "Field already at setpoint with cold switch: Skip ramp"
                #                 )
                #             )
                #             self._state = MagnetRampingState.DONE
                #             return
                if self._visa_magnet.magnet.has_switchheater:
                    if self._visa_magnet.visa_station.holding_current:
                        if self._visa_magnet.visa_station.holding_switchheater_on:
                            if self._visa_magnet.switchheater_state:
                                self._state = MagnetRampingState.DONE
                                logger.info(
                                    self.prefix(
                                        "Field already at setpoint with switch warm and holding current: Skip ramp"
                                    )
                                )
                                # return
                        if not self._visa_magnet.switchheater_state:
                            self._state = MagnetRampingState.DONE
                            logger.info(
                                self.prefix(
                                    "Field already at setpoint with switch cold: Skip ramp"
                                )
                            )
                            # return
                    if not self._visa_magnet.visa_station.holding_current:
                        if not self._visa_magnet.switchheater_state:
                            logger.info(
                                self.prefix("We are checking if at zero current is ok")
                            )
                            if (
                                self._visa_magnet.visa_state
                                == AMI430State.AT_ZERO_CURRENT
                            ):
                                self._state = MagnetRampingState.DONE
                                logger.info(
                                    self.prefix(
                                        "Field already at setpoint with switch cold and zero current: Skip ramp"
                                    )
                                )
                                # return
                else:
                    if self._visa_magnet.visa_state == AMI430State.HOLDING:
                        logger.info(self.prefix("Field already at setpoint: Skip ramp"))
                        self._state = MagnetRampingState.DONE
                        # return
        # return

        # self._visa_magnet.ensure_switch_on()

    def is_done(self):
        return self._state == MagnetRampingState.DONE

    def prefix(self, msg) -> str:
        return self._visa_magnet.prefix(msg)

    @property
    def magnet(self) -> "Magnet":
        return self._visa_magnet.magnet

    @property
    def statetext(self) -> str:
        return f"{self._visa_magnet.name}-{self._state.name}"

    def tick(self):
        state_before = self._state
        self._tick()
        state_after = self._state
        if state_before != state_after:
            logger.debug(
                self.prefix(
                    f"{state_before.name} -> {state_after.name}, timeout {self._timeout - time.time():0.1f} s"
                )
            )

    def _tick(self):
        def start_ramping():
            self._visa_magnet.write_raw("PAUSE")
            self._visa_magnet.visa_state
            logger.info(self.prefix("Field Ramp"))
            # self._visa_magnet.write_raw("CONF:RAMP:RATE:SEG 1")
            self._visa_magnet.write_raw(
                f"CONF:RAMP:RATE:FIELD 1,{self._visa_magnet.field_ramp_TeslaPers:f},0"
            )
            self._visa_magnet.write_raw(
                f"CONF:FIELD:TARG {self._visa_magnet.field_setpoint_Tesla:f}"
            )
            time.time() + self._visa_magnet.expected_ramp_duration_s * 1.5

            self._visa_magnet.write_raw("RAMP")

        if self._state == MagnetRampingState.INIT:
            if not self.magnet.has_switchheater:
                start_ramping()
                self._state = MagnetRampingState.WAITFOR_HOLDING
                return

            if self._visa_magnet.ask_raw("PS?", astype=int) == 1:
                # this assumes that the switch is already heated we neglect to wait for swith to warm and directly set the paused state
                self._visa_magnet.write_raw("PAUSE")
                self._state = MagnetRampingState.WAITFOR_SWITCH_WARM
                return

            # We are at zero current: Match supply and magnet current!
            self._visa_magnet.write_raw("RAMP")
            self._timeout = (
                time.time() + self.magnet.expected_current_ramptime_cold_switch_s * 1.5
            )
            logger.info(
                f"{LoggerTags.MAGNET_STATE.name} {self._visa_magnet.name} {self._visa_magnet.visa_state.name} {self._visa_magnet.visa_state.value}"
            )

            self._state = MagnetRampingState.WAITFOR_CURRENT
            return

        if self._state == MagnetRampingState.WAITFOR_CURRENT:
            if self._visa_magnet.visa_state == AMI430State.HOLDING:
                self._visa_magnet.write_raw(
                    "PS 1"
                )  # Persistent switch heater ON (heat up)
                self._timeout = (
                    time.time() + self.magnet.switchheater_heat_time_s + 10.0
                )
                self._state = MagnetRampingState.WAITFOR_SWITCH_WARM
                return
            return

        if self._state == MagnetRampingState.WAITFOR_SWITCH_WARM:
            if self._visa_magnet.visa_state == AMI430State.PAUSED:
                start_ramping()
                self._state = MagnetRampingState.WAITFOR_HOLDING
                return
            return

        if self._state == MagnetRampingState.WAITFOR_HOLDING:
            if self._visa_magnet.visa_state == AMI430State.HOLDING:
                self._visa_magnet.field_actual_Tesla = (
                    self._visa_magnet.field_setpoint_Tesla
                )
                if not self.magnet.has_switchheater:
                    self._state = MagnetRampingState.DONE
                    return
                if self._visa_magnet.visa_station.holding_switchheater_on:
                    self._state = MagnetRampingState.DONE
                    return
                logger.info(self.prefix("Persistent switch cooling"))
                self._visa_magnet.write_raw(
                    "PS 0"
                )  # Persistent switch heater OFF (cool down)
                self._timeout = (
                    time.time() + self.magnet.switchheater_cool_time_s + 10.0
                )
                self._state = MagnetRampingState.WAITFOR_SWITCH_COLD
            return

        if self._state == MagnetRampingState.WAITFOR_SWITCH_COLD:
            if (
                self._visa_magnet.visa_state == AMI430State.PAUSED
            ):  # changed to PAUSED from HOLDING
                if self._visa_magnet.visa_station.holding_current:
                    self._state = MagnetRampingState.DONE
                    return

                logger.info(self.prefix("Current zeroing"))

                self._visa_magnet.write_raw("ZERO")
                logger.info(
                    f"{LoggerTags.MAGNET_STATE.name} {self._visa_magnet.name} {self._visa_magnet.visa_state.name} {self._visa_magnet.visa_state.value}"
                )
                self._state = MagnetRampingState.WAITFOR_ZERO_CURRENT
                self._timeout = (
                    time.time()
                    + self.magnet.expected_current_ramptime_cold_switch_s * 1.5
                )
                return

            if time.time() > self._timeout:
                raise Exception("Timeout")
            return
        if self._state == MagnetRampingState.WAITFOR_ZERO_CURRENT:
            if self._visa_magnet.visa_state == AMI430State.AT_ZERO_CURRENT:
                logger.info(
                    f"{LoggerTags.MAGNET_STATE.name} {self._visa_magnet.name} {self._visa_magnet.visa_state.name} {self._visa_magnet.visa_state.value}"
                )
                self._state = MagnetRampingState.DONE
                return
            if time.time() > self._timeout:
                raise Exception("Timeout")
            return
        assert self._state == MagnetRampingState.DONE


class RampingStatemachineStation:
    """
    Order magnets by ramp direccion
    For each magnet
    - send command: ramp
    - wait for status HOLIDING
    - send command: cool down switch
    - wait for status ...
    - send command: zero current
    - wait for status ...
    """

    def __init__(self, visa_station: "VisaStation"):
        self._visa_station = visa_station
        self._magnets_to_be_ramped: List[VisaMagnet] = []
        self._current_magnet: Optional[RampingStatemachineMagnet] = None
        self.done = True

    def start_ramping(self):
        "List of magnets waiting for there field to be ramped."
        self.done = False

        tmp_magnets = []
        for visa_magnet in self._visa_station.visa_magnets:
            current_field_T = visa_magnet.visa_field_T
            set_field_T = visa_magnet.field_setpoint_Tesla
            increment_T = set_field_T - current_field_T
            # if abs(increment_T) > 1e-6:
            tmp_magnets.append((increment_T, visa_magnet))
        tmp_magnets.sort()
        for _, visa_magnet in tmp_magnets:
            self._magnets_to_be_ramped.append(visa_magnet)

    @property
    def statetext(self) -> str:
        states = [visa_magnet.name for visa_magnet in self._magnets_to_be_ramped]
        if self._current_magnet is not None:
            states.insert(0, self._current_magnet.statetext)
        return ",".join(states)

    def tick(self):
        "process next step"
        if self._current_magnet is None:
            if len(self._magnets_to_be_ramped) == 0:
                # We are done: All magnets reached the new field and
                # are in state HOLDING
                self.done = True
                return

            # Lets ramp the field of the next magnet
            self._current_magnet = RampingStatemachineMagnet(
                visa_magnet=self._magnets_to_be_ramped.pop(0)
            )

        self._current_magnet.tick()

        if self._current_magnet.is_done():
            self._current_magnet = None


class VisaStation:
    def __init__(self, station: Station):
        self._logging = EnumLogging.DEBUG

        self.holding_switchheater_on: bool = True
        "Only relavant for the magnet with switchheader"
        self.holding_current = True
        "Only relavant for the magnet with switchheader"

        self.station = station
        self.visa_magnet_x: "VisaMagnet" = None
        self.visa_magnet_y: "VisaMagnet" = None
        self.visa_magnet_z: "VisaMagnet" = None
        self._state_machine: RampingStatemachineStation = RampingStatemachineStation(
            visa_station=self
        )
        self._mode: ControlMode = ControlMode.PASSIVE
        self.init_logger()

    def init_logger(self) -> None:
        logfile = DIRECTORY_OF_THIS_FILE / f"tmp_AMI430_{self.station.name}.log"
        fh = logging.FileHandler(logfile)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    @property
    def visa_magnets(self) -> List["VisaMagnet"]:
        return [
            visa_magnet
            for visa_magnet in (
                self.visa_magnet_x,
                self.visa_magnet_y,
                self.visa_magnet_z,
            )
            if visa_magnet is not None
        ]

    @property
    def statetext(self) -> str:
        return self._state_machine.statetext

    def get_labber_state(self) -> LabberState:
        if not self._state_machine.done:
            return LabberState.MISALIGNED

        def fix_state(visa_magnet: VisaMagnet) -> AMI430State:
            logger.info("We are checking if we can terminate the statemachine")
            logger.info(
                f"****************************The relevant variables are Switchheater yes/no {visa_magnet.magnet.has_switchheater}Hold current yes/no {visa_magnet.visa_station.holding_current} Hold switchheater yes/no {visa_magnet.visa_station.holding_switchheater_on}"
            )
            if visa_magnet.magnet.has_switchheater:
                if not visa_magnet.visa_station.holding_current:
                    if visa_magnet.visa_state is AMI430State.AT_ZERO_CURRENT:
                        return AMI430State.HOLDING
                if not visa_magnet.visa_station.holding_switchheater_on:
                    if visa_magnet.visa_state is AMI430State.PAUSED:
                        return AMI430State.HOLDING
            return visa_magnet.visa_state

        states = {fix_state(magnet) for magnet in self.visa_magnets}
        if len(states) > 1:
            logger.info(f"LabberState.MISALIGNED: {states}")
            return LabberState.MISALIGNED
        assert len(states) == 1
        state = states.pop()
        assert isinstance(state, AMI430State)
        return state.labber_state

    def start_ramping(self) -> None:
        self._state_machine.start_ramping()

    def tick(self) -> None:
        textstate_before = self.statetext

        while True:
            self._state_machine.tick()
            textstate_after = self.statetext
            if textstate_before == textstate_after:
                # logger.debug(f"Slowlane textstate_after={textstate_after}")
                break
            logger.debug(
                f"Fastlane textstate_before={textstate_before} -> textstate_after={textstate_after}"
            )
            textstate_before = textstate_after

    def open(self, initialize_visa=True) -> None:
        def add_magnet(magnet: Magnet, name: str):
            assert magnet is not None
            assert isinstance(magnet, Magnet)
            assert isinstance(name, str)
            visa_magnet = VisaMagnet(visa_station=self, magnet=magnet, name=name)
            if initialize_visa:
                visa_magnet.open()
            return visa_magnet

        if self.station.axis == Axis.AXIS3:
            self.visa_magnet_x = add_magnet(self.station.x_axis, name="X")
        self.visa_magnet_y = add_magnet(self.station.y_axis, name="Y")
        self.visa_magnet_z = add_magnet(self.station.z_axis, name="Z")

    def close(self) -> None:
        for visa_magnet in self.visa_magnets:
            visa_magnet.close()

    def set_quantity(self, quantity: Quantity, value):
        value_new = self._set_quantity(quantity, value)
        logger.info(f"{LoggerTags.LABBER_SET.name} {quantity.name} {value} {value_new}")
        return value_new

    def _set_quantity(self, quantity: Quantity, value):
        visa_magnet = self.quantity_setpoint_field.get(quantity, None)
        if visa_magnet is not None:
            assert isinstance(value, float)
            visa_magnet.field_setpoint_Tesla = value
            return value

        visa_magnet = self.quantity_setpoint_ramp.get(quantity, None)
        if visa_magnet is not None:
            assert isinstance(value, float)
            max_ramp_Tpers = visa_magnet.magnet.max_rampr_rate_Tpers
            if value <= max_ramp_Tpers:
                visa_magnet.field_ramp_TeslaPers = value
                return value

            logger.warning(
                f"Maximum Ramp rate clipped from {value:0.4f} T/s to {max_ramp_Tpers:0.4f} T/s."
            )
            return max_ramp_Tpers

        if quantity is Quantity.ControlLogging:
            self._logging = EnumLogging.get_exception(value)
            return value
        if quantity is Quantity.ControlMode:
            self._mode = ControlMode.get_valuelabber_exception(value)
            return value
        if quantity is Quantity.StatusSwitchheaterStatus:
            # TODO
            v_dict = {"ON": True, "OFF": False}
            # return self.switchheater_status = v_dict[value]
            return value
        if quantity is Quantity.ControlHoldSwitchheaterOn:
            v_dict = {"True": 1, "False": 0}
            # self.holding_switchheater_on = v_dict[value]
            if isinstance(value, str):
                value = v_dict[value]
            self.holding_switchheater_on = abs(value) > 0.5
            return value
            # self.holding_switchheater_on = abs(value)> 0.5
            # return value 
        if quantity is Quantity.ControlHoldCurrent:
            v_dict = {"True": 1, "False": 0}
            if isinstance(value, str):
                value = v_dict[value]
            self.holding_current = abs(value) > 0.5
            return value

        if quantity is Quantity.ControlLabberState:

            # if isinstance(value, float):
            #     # The measurement windows seems to send a float, but a text of the state was expected...
            #     value_float = value
            #     value = LabberState(int(value_float) + 1).name
            #     logger.info(
            #         f"Hack: Converted {Quantity.ControlLabberState.name} {value_float} -> {value}"
            #     )

            def action():
                if value == LabberState.RAMPING.name:
                    self.start_ramping()
                    return

                logger.warning(
                    f"set_quantity: quantity={quantity.name}: can not set state {value}"
                )

            action()
            return self.get_labber_state().name

        raise Exception(f"set_quantity(): Unknown quantity '{quantity.name}' {value}")

    def wait_till_ramped(self):
        self.station.validate_field_limit(visa_station=self)
        self.start_ramping()
        start_s = time.time()
        while True:
            labber_state = (
                self.get_labber_state()
            )  # we change the order here to observe if this changes something.
            self.tick()
            logger.info(f"Status of the RampingStatemachine {self._state_machine.done}")
            logger.info(f"{LoggerTags.LABBER_STATE.name} {labber_state.name}")
            logger.info(
                f"{LoggerTags.RAMPING_DURATION_S.name} {time.time()-start_s:0.3} {self.statetext}"
            )
            if labber_state == LabberState.HOLDING:
                break
            if not labber_state in (LabberState.RAMPING, LabberState.MISALIGNED):
                logger.warning(f"Unexected labber state '{labber_state.name}'")
            for magnet in self.visa_magnets:
                magnet.visa_field_T

            logger.info(f"RAMPING WAIT: {time.time()-start_s:0.3}s {self.statetext}")
            time.sleep(1.0)

    @property
    def switchheater_state(self) -> int:
        visa_magnet = self.visa_magnet_z
        if visa_magnet is None:
            return 0
        if not visa_magnet.magnet.has_switchheater:
            return 0
        return visa_magnet.switchheater_state

    def get_quantity(self, quantity: Quantity) -> Any:
        assert isinstance(quantity, Quantity)
        if quantity is Quantity.ConfigName:
            return self.station.name
        if quantity is Quantity.ConfigAxis:
            return self.station.axis.name
        if quantity is Quantity.ControlLogging:
            return self._logging.value
        if quantity is Quantity.StatusSwitchheaterStatus:
            return self.switchheater_state
        if quantity is Quantity.ControlHoldSwitchheaterOn:
            return self.holding_switchheater_on
        if quantity is Quantity.ControlHoldCurrent:
            return self.holding_current
        if quantity is Quantity.ControlLabberState:
            return self.get_labber_state().name
        if quantity is Quantity.ControlMode:
            return self._mode.name

        visa_maget = self.quantity_setpoint_field.get(quantity, None)
        if visa_maget is not None:
            return visa_maget.field_setpoint_Tesla

        visa_maget = self.quantity_setpoint_ramp.get(quantity, None)
        if visa_maget is not None:
            return visa_maget.field_ramp_TeslaPers

        visa_maget = self.quantity_magnet_state.get(quantity, None)
        if visa_maget is not None:
            return visa_maget.visa_state.name

        visa_maget = self.quantity_magnet_field_actual.get(quantity, None)
        if visa_maget is not None:
            return visa_maget.visa_field_T

        raise Exception(f"get_quantity(): Unknown quantity '{quantity.name}'")

    @property
    def quantity_setpoint_ramp(self):
        return {
            Quantity.ControlRampRateX: self.visa_magnet_x,
            Quantity.ControlRampRateY: self.visa_magnet_y,
            Quantity.ControlRampRateZ: self.visa_magnet_z,
        }

    @property
    def quantity_setpoint_field(self):
        return {
            Quantity.ControlSetpointX: self.visa_magnet_x,
            Quantity.ControlSetpointY: self.visa_magnet_y,
            Quantity.ControlSetpointZ: self.visa_magnet_z,
        }

    @property
    def quantity_magnet_state(self):
        return {
            Quantity.StatusMagnetStateX: self.visa_magnet_x,
            Quantity.StatusMagnetStateY: self.visa_magnet_y,
            Quantity.StatusMagnetStateZ: self.visa_magnet_z,
        }

    @property
    def quantity_magnet_field_actual(self):
        return {
            Quantity.StatusFieldActualX: self.visa_magnet_x,
            Quantity.StatusFieldActualY: self.visa_magnet_y,
            Quantity.StatusFieldActualZ: self.visa_magnet_z,
        }


class VisaMagnet:
    def __init__(self, visa_station: VisaStation, magnet: Magnet, name: str):
        self.visa_station = visa_station
        self.magnet = magnet
        self.name = name
        self.visa_handle: pyvisa.resources.MessageBasedResource = None

        self.field_actual_Tesla: float = None
        "This is the field which is currently set"
        self.field_setpoint_Tesla: float = 0.0
        "This field should be set when calling ramp"
        self.field_ramp_TeslaPers: float = 0.0

        magnet.consistency_check()

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
        # return "@ivi"
        return "@py"

    @property
    def expected_ramp_duration_s(self) -> float:
        try:
            return self.field_setpoint_Tesla / self.field_ramp_TeslaPers
        except (ZeroDivisionError, DivisionByZero):
            return 2 * 60 * 60

    @property
    def switchheater_state(self) -> int:
        assert self.magnet.has_switchheater
        return self.ask_raw("PS?", astype=int)

    # @switchheater_state.setter
    # def switchheater_state(self, state: str) -> None:
    #     assert self.magnet.has_switchheater

    # self.write_raw(f"PS {SwitchHeaterState[state].value}")

    def open(self) -> None:
        resource_manager = pyvisa.ResourceManager(self.visalib)
        resources = resource_manager.list_resources()

        self.visa_handle = resource_manager.open_resource(
            self.magnet.ip_address, read_termination="\n"
        )
        assert isinstance(self.visa_handle, pyvisa.resources.MessageBasedResource)

        self._visa_clear()
        self._visa_init()

    def prefix(self, msg) -> str:
        return f"{self.name}: {msg}"

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

        # the AMI 430 sends a welcome message of
        # 'American Magnetics Model 430 IP Interface'
        # 'Hello'
        # here we read that out before communicating with the instrument
        # if that is not the first reply likely there is left over messages
        # in the buffer so read until empty
        message1 = self.visa_handle.read()
        if "American Magnetics Model 430 IP Interface" in message1:
            # read the hello part of the welcome message
            self.visa_handle.read()
            return

        try:
            # swallow all date from the previous session
            while True:
                self.visa_handle.read()
        except pyvisa.VisaIOError:
            pass

    def _visa_init(self) -> None:
        """
        Initialize everything.
        For example the units we are going to use.
        """

        idn = self.ask_raw("*IDN?")

        # Choose field units in Tesla and ramp units in seconds
        self.write_raw("CONF:FIELD:UNITS 1")
        self.write_raw("CONF:RAMP:RATE:UNITS 0")
        self.write_raw(f"CONF:COIL {self.magnet.coil_constant_TperA:f}")
        self.write_raw(f"CONF:CURR:LIMIT {self.magnet.current_limit_A:f}")
        self.write_raw(f"CONF:IND {self.magnet.inductance_H:f}")
        self.write_raw(f"CONF:STAB {self.magnet.stability_parameter:f}")
        # TODO(benedikt)
        self.write_raw("CONF:RAMP:RATE:SEG 1")
        self.write_raw("CONF:RAMP:RATE:FIELD 1,0.001,0")
        if self.magnet.has_switchheater:
            self.write_raw("CONF:PS 1")
            self.write_raw(f"CONF:PS:HTIME {self.magnet.switchheater_heat_time_s:f}")
            self.write_raw(f"CONF:PS:CTIME {self.magnet.switchheater_cool_time_s:f}")
            # Datasheet ...: mA
            self.write_raw(
                f"CONF:PS:CURR {self.magnet.switchheater_current_A*1000.0:f}"
            )
            self.write_raw(
                f"CONF:PS:PSRR {self.magnet.persisten_current_rampe_rate_Apers:f}"
            )
        else:
            self.write_raw("CONF:PS 0")

    def wait_for_state(
        self,
        transition_state: AMI430State,
        final_state: AMI430State,
        max_timeout_s=10.0,
        sleep_s=4.0,
    ) -> None:
        begin_s = time.time()
        while True:
            print(f"wait_for_state SLEEP {sleep_s}")

            time.sleep(sleep_s)
            visa_state = self.visa_state
            if self.visa_state != transition_state:
                break
            duration_s = time.time() - begin_s
            msg = f"Timeout after waiting for {max_timeout_s}s for {final_state.name}. Current state {visa_state.name}"
            if duration_s > max_timeout_s:
                raise Exception(msg)
        assert self.visa_state == final_state

    @property
    def visa_field_T(self) -> float:
        field_T = self.ask_raw("FIELD:MAG?", astype=float)
        logger.info(f"{LoggerTags.MAGNET_FIELD.name} {self.name} {field_T}")
        return field_T

    @property
    def visa_current_magnet_A(self) -> float:
        return self.ask_raw("CURR:MAG?", astype=float)

    @property
    def visa_current_supply_A(self) -> float:
        return self.ask_raw("CURR:SUPP?", astype=float)

    @property
    def visa_state(self) -> AMI430State:
        state = self.ask_raw("STATE?", astype=AMI430State.from_visa)
        logger.info(
            f"{LoggerTags.MAGNET_STATE.name} {self.name} {state.name} {state.value}"
        )
        return state

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
        logger.debug(self.prefix(f"Writing: {cmd}"))
        self.visa_handle.write(cmd)

    def ask_raw(self, cmd: str, astype=None) -> Any:
        response = self._ask_raw(cmd=cmd, astype=astype)
        logger.debug(self.prefix(f"ask_raw: '{cmd}' -> {response!r}"))
        return response

    def _ask_raw(self, cmd: str, astype=None) -> Any:
        """
        Low-level interface to ``visa_handle.ask``.

        Args:
            cmd: The command to send to the instrument.

        Returns:
            The instrument's response.
        """
        # logger.debug(self.prefix(f"Querying: {cmd}"))
        response = self.visa_handle.query(cmd)
        if astype is None:
            # logger.debug(self.prefix(f"Response: '{response}'"))
            return response
        try:
            response_type = astype(response)
        except Exception as e:
            raise Exception(f"_ask_raw({cmd!r}, {astype!r}") from e
        # logger.debug(self.prefix(f"Response: {repr(response_type)}"))
        return response_type

    def debug(self, msg: str) -> None:
        self.visa_log.debug(f"{self.name} {msg}")

    def info(self, msg: str) -> None:
        self.visa_log.info(f"{self.name} {msg}")


def main():
    from AMI430_driver_config_sofia import get_station

    logging.basicConfig()
    logger.setLevel(logging.DEBUG)

    station = get_station()
    visa_station = VisaStation(station=station)
    visa_station.open()
    visa_station.visa_magnet_z.magnet.has_switchheater
    visa_station.visa_magnet_x.magnet.has_switchheater
    if False:
        visa_station.visa_magnet_y.field_setpoint_Tesla = 0.01
        visa_station.visa_magnet_y.field_ramp_TeslaPers = 0.001
        visa_station.visa_magnet_y.ramping()
        visa_magnet = visa_station.visa_magnet_y

    # visa_station.set_quantity(Quantity.ControlMode, "PASSIVE")
    return
    t0 = time.time()
    visa_station.start_ramping()
    while True:
        if visa_station.get_labber_state() == LabberState.HOLDING:
            print("Elapsed time:", time.time() - t0)
            break

        print(f"visa_station.get_labber_state {visa_station.get_labber_state().name}")
        print(
            f"y={visa_station.visa_magnet_y.visa_field_T:0.3f}T z={visa_station.visa_magnet_z.visa_field_T:0.3f}T"
        )
        visa_station.tick()
        time.sleep(1.0)

    t0 = time.time()
    visa_station.start_ramping()

    while True:
        visa_station.tick()
        print(" Labber State", visa_station.get_labber_state())
        if visa_station.get_labber_state() == LabberState.HOLDING:
            print(
                "****************************************************************Elapsed time:",
                time.time() - t0,
            )
            break

        print(f"visa_station.get_labber_state {visa_station.get_labber_state().name}")
        print(
            f"y={visa_station.visa_magnet_y.visa_field_T:0.3f}T z={visa_station.visa_magnet_z.visa_field_T:0.3f}T"
        )
        print(" SLEEP")
        time.sleep(1.0)


if __name__ == "__main__":
    main()
