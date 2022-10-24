from logging import Logger
import matplotlib.pyplot as plt
import pathlib
from AMI430_logparser import *
from AMI430_visa import *
import matplotlib

matplotlib.rcParams["backend"] = "Qt5Agg"
from datetime import datetime
from matplotlib.widgets import MultiCursor


class Plotter:
    def __init__(self, dataframes: List[DataframeBase], filename: os.path) -> None:
        self.dataframes = dataframes
        self._filename = filename
        self._parse_logfile_to_dataframes()

    def _parse_logfile_to_dataframes(self):
        for log in parse_file(filename):
            for dataframe in dataframes:
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

    def plot(self, logger_tag: LoggerTags, ax: plt.axes) -> None:
        for dataframe in self.dataframes:
            if dataframe.logger_tag == logger_tag:
                # check if we can do this with the type class.
                self._axis_labeling(ax, logger_tag)
                if logger_tag in LoggerTags.general_properties():
                    ax.plot(dataframe.time_stamp, dataframe.value)
                    return
                ax.plot(dataframe.time_stamp, dataframe.value, label=dataframe.magnet)
        return

    def _update_plot(self) -> None:
        pass

    def clear_dataframes(self) -> None:
        pass

    def refresh_singleaxis(self) -> None:
        pass


filename = pathlib.Path("tmp_AMI430.log")


dataframes = (
    # DataFrameMagnetField("Magnet Field", magnet="Z"),
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
)


fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True)

plotter = Plotter(dataframes, filename)
plotter.plot(LoggerTags.MAGNET_FIELD, ax1)
plotter.plot(LoggerTags.MAGNET_STATE, ax2)
plotter.plot(LoggerTags.LABBER_STATE, ax3)
multi = MultiCursor(fig.canvas, (ax1, ax2, ax3), color="r", lw=1)
plt.show()


# def refresh(ax1, ax2, ax3):
#     # we need a clear dataframe function
#     for log in parse_file(filename):
#         for dataframe in dataframes:
#             dataframe.pick2(log)
#     for dF in dataframes:
#         if dF.logger_tag == LoggerTags.MAGNET_FIELD:
#             ax1.plot(dF.time_stamp,dF.value, label = dF.magnet)
#             ax1.legend()
#         if dF.logger_tag == LoggerTags.MAGNET_STATE:
#             ax2.plot(dF.time_stamp,dF.value, label = dF.magnet)
#             ax2.legend()
#         if dF.logger_tag == LoggerTags.LABBER_STATE:
#             ax3.plot(dF.time_stamp,dF.value)
#             pass


# def on_click(event):
#     ax1.cla()
#     ax2.cla()
#     ax3.cla()
#     refresh(ax1,ax2,ax3)
#     plt.legend()
#     plt.draw()


# fig, (ax1,ax2,ax3) = plt.subplots(3,1,sharex = True)
# ax1.set_title(LoggerTags.MAGNET_FIELD.name)
# ax1.set_ylabel('B in [T]')
# # ax1.set_xlabel('Timestamp')
# ax1.set_xticklabels([])


# ax2.set_title(LoggerTags.MAGNET_STATE.name)
# ax2.set_yticks([member.value for member in AMI430State])
# ax2.set_yticklabels([member.name for member in AMI430State])
# ax2.set_ylabel('')
# ax2.grid(True, axis = 'y')
# ax2.set_xlabel('Timestamp')

# ax3.set_title(LoggerTags.LABBER_STATE.name)
# ax3.set_yticks([member.value for member in LabberState])
# ax3.set_yticklabels([member.name for member in LabberState])
# ax3.set_ylabel('')
# ax3.grid(True, axis = 'y')
# ax3.set_xticklabels([])

# # .mpl_connect('button_press_event', onclick)
# plt.connect('button_press_event', on_click)
# axcut = plt.axes([0.9,0.0,0.1,0.075])
# bcut = Button(axcut, 'Refresh', color = 'Blue', hovercolor = 'green')
# bcut.on_clicked(on_click)

# refresh(ax1, ax2, ax3)
# multi = MultiCursor(fig.canvas , (ax1,ax2,ax3), color = 'r',lw = 1)
# plt.legend()
# plt.show()
# plt.draw()
