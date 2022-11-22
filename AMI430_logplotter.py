import matplotlib.pyplot as plt
import pathlib
from AMI430_logparser import *
from AMI430_visa import *
from AMI430_utils import *
import matplotlib
import numpy as np
from matplotlib.patches import Rectangle

matplotlib.rcParams["backend"] = "Qt5Agg"
from datetime import datetime, timedelta
from matplotlib.widgets import MultiCursor


class Plotter:
    def __init__(self, axis: Axis, filename: os.path, timewindow=None) -> None:
        self.axis = axis
        self._filename = filename
        self.timewindow = timewindow
        self.dataframes = []
        self._generate_dataframes()
        self._parse_logfile_to_dataframes()

    def _parse_logfile_to_dataframes(self):
        for log in parse_file(self._filename, self.timewindow):
            for dataframe in self.dataframes:
                dataframe.pick2(log)

    def _generate_dataframes(self):
        if self.axis is Axis.AXIS3:
            axislist = ["X", "Y", "Z"]
        if self.axis is Axis.AXIS2:
            axislist = ["Y", "Z"]
        for dim in axislist:
            self.dataframes.append(
                DataFrameMagnetField(
                    "Magnet Field", logger_tag=LoggerTags.MAGNET_FIELD, magnet=dim
                )
            )
            self.dataframes.append(
                DataFrameMagnetState(
                    "Magnet State", logger_tag=LoggerTags.MAGNET_STATE, magnet=dim
                )
            )
            self.dataframes.append(
                DataFrameSetpoint(
                    "Setpoint", logger_tag=LoggerTags.LABBER_SET, magnet=dim
                )
            )
        self.dataframes.append(
            DataframeBase("Labber State", logger_tag=LoggerTags.LABBER_STATE)
        )
        self.dataframes.append(
            DataframeBase("Ramping Duration", logger_tag=LoggerTags.RAMPING_DURATION_S)
        )
        return

    def _axis_labeling(self, ax: plt.axes, logger_tag: LoggerTags) -> None:
        ax.set_title(logger_tag.name)
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("")

        if logger_tag == LoggerTags.MAGNET_FIELD:
            ax.set_ylabel("B Field [T]")
            return
        if logger_tag == LoggerTags.MAGNET_STATE:
            ax.set_yticks([member.value for member in AMI430State])
            ax.set_yticklabels([member.name for member in AMI430State])
            return
        if logger_tag == LoggerTags.LABBER_STATE:
            ax.set_yticks([member.value for member in LabberState])
            ax.set_yticklabels([member.name for member in LabberState])
            return
        if logger_tag == LoggerTags.LABBER_SET:
            ax.set_ylabel("B Field [T]")
            return
        if logger_tag == LoggerTags.RAMPING_DURATION_S:
            ax.set_ylabel("Ramping Duration [s]")

    def plot(self, logger_tag: LoggerTags, ax: plt.axes) -> None:
        for dataframe in self.dataframes:
            if dataframe.logger_tag == logger_tag:
                # check if we can do this with the type class.
                self._axis_labeling(ax, logger_tag)
                if logger_tag in LoggerTags.general_properties():
                    ax.plot(dataframe.time_stamp, dataframe.value)
                    return
                ax.plot(dataframe.time_stamp, dataframe.value, label=dataframe.magnet)
                ax.legend(loc="upper right")
        return

    def plot_timewindow(self, dates: List[datetime], fig: plt.figure) -> None:

        for ax in fig.get_axes():
            ax.set_xlim(dates)
        return

    def highlight_state(self, fig: plt.figure, logger_tag: LoggerTags, state) -> None:
        for dataframe in self.dataframes:
            if dataframe.logger_tag == logger_tag:
                axes = fig.get_axes()
                for ax in axes:
                    whr_idxlist = np.where(np.array(dataframe.value) == state.value)
                    whr_time_stamps = np.array(dataframe.time_stamp)[whr_idxlist]

                    # ax.scatter(whr_time_stamps, np.ones_like(whr_time_stamps) * 6)
                    for element in whr_time_stamps:
                        ax.add_patch(
                            Rectangle(
                                (element - timedelta(seconds=1), 0),
                                timedelta(seconds=2),
                                10,
                                alpha=0.2,
                            )
                        )
        return