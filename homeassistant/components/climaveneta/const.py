"""Constants for the Climaveneta iMXW and iLife2 integration."""
from datetime import timedelta

DOMAIN = "climaveneta"


DEFAULT_MODBUS_HUB = "modbus_hub"
DEFAULT_SERIAL_SLAVE_ID = 1

CONF_HUB = "hub"
DEVICE_TYPE = "device_type"
CLIMAVENETA_IMXW = "imxw"
CLIMAVENETA_ILIFE2 = "ilife2"

TIMEOUT = 60

SCAN_INTERVAL = timedelta(seconds=30)


""" Climaveneta iMXW modbus registers"""
IMXW_ACTUAL_AIR_TEMPERATURE_REGISTER = 0x1002
IMXW_ACTUAL_WATER_TEMPERATURE_REGISTER = 0x1004

IMXW_STATE_READ_ON_OFF_REGISTER = 0x100F
IMXW_STATE_READ_FAN_ONLY_REGISTER = 0x1010
IMXW_STATE_READ_SEASON_REGISTER = 0x1013
IMXW_STATE_READ_FAN_AUTO_REGISTER = 0x1017
IMXW_STATE_READ_FAN_STOP_REGISTER = 0x1018
IMXW_STATE_READ_FAN_MIN_SPEED_REGISTER = 0x1019
IMXW_STATE_READ_FAN_MED_SPEED_REGISTER = 0x101A
IMXW_STATE_READ_FAN_MAX_SPEED_REGISTER = 0x101B
IMXW_STATE_READ_EV_WATER_REGISTER = 0x101C

IMXW_ALARM_T1_REGISTER = 0x1028
IMXW_ALARM_T3_REGISTER = 0x102A
IMXW_ALARM_WATER_DRAIN_REGISTER = 0x102B

IMXW_TARGET_TEMPERATURE_SUMMER_REGISTER = 0x102D
IMXW_TARGET_TEMPERATURE_WINTER_REGISTER = 0x102E

IMXW_STATE_WRITE_ON_OFF_REGISTER = 0x105C
IMXW_STATE_WRITE_MODE_REGISTER = 0x105D
IMXW_STATE_WRITE_FAN_SPEED_REGISTER = 0x105E

IMXW_MODE_SUMMER = 0
IMXW_MODE_WINTER = 1

IMXW_MODE_OFF = 0
IMXW_MODE_ON = 1


""" Climaveneta iLife modbus registers"""
ILIFE_TARGET_TEMPERATURE_REGISTER = 231
ILIFE_ACTUAL_AIR_TEMPERATURE_REGISTER = 0
ILIFE_ACTUAL_WATER_TEMPERATURE_REGISTER = 1
ILIFE_STATE_READ_SETPOINT_REGISTER = 8
ILIFE_STATE_READ_REGISTER = 104
ILIFE_STATE_READ_FAN_SPEED = 15
ILIFE_STATE_READ_PROGRAM_REGISTER = 201
ILIFE_STATE_OUT_REGISTER = 9
ILIFE_STATE_MAN_REGISTER = 233

ILIFE_WATER_BYPASS = 0
ILIFE_WATER_CIRCULATING = 1

""" global mode/flags"""
MODE_SUMMER = 0
MODE_WINTER = 1

MODE_OFF = 0
MODE_ON = 1

WATER_BYPASS = 0
WATER_CIRCULATING = 1
