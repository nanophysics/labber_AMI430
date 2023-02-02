import pytest
import numpy as np

from AMI430_utils import Station, FieldLimitViolation
from AMI430_visa import VisaStation

import AMI430_driver_config_sofia
import AMI430_driver_config_tabea

sofia = AMI430_driver_config_sofia.get_station()
#tabea = AMI430_driver_config_tabea.get_station()


def verify_field(station: Station, x: float, y: float, z: float):
    visa_station = VisaStation(station)
    visa_station.open(initialize_visa=False)
    visa_station.visa_magnet_x.field_setpoint_Tesla = x
    visa_station.visa_magnet_y.field_setpoint_Tesla = y
    visa_station.visa_magnet_z.field_setpoint_Tesla = z
    visa_station.station.validate_field_limit(visa_station=visa_station)


@pytest.mark.parametrize(
    "station, x, y, z",
    (
        (sofia, 0.0, 0.0, 0.0),
        (
            sofia,
            -1e-13,
            -1e-13,
            -1e-13,
        ),
        (sofia, 1 / np.sqrt(3), 1 / np.sqrt(3), 1 / np.sqrt(3)),
        (sofia, 0, 3 / np.sqrt(2), 3 / np.sqrt(2)),
        (sofia, 1 / np.sqrt(2), 1 / np.sqrt(2), 0),
        (sofia, 1 / np.sqrt(2), 0, 1 / np.sqrt(2)),
        (sofia, 0,0,6.0),
        (sofia,1.0,0,0)
    ),
)
def test_limits_valid(station: Station, x: float, y: float, z: float):
    verify_field(station, x, y, z)


@pytest.mark.parametrize(
    "station, x, y, z",
    (
        (sofia, 12.0, 12.0, 12.0),
        (sofia, 1.1, 0.0, 0.0),
        (sofia, 0.0, 3.1, 0.0),
        (sofia, 0.0, 0.0, 6.1),
        (sofia, 1, 0.002, 0.0),
        (sofia, 0.00001, 3, 0.0),
        (sofia, 0.0, 0.0, 6.01),
        (sofia, 1.001 / np.sqrt(3), 1 / np.sqrt(3), 1 / np.sqrt(3)),
    ),
)
def test_limits_violation(station: Station, x: float, y: float, z: float):
    with pytest.raises(FieldLimitViolation):
        verify_field(station, x, y, z)
