from multiprocessing.sharedctypes import Value
import re
import time
import pathlib
from typing import List
from dataclasses import dataclass, field
import enum 
from AMI430_driver_utils import EnumLogging, EnumMixin

re_line = re.compile(r"^(?P<time_stamp>\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d) ((?P<severity>[A-Z]+) (?P<tag>[A-Za-z0-9_]+) (?P<msg>.*)|(?P<msg_without_tag>.*))$")

class LoggerTags(EnumMixin, enum.IntEnum):
    MAGNET_FIELD = enum.auto()
    MAGNET_STATE = enum.auto()
    LABBER_STATE = enum.auto()
    AMI430State = enum.auto()
    MAGNET_RAMPING_STATE = enum.auto()
    LABBER_SET = enum.auto()
    STATION_RAMPING_STATE = enum.auto()
    RAMPING_DURATION_S = enum.auto()


@dataclass
class Log:
    lineno: int
    match_line: re.Match

    @property
    def time_stamp(self) -> str:
        return self.match_line.group("time_stamp")

    @property
    def tag(self) -> str:
        return self.match_line.group("tag")

    @property
    def msg(self) -> str:
        return self.match_line.group("msg")

@dataclass
class DataframeBase:
    name: str
    logger_tag : LoggerTags
    time_stamp: List[str] = field(default_factory=list)
    value : List[float] = field(default_factory=list)
    label : List[str] = field(default_factory=list)

    def pick2(self, log : Log) -> None: 
        if log.tag != self.logger_tag.name:
            return
        # try:
        #     log_enum = LoggerTags(log.tag)
        # except ValueError: 
        #     return
        # if log_enum != self.logger_tag:
        #     return
        self.pick(log)
    def pick(self, log: Log) -> None:
        raise Exception('Needs to be overwritten')

@dataclass
class DataFrameMagnetField(DataframeBase):
    magnet: str = None

    def pick(self, log: Log) -> None:
        # FIELD X 0.01
        magnet, _, field_str_T = log.msg.partition(" ")
        if magnet != self.magnet:
            return
        field_T = float(field_str_T)
        self.time_stamp.append(log.time_stamp)
        self.value.append(field_T)


@dataclass
class DataFrameMagnetState(DataframeBase):
    magnet: str = None

    def pick(self, log: Log) -> None:
        # MAGNET_STATE Y PAUSED 1
        magnet, state_str, state_val = log.msg.split(" ")
        if magnet != self.magnet:
            return
        state_val = int(state_val)
        self.time_stamp.append(log.time_stamp)
        self.value.append(state_val)
        self.label.append(state_str)


def parse_file(filename: pathlib.Path):
    for lineno0, line in enumerate(filename.open("r").readlines()):
        line = line.rstrip()
        match_line = re_line.match(line)
        yield Log(lineno0+1, match_line)

def main(filename):
     
    dataframes = (
        # DataFrameMagnetField("Magnet Field", magnet="Z"),
        DataFrameMagnetField("Magnet Field",logger_tag=LoggerTags.MAGNET_FIELD, magnet="Y"),
        DataFrameMagnetState("Magnet State",logger_tag=LoggerTags.MAGNET_STATE, magnet="Y"),
    #     DataFrameMagnetState("Magnet State", magnet="Y"),
    )
    for log in parse_file(filename):
        for dataframe in dataframes:
            dataframe.pick2(log)

    for dataframe in dataframes:
        print(dataframe)

main(pathlib.Path('tmp_AMI430.log'))