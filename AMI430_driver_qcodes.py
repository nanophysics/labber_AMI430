from AMI430_utils import Station

import qcodes.instrument.sims as sims
import qcodes

from qcodes.instrument_drivers.american_magnetics.AMI430_visa import (
    AMI430,
    AMI430_3D,
    AMI430Warning,
)


# If any of the field limit functions are satisfied we are in the safe zone.
# We can have higher field along the z-axis if x and y are zero.
field_limit = [
    lambda x, y, z: x == 0 and y == 0 and z < 3,
    lambda x, y, z: np.linalg.norm([x, y, z]) < 2,
]


class DriverQCodes:
    def __init__(self, station: Station):
        self.station = station

        visalib = None
        if self.station.use_visa_simulation:
            # path to the .yaml file containing the simulated instrument
            visalib = sims.__file__.replace("__init__.py", "AMI430.yaml@sim")

        self.ix = AMI430(
            "x", address=self.station.x_axis.ip_address, visalib=visalib, terminator="\n"
        )
        self.iy = AMI430(
            "y", address=self.station.y_axis.ip_address, visalib=visalib, terminator="\n"
        )
        self.iz = AMI430(
            "z", address=self.station.z_axis.ip_address, visalib=visalib, terminator="\n"
        )
        self.i3d = AMI430_3D(
            "AMI430_3D", self.ix, self.iy, self.iz, field_limit=field_limit
        )

    def close(self):
        self.ix.close()
        self.iy.close()
        self.iz.close()
