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
    def __init__(
        self, dataframes: List[DataframeBase], filename: os.path, timewindow=None
    ) -> None:
        self.dataframes = dataframes
        self._filename = filename
        self.timewindow = timewindow
        self._parse_logfile_to_dataframes()

    def _parse_logfile_to_dataframes(self):
        for log in parse_file(self._filename, self.timewindow):
            for dataframe in self.dataframes:
                dataframe.pick2(log)

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
            ax.set_ylabel('Ramping Duration [s]')

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

    def highlight_field_value(self) -> None:
        pass

    def _update_plot(self) -> None:
        pass

    def clear_dataframes(self) -> None:
        pass

    def refresh_singleaxis(self) -> None:
        pass

filename = pathlib.Path("tmp_AMI430_Sofia.log")
dataframes = (
    # dfMagnetField(@x@),
    DataFrameMagnetField(
        "Magnet Field", logger_tag=LoggerTags.MAGNET_FIELD, magnet="Z"
    ),
    DataFrameMagnetField(
        "Magnet Field", logger_tag=LoggerTags.MAGNET_FIELD, magnet="Y"
    ),
    DataFrameMagnetState(
        "Magnet State", logger_tag=LoggerTags.MAGNET_STATE, magnet="Y"
    ),
    DataFrameMagnetField(
        "Magnet Field", logger_tag=LoggerTags.MAGNET_FIELD, magnet="Z"
    ),
    DataFrameMagnetState(
        "Magnet State", logger_tag=LoggerTags.MAGNET_STATE, magnet="Z"
    ),
    DataframeBase("Labber State", logger_tag=LoggerTags.LABBER_STATE),
    DataFrameSetpoint("Setpoint", logger_tag=LoggerTags.LABBER_SET, magnet="Z"),
    DataFrameSetpoint("Setpoint", logger_tag=LoggerTags.LABBER_SET, magnet="X"),
    DataFrameSetpoint("Setpoint", logger_tag=LoggerTags.LABBER_SET, magnet="Y"),
    DataframeBase("Ramping Duration", logger_tag=LoggerTags.RAMPING_DURATION_S),
)

timewindow = ["2022-10-31", "2022-11-10"]

# plotter = Plotter(dataframes, filename,timewindow) # Keep this separate otherwise the dataframes are parsed several times.
plotter = Plotter(dataframes, filename,timewindow)


def main():
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True)
    timewindow = [datetime(2022, 10, 31, 0, 0, 0), datetime(2022, 11, 5, 0, 0, 0)]
    plotter = Plotter(dataframes, filename, timewindow)
    # plotter = Plotter(dataframes, filename)
    plotter.plot(LoggerTags.MAGNET_FIELD, ax1)
    plotter.plot(LoggerTags.MAGNET_STATE, ax2)
    # plotter.plot(LoggerTags.MAGNET_STATE, ax2)
    plotter.plot(LoggerTags.LABBER_STATE, ax3)
    multi = MultiCursor(fig.canvas, (ax1, ax2, ax3), color="r", lw=1)
    # dates = [datetime(2022, 10, 24, 0, 0, 0), datetime(2022, 10, 24, 23, 0, 0)]
    # plotter.plot_timewindow(dates, fig)
    plotter.highlight_state(fig, LoggerTags.LABBER_STATE, state=LabberState.HOLDING)
    plt.show()


if __name__ == "__main__":
    main()
