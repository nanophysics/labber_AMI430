import numpy as np 
import matplotlib.pyplot as plt 
import pandas as pd 
import pathlib
from AMI430_logparser import *
from AMI430_visa import * 
import matplotlib 
matplotlib.rcParams['backend'] = 'Qt5Agg'
from datetime import datetime
filename = pathlib.Path('tmp_AMI430.log')
     
dataframes = (
    # DataFrameMagnetField("Magnet Field", magnet="Z"),
    DataFrameMagnetField("Magnet Field",logger_tag=LoggerTags.MAGNET_FIELD, magnet="Y"),
    DataFrameMagnetState("Magnet State",logger_tag=LoggerTags.MAGNET_STATE, magnet="Y"),
    DataFrameMagnetField("Magnet Field",logger_tag=LoggerTags.MAGNET_FIELD, magnet="Z"),
    DataFrameMagnetState("Magnet State",logger_tag=LoggerTags.MAGNET_STATE, magnet="Z"),
    DataframeBase("Labber State", logger_tag=LoggerTags.LABBER_STATE),

)
for log in parse_file(filename):
    for dataframe in dataframes:
        dataframe.pick2(log)

# for dataframe in dataframes:
#     print(dataframe)

fig, (ax1,ax2,ax3) = plt.subplots(3,1,sharex = True)
ax1.set_title(LoggerTags.MAGNET_FIELD.name)
ax1.set_ylabel('B in [T]')
# ax1.set_xlabel('Timestamp')
ax1.set_xticklabels([])


ax2.set_title(LoggerTags.MAGNET_STATE.name)
ax2.set_yticks([member.value for member in AMI430State])
ax2.set_yticklabels([member.name for member in AMI430State])
ax2.set_ylabel('')
ax2.grid(True, axis = 'y')
ax2.set_xlabel('Timestamp')

ax3.set_title(LoggerTags.LABBER_STATE.name)
ax3.set_yticks([member.value for member in LabberState])
ax3.set_yticklabels([member.name for member in LabberState])
ax3.set_ylabel('')
ax3.grid(True, axis = 'y')
ax3.set_xticklabels([])


# Todo: vertical line that shows all values 
# Todo: labelintervall choice for xaxis.
for dF in dataframes: 
    if dF.logger_tag == LoggerTags.MAGNET_FIELD:
        ax1.plot(dF.time_stamp,dF.value, label = dF.magnet)
        ax1.legend()
    if dF.logger_tag == LoggerTags.MAGNET_STATE:
        ax2.plot(dF.time_stamp,dF.value, label = dF.magnet)
        ax2.legend()
    if dF.logger_tag == LoggerTags.LABBER_STATE:
        ax3.plot(dF.time_stamp,dF.value)
        pass

plt.legend()
plt.show()


