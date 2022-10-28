import numpy as np
from AMI430_utils import Station, Magnet, check_smaller_than
from AMI430_visa import VisaStation, Axis


def validate_field_limit(visa_station: "VisaStation") -> None:
    assert visa_station.station.axis is Axis.AXIS3
    x = visa_station.visa_magnet_x.field_setpoint_Tesla
    y = visa_station.visa_magnet_y.field_setpoint_Tesla
    z = visa_station.visa_magnet_z.field_setpoint_Tesla
    check_smaller_than(x, 1.0, "X too large")
    check_smaller_than(y, 3.0, "Y too large")
    check_smaller_than(z, 6.0, "Z too large")
    if np.abs(x) <= 1e-12:
        if np.abs(y) <= 1e12:
            return
        check_smaller_than(np.linalg.norm([y, z]), 3.0, "2D field vector too large")
        return
    check_smaller_than(np.linalg.norm([x, y, z]), 1.0, "3D field vector too large")


def get_station() -> Station:
    station = Station(
        name="Sofia",
        validate_field_limit=validate_field_limit,
        x_axis=Magnet(
            ip_address="TCPIP0::169.254.27.8::7180::SOCKET",
            current_limit_A=65.32,  # Ampere
            field_limit_T=1.0,  # Tesla
            ramp_rate_limit_Apers=0.222,  # Ampere/s
            ramp_rate_initial_Apers=0.02,
            inductance_H=4.5,
            has_switchheater=False,
        ),
        y_axis=Magnet(
            ip_address="TCPIP0::169.254.70.51::7180::SOCKET",
            current_limit_A=79.77,  # Ampere
            field_limit_T=3.0,  # Tesla
            ramp_rate_limit_Apers=0.0353,  # Ampere/s
            ramp_rate_initial_Apers=0.02,
            inductance_H=28.3,
            has_switchheater=False,
        ),
        z_axis=Magnet(
            ip_address="TCPIP0::169.254.201.182::7180::SOCKET",
            current_limit_A=61.98,  # Ampere
            field_limit_T=6.0,  # Tesla
            ramp_rate_limit_Apers=0.0909,  # Ampere/s
            ramp_rate_initial_Apers=0.06,
            inductance_H=11.0,  # Henry
            has_switchheater=True,
            switchheater_heat_time_s=30.0,
            switchheater_cool_time_s=30.0,  # 600.0, changed it for test purposes
            switchheater_current_A=20.1e-3,
            persisten_current_rampe_rate_Apers=10.0,
        ),
    )
    return station
