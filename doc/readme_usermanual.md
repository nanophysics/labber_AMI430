# User Manual

## Stati

The code implementing this table may be found here: AMI430_visa.py

| Name | set by | comment |
| - | - | - |
| RAMPING | Labber | Labber driver will return immediately and start ramping towards the “field setpoint”. As soon as “field setpoint” is reached: switch to HOLDING
 |
| HOLDING | Magnet | |
| PAUSED | Labber | Labber driver will return immediately and stop ramping |
| IDLE | Magnet | ... |
| OFF | Labber | Labber will block until state is reached |
| PERSIST_HEATING | Labber | Labber will block until state is reached |
| PERSIST_COOLING | Labber | Labber will block until state is reached |
| MISALIGNED | Magnet | The three magnets are NOT in the same state |
| ERROR | Magnet | At least one magnet is in error state |
