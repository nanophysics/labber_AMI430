import enum
import logging

logger = logging.getLogger("LabberDriver")

class DriverAbortException(Exception):
    pass

class EnumMixin:
    def eq(self, other):
        assert isinstance(other, type(self))
        return self == other

    @classmethod
    def all_text(cls):
        return ", ".join(sorted([f'"{d.name}"' for d in cls]))

    @classmethod
    def get_exception(cls, value: str):
        assert isinstance(value, str)
        err = f'Unkown "{value}". Expect one of {cls.all_text()}!'
        try:
            return cls[value]
        except KeyError as e:
            raise Exception(err) from e

    @classmethod
    def from_visa(cls, value_text: str) -> enum.Enum:
        assert isinstance(value_text, str)
        err = f'Unkown "{value_text}". Expect one of {cls.all_text()}!'
        try:
            value = int(value_text)
        except ValueError as e:
            raise Exception(err) from e
        try:
            return cls(value)
        except KeyError as e:
            raise Exception(err) from e


class EnumLogging(EnumMixin, enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"

    def setLevel(self):
        level = {
            EnumLogging.DEBUG: logging.DEBUG,
            EnumLogging.INFO: logging.INFO,
            EnumLogging.WARNING: logging.WARNING,
        }[self]
        logger.info(f"Set Logging Level to '{self.name}'")
        logger.setLevel(level)


class Quantity(EnumMixin, enum.Enum):
    """
    Readable name => value as in 'heater_thermometrie_2021.ini'
    """
    ControlLogging = "Control / Logging"
    ControlLabberState = "Control / Labber State"
    ControlHoldCurrent = "Control / Hold Current Z"
    ControlHoldSwitchheaterOn = "Control / Hold Switchheater on Z"
    ControlRampRateZ = "Control / Ramp Rate Z"
    ControlRampRateX = "Control / Ramp Rate X"
    ControlRampRateY = "Control / Ramp Rate Y"
    ControlSetpointX = "Control / Field Setpoint X"
    ControlSetpointY = "Control / Field Setpoint Y"
    ControlSetpointZ = "Control / Field Setpoint Z"
    StatusSwitchheaterStatus = "Status / Switchheater Status Z"
    StatusFieldActualX = "Status / Field actual X"
    StatusFieldActualY = "Status / Field actual Y"
    StatusFieldActualZ = "Status / Field actual Z"
    StatusMagnetStateX = "Status / Magnet State X"
    StatusMagnetStateY = "Status / Magnet State Y"
    StatusMagnetStateZ = "Status / Magnet State Z"
    ConfigName =  "Config / Name"
    ConfigAxis = "Config / Axis"
        
