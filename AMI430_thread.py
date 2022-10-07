import time
import logging
import threading
import enum

import AMI430_visa
from AMI430_driver_utils import DriverAbortException
from AMI430_driver_utils import Quantity
from AMI430_utils import Station

TICK_INTERVAL_S = 0.5

logger = logging.getLogger("LabberDriver")

LOCK = threading.Lock()


def synchronized(func):
    def wrapper(*args, **kwargs):
        with LOCK:
            try:
                return func(*args, **kwargs)
            except:  # pylint: disable=bare-except
                logger.exception('Exception in method "HeaterThread.%s"', func.__name__)
                raise

    return wrapper


class VisaThread(threading.Thread):
    """
    EVERY communication between Labber GUI and visa_station is routed via this class!

    There are two problems to solve:
     - Concurrency
        - Labber GUI: 'labber thread'
        - This class: 'visa thread'

     - Synchronized access
       The two threads agree, that before accessing data, the 'LOCK' has to be aquired.
       This is implement using @synchronized.
    """

    def __init__(self, station: Station):
        self.dict_values_labber_thread_copy = {}
        super().__init__(daemon=True)
        self._visa_station = AMI430_visa.VisaStation(station=station)
        logger.info(f"LabberThread(config='{self._visa_station.name}')")
        self._stopping = False
        self.start()

    @property
    def station(self) -> Station:
        return self._visa_station.station

    @property
    def visa_station(self) -> AMI430_visa.VisaStation:
        return self._visa_station

    def run(self):
        while not self._stopping:
            start_s = time.time()
            try:
                self._tick()
            except DriverAbortException as ex:
                logger.error(f"AMI430_driver_utils.DriverAbortException(): {ex}")
                logger.exception(ex)
                raise

            except Exception as ex:
                # Log the error but keep running
                logger.exception(ex)

            elapsed_s = time.time() - start_s
            if elapsed_s > TICK_INTERVAL_S:
                logger.warning(
                    f"tick() took:{elapsed_s:0.3f}s. Exected <= {TICK_INTERVAL_S:0.3f}s"
                )

    def stop(self):
        self._stopping = True
        self.join(timeout=10.0)

    @synchronized
    def _tick(self) -> None:
        """
        Called by the thread: synchronized to make sure that the labber GUI is blocked
        """
        self._visa_station.tick()
        # Create a copy of all values to allow access for the labber thread without any delay.
        self.dict_values_labber_thread_copy = self._visa_station.dict_values.copy()

    @synchronized
    def set_quantity_sync(self, quantity: Quantity, value):
        """
        Called by labber GUI
        """
        return self._visa_station.set_quantity(quantity=quantity, value=value)

    def set_value(self, name: str, value):
        """
        Called by the tread (visa_station):
        Update a value which may be retrieved later by the labber GUI using 'get_quantity_sync'.
        """

        assert isinstance(name, str)
        quantity = Quantity(name)

        if quantity == Quantity.ControlWriteTemperatureAndSettle_K:
            return self._set_temperature_and_settle(quantity=quantity, value=value)

        return self.set_quantity_sync(quantity=quantity, value=value)

    def _set_temperature_and_settle_obsolete(self, quantity: Quantity, value: float):
        assert quantity == Quantity.ControlWriteTemperatureAndSettle_K

        def block_until_settled():
            tick_count_before = self._visa_station.tick_count
            timeout_s = self._visa_station.time_now_s + self._visa_station.get_quantity(
                Quantity.ControlWriteTimeoutTime_S
            )
            while True:
                self._visa_station.sleep(TICK_INTERVAL_S / 2.0)
                if tick_count_before == self._visa_station.tick_count:
                    # Wait for a tick to make sure that the statemachine was called at least once
                    continue
                if not self._visa_station.hsm_heater.is_state(
                    HeaterHsm.state_connected_thermon_heatingcontrolled
                ):
                    # Unexpected state change
                    logger.info(
                        f"Waiting for 'ControlWriteTemperatureAndSettle_K'. Unexpected state change. Got '{self._visa_station.hsm_heater._state_actual}'!"
                    )
                    return
                if self._is_settled():
                    return
                if self._visa_station.time_now_s > timeout_s:
                    logger.info("Timeout while 'ControlWriteTemperatureAndSettle_K'")
                    return

        if abs(value - heater_wrapper.TEMPERATURE_SETTLE_OFF_K) < 1.0e-9:
            logger.warning(f"'{quantity.value}' set to {value:0.1f} K: SKIPPED")
            return

        self._visa_station.set_quantity(Quantity.ControlWriteTemperature_K, value)
        self._visa_station.hsm_heater.wait_temperature_and_settle_start()
        logger.warning(
            f"'{quantity.value}' set to {value:0.1f} K: Blocking. Timeout = {self._visa_station.get_quantity(Quantity.ControlWriteTimeoutTime_S)}s"
        )
        block_until_settled()
        self._visa_station.hsm_heater.wait_temperature_and_settle_over()
        logger.warning("Settle/Timeout time over")
        return heater_wrapper.TEMPERATURE_SETTLE_OFF_K

    @synchronized
    def set_quantity(self, quantity: Quantity, value):
        return self._visa_station.set_quantity(quantity=quantity, value=value)

    def get_value(self, name: str):
        """
        This typically returns immedately as it accesses a copy of all values.
        Only in rare cases, it will delay for max 0.5s.
        """
        assert isinstance(name, str)
        quantity = Quantity(name)
        try:
            value = self.dict_values_labber_thread_copy[quantity]
        except KeyError:
            # Not all values are stored in the dictionary.
            # In this case we have to use the synchronized call.
            value = self.get_quantity_sync(quantity=quantity)
        if isinstance(value, enum.Enum):
            return value.value
        return value

    @synchronized
    def get_quantity_sync(self, quantity: Quantity):
        return self._visa_station.get_quantity(quantity=quantity)

    @synchronized
    def signal(self, signal):
        self._visa_station.signal(signal)

    @synchronized
    def expect_state(self, expected_meth):
        self._visa_station.expect_state(expected_meth=expected_meth)
