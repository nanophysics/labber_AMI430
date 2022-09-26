# User Manual

## Installation

Existing installation manuals
| Labber | Pyboard | Python | State | Project |
| - | - | - | - | - |
| Labber | - |3.7+visa+qcodes| .. | [labber_AMI430](https://github.com/nanophysics/labber_AMI430) |
| Labber | Pyboard | 3.7 | actual | [heater_thermometrie_2021](https://github.com/nanophysics/heater_thermometrie_2021/blob/main/doc_installation/README_INSTALLATION_python3_7_9.md) |
| Labber | Pyboard | 3.7 | python installation is missing | [compact_2012](https://github.com/nanophysics/compact_2012/blob/master/doc_installation/README_INSTALLATION_WITH_LABBER.md) |
| - | - | py3.9| actual | [pymeas noise](https://github.com/nanophysics/pymeas2019_noise/tree/master/documentation) |




```
cd git_qcodes

C:\Users\maerki\AppData\Local\Programs\Python\Python37\python.exe -m pip install --no-warn-script-location -e .

C:\Users\maerki\AppData\Local\Programs\Python\Python37\python.exe -m pip install --no-warn-script-location pyvisa-py pyvisa-sim
```

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
