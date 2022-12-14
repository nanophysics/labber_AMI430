import numpy as np
from AMI430_utils import Station, Magnet

field_limit = (
    [  # If any of the field limit functions are satisfied we are in the safe zone.
        lambda x, y, z: x == 0
        and y == 0
        and z < 3,  # We can have higher field along the z-axis if x and y are zero.
        lambda x, y, z: np.linalg.norm([x, y, z]) < 2,
    ]
)


def get_station():
    station = Station(
        name="Tabea",
        validate_field_limit=field_limit,
        x_axis=Magnet(
            ip_address="169.254.47.78",
            current_limit_A=61.98,  # Ampere
            field_limit_T=6,  # Tesla
            ramp_rate_limit_Apers=0.0909,  # Ampere/s
            ramp_rate_initial_Apers=0.02,
            inductance_H=28.3,
            has_switchheater=True,
            switchheater_heat_time_s=30.0,
            switchheater_cool_time_s=600.0,
            switchheater_current_A=20.1e-3,
            persisten_current_rampe_rate_Apers=10.0,
        ),
        y_axis=Magnet(
            ip_address="169.254.223.195",
            current_limit_A=12.23,  # Ampere
            field_limit_T=12.34,  # Tesla
            ramp_rate_limit_Apers=12.34,  # Ampere/s
            ramp_rate_initial_Apers=0.02,
            inductance_H=28.3,
            has_switchheater=False,
        ),
    )
    return station
