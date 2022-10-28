# pylint: disable=dangerous-default-value
import sys
import logging
from AMI430_driver_utils import Quantity

import InstrumentDriver  # pylint: disable=import-error

import AMI430_visa
from AMI430_utils import Station
import AMI430_driver_config
import AMI430_thread

logger = logging.getLogger("LabberDriver")

logging.basicConfig()
logger.setLevel(logging.DEBUG)


assert sys.version_info.major == 3
assert sys.version_info.minor == 7
assert sys.version_info.micro == 9


class Driver(InstrumentDriver.InstrumentWorker):
    """This class implements the AMI430 driver"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._thread: AMI430_thread.VisaThread = None
        self._ramping_required = True

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""

        # Reset the usb connection (it must not change the applied voltages)
        self.log("AMI 430 Magnets Driver")
        station = AMI430_driver_config.get_station()
        self._thread = AMI430_thread.VisaThread(station=station)

    @property
    def station(self) -> Station:
        return self._thread.station

    @property
    def visa_station(self) -> AMI430_visa.VisaStation:
        return self._thread.visa_station

    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        self._thread.stop()

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        # keep track of multiple calls, to set multiple voltages efficiently
        if self.isFirstCall(options):
            logger.info(f"********** FIRST CALL {quant.name} {value}: {options}")

        value_new = value

        try:
            quantity = Quantity(quant.name)
            value_new = self._thread.set_quantity_sync(quantity=quantity, value=value)
            if quantity in (
                Quantity.ControlSetpointX,
                Quantity.ControlSetpointY,
                Quantity.ControlSetpointZ,
                Quantity.ControlHoldCurrent,
                Quantity.ControlHoldSwitchheaterOn,
            ):
                self._ramping_required = True

            if self.isFinalCall(options):
                if self.visa_station._mode is AMI430_visa.ControlMode.RAMPING_WAIT:
                    if self._ramping_required:
                        self._ramping_required = False
                        logger.info(
                            f"********** FINAL CALL {quant.name} {value}: {options}"
                        )
                        self._thread.wait_till_ramped_sync()
                        logger.info(
                            f"********** FINAL CALL DONE {quant.name} {value}: {options}"
                        )

            return value_new
        except:
            print(" ???", quant.name, value)
            pass

        logger.error(f"performSetValue: Unknown quantity '{quant.name}' {value}")
        # if quant.name == "Control / Field target":
        #     raise

    def checkIfSweeping(self, quant):
        """Always return false, sweeping is done in loop"""
        return False

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        # only implmeneted for geophone voltage
        logger.debug(f"performGetValue({quant.name})")

        try:
            quantity = Quantity(quant.name)
        except:
            raise Exception("performGetValue(): Unknown quant.name={quant.name} ")

        try:
            value = self._thread.get_quantity_sync(quantity=quantity)
            return value
        except:
            raise Exception(
                f"performGetValue(): Failed to get_quantity_sync(quantity={quantity}) "
            )
