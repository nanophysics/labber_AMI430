
from AMI430_driver_config_tabea import get_station as get_station_tabea

def get_station():
    station = get_station_tabea()
    station.name = "sofia"
    station.z_axis = station.y_axis
    return station