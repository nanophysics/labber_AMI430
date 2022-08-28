# Design

## Variants

### Variant `Channel`

As QCodes:
* For every channel one driver
* And a XY driver
* And a XYZ driver


### Variant `All in one - from scratch`

One labber driver for all channels.

### Variant `All in one - depend on qcodes`

One labber driver for all channels.

This driver `pip install qcodes` and uses the internal qcodes interface.

A `AMI430_driver.ini`, `AMI430_driver.py` will connect labber with qcodes


## Design decisions

| Topic | QCodes | labber_AMI430 | Comment |
| - | - | - | - |
| Ramp Mode | `default`/`simultaneous` | `simultaneous` | Simplification |
