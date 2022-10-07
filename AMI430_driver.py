# pylint: disable=dangerous-default-value
import sys
import logging

import InstrumentDriver  # pylint: disable=import-error

import AMI430_driver_config
import AMI430_visa
from AMI430_utils import Station

logger = logging.getLogger("LabberDriver")

logging.basicConfig()
logger.setLevel(logging.DEBUG)

LABBER_INTERNAL_QUANTITIES = ("Expert",)

assert sys.version_info.major == 3
assert sys.version_info.minor == 7
assert sys.version_info.micro == 9

class Driver(InstrumentDriver.InstrumentWorker):
    """This class implements the AMI430 driver"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.station: Station = None
        self.visa_station: AMI430_visa.VisaStation = None

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""

        # Reset the usb connection (it must not change the applied voltages)
        self.log("AMI 430 Magnets Driver")
        self.station = AMI430_driver_config.get_station()
        self.visa_station = AMI430_visa.VisaStation(station=self.station)
        self.visa_station.open()

    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        self.visa_station.close()

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        # keep track of multiple calls, to set multiple voltages efficiently
        value_new = value

        if quant.name == "Control / Field target":
            self.control_field_target = value
            value_new = list([v + 1 for v in value])
            logger.debug(f"performSetValue('{quant.name}', '{value}') -> '{value_new}'")

        # if quant.name == 'Control / Switchheater Status Z':
        #     self.visa_station.visa_magnet_z.switchheater_state = value
        #     logger.debug(f"performSetValue('{quant.name}', '{value}') -> '{value_new}'")

        if quant.name == 'Control / Hold Switchheater on Z':
            self.visa_station.holding_switchheater_on = value
            logger.debug(f"performSetValue('{quant.name}', '{value}') -> '{value_new}'")

        if quant.name == 'Control / Hold Current Z':
            self.visa_station.holding_current = value 
            logger.debug(f"performSetValue('{quant.name}', '{value}') -> '{value_new}'")

        return value_new
        # if quant.name in LABBER_INTERNAL_QUANTITIES:
        #     return value
        # try:
        #     value_new = self.ht.set_value(name=quant.name, value=value)
        #     logger.debug(f"performSetValue('{quant.name}', '{value}') -> '{value_new}'")
        #     return value_new
        # except QuantityNotFoundException as e:
        #     logger.exception(e)
        #     raise

    def checkIfSweeping(self, quant):
        """Always return false, sweeping is done in loop"""
        return False

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        # only implmeneted for geophone voltage
        logger.debug(f"performGetValue({quant.name})")
        if quant.name == "Config / Name":
            return self.station.name
        if quant.name == "Config / Axis":
            return self.station.axis.name
        if quant.name == "Status / Labber State":
            labber_state = self.visa_station.get_labber_state()
            return labber_state.name
        if quant.name == 'Control / Switchheater Status Z':
            return self.visa_station.visa_magnet_z.switchheater_state
        if quant.name == 'Control / Hold Switchheater on Z':
            return self.visa_station.holding_switchheater_on
        if quant.name == 'Control / Hold Current Z':
            return self.visa_station.holding_current
        return 42
        # if quant.name in LABBER_INTERNAL_QUANTITIES:
        #     return quant.getValue()
        # try:
        #     value = self.ht.get_value(name=quant.name)
        #     logger.debug(f"performGetValue({quant.name}) -> '{value}'")
        #     return value
        # except QuantityNotFoundException as e:
        #     logger.exception(e)
        #     raise
