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
        name="Simulation",
        field_limit=field_limit,
        use_visa_simulation = True,
        x_axis=Magnet(
            ip_address="GPIB::1::INSTR",
            current_limit_A=61.98,  # Ampere
            field_limit_T=6,  # Tesla
            ramp_rate_limit_Apers=0.0909,  # Ampere/s
            has_switchheater=True,
        ),
        y_axis=Magnet(
            ip_address="GPIB::2::INSTR",
            current_limit_A=12.23,  # Ampere
            field_limit_T=12.34,  # Tesla
            ramp_rate_limit_Apers=12.34,  # Ampere/s
            has_switchheater=False,
        ),
        z_axis=Magnet(
            ip_address="GPIB::3::INSTR",
            current_limit_A=12.23,  # Ampere
            field_limit_T=12.34,  # Tesla
            ramp_rate_limit_Apers=12.34,  # Ampere/s
            has_switchheater=False,
        )
    )
    return station
