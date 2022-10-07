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

    ControlWriteHeating = "Control Heating / Mode"
    ControlWriteExpert = "Expert"
    ControlWriteLogging = "Control Mode / Logging"
    ControlWriteThermometrie = "Control Heating / Thermometrie"
    ControlWriteGreenLED = "Green LED"
    ControlWritePower_W = "Control Heating / set power (mode manual)"
    ControlWriteTemperature_K = "Control Heating / set temperature (mode controlled)"
    ControlWriteTemperatureAndSettle_K = (
        "Control Heating / set temperature and settle (mode controlled)"
    )
    ControlWriteTemperatureToleranceBand_K = (
        "Control Heating / temperature tolerance band (plus minus)"
    )
    ControlWriteSettleTime_S = "Control Heating / settle time (mode controlled)"
    ControlWriteTimeoutTime_S = "Control Heating / timeout time (mode controlled)"
    StatusReadTemperatureBox_C = "Temperature HeaterBox / Temperature_C"
    StatusReadSerialNumberHeater = "Status Heater / Serial Number Heater"
    StatusReadSerialNumberInsertHidden = "SerialNumberInsertHidden"
    StatusReadSerialNumberInsert = "Status Heater / Serial Number Insert"
    StatusReadDefrostSwitchOnBox = "Status Heater / Defrost - Switch on box"
    StatusReadDefrostUserInteraction = "Status Heater / Defrost - User interaction"
    StatusReadInsertConnected = "Status Insert / Insert Connected"
    StatusReadErrorCounter = "Status Heater / Error counter"
    StatusReadSettled = "Status Heater / Settled (expert)"
    TemperatureReadonlyResistanceCarbon_OHM = (
        "Temperature Resistance / Carbon_Ohm (expert)"
    )
    TemperatureReadonlyResistancePT1000_OHM = (
        "Temperature Resistance / PT1000_Ohm (expert)"
    )
    TemperatureReadonlyTemperatureCarbon_K = (
        "Temperature Temperature / Carbon_K (expert)"
    )
    TemperatureReadonlyTemperaturePT1000_K = (
        "Temperature Temperature / PT1000_K (expert)"
    )
    TemperatureReadonlyTemperatureCalibrated_K = (
        "Temperature Temperature / Temperature_K"
    )
