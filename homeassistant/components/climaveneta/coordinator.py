"""Coordinator for the climaveneta iMXW and iLife2 AC."""

import logging

from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_OFF,
    HVACAction,
    HVACMode,
)
from homeassistant.components.modbus import CALL_TYPE_REGISTER_HOLDING, ModbusHub
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CLIMAVENETA_IMXW,
    ILIFE_ACTUAL_AIR_TEMPERATURE_REGISTER,
    ILIFE_STATE_MAN_REGISTER,
    ILIFE_STATE_READ_PROGRAM_REGISTER,
    ILIFE_STATE_READ_REGISTER,
    ILIFE_STATE_READ_SETPOINT_REGISTER,
    IMXW_ACTUAL_AIR_TEMPERATURE_REGISTER,
    IMXW_ACTUAL_WATER_TEMPERATURE_REGISTER,
    IMXW_ALARM_T1_REGISTER,
    IMXW_ALARM_T3_REGISTER,
    IMXW_ALARM_WATER_DRAIN_REGISTER,
    IMXW_STATE_READ_EV_WATER_REGISTER,
    IMXW_STATE_READ_FAN_AUTO_REGISTER,
    IMXW_STATE_READ_FAN_MAX_SPEED_REGISTER,
    IMXW_STATE_READ_FAN_MED_SPEED_REGISTER,
    IMXW_STATE_READ_FAN_MIN_SPEED_REGISTER,
    IMXW_STATE_READ_FAN_ONLY_REGISTER,
    IMXW_STATE_READ_ON_OFF_REGISTER,
    IMXW_STATE_READ_SEASON_REGISTER,
    IMXW_TARGET_TEMPERATURE_SUMMER_REGISTER,
    IMXW_TARGET_TEMPERATURE_WINTER_REGISTER,
    MODE_ON,
    MODE_SUMMER,
    MODE_WINTER,
    SCAN_INTERVAL,
    WATER_CIRCULATING,
)

_LOGGER = logging.getLogger(__name__)


class ClimavenetaCoordinator(DataUpdateCoordinator[None]):
    """Class to manage fetching Climaveneta data."""

    fan_mode = FAN_AUTO
    hvac_mode: HVACMode = HVACMode.OFF
    hvac_action: HVACAction = HVACAction.OFF

    def __init__(
        self, hass: HomeAssistant, device_type: str, hub: ModbusHub, slaveid: int, name
    ) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=SCAN_INTERVAL,
        )
        self.device_type = device_type
        self.hub = hub
        self.slave_id = slaveid
        self.data_modbus = {"a": 1}
        self.name = name

    async def _async_update_data(self):
        """Fetch data from API endpoint."""

        if self.device_type == CLIMAVENETA_IMXW:
            self.async_update_imxw()
        else:
            self.async_update_ilife()

    async def async_update_imxw(self):
        """Fetch data from IMXW device."""
        if self.data_modbus is None:
            self.data_modbus = {}

        # setpoint and actuals
        self.data_modbus["summer_winter"] = await self._async_read_int16_from_register(
            CALL_TYPE_REGISTER_HOLDING, IMXW_STATE_READ_SEASON_REGISTER
        )

        if self.data_modbus["summer_winter"] == MODE_WINTER:  # winter
            self.data_modbus[
                "winter_temperature"
            ] = await self._async_read_temp_from_register(
                CALL_TYPE_REGISTER_HOLDING, IMXW_TARGET_TEMPERATURE_WINTER_REGISTER
            )
            self.data_modbus["target_temperature"] = self.data_modbus[
                "winter_temperature"
            ]
        else:  # summer
            self.data_modbus[
                "summer_temperature"
            ] = await self._async_read_temp_from_register(
                CALL_TYPE_REGISTER_HOLDING, IMXW_TARGET_TEMPERATURE_SUMMER_REGISTER
            )
            self.data_modbus["target_temperature"] = self.data_modbus[
                "summer_temperature"
            ]

        self.data_modbus[
            "current_temperature"
        ] = await self._async_read_temp_from_register(
            CALL_TYPE_REGISTER_HOLDING, IMXW_ACTUAL_AIR_TEMPERATURE_REGISTER
        )

        # state heating/cooling/fan only/off
        self.data_modbus["on_off"] = await self._async_read_int16_from_register(
            CALL_TYPE_REGISTER_HOLDING, IMXW_STATE_READ_ON_OFF_REGISTER
        )
        if self.data_modbus["on_off"]:
            self.data_modbus["fan_only"] = await self._async_read_int16_from_register(
                CALL_TYPE_REGISTER_HOLDING, IMXW_STATE_READ_FAN_ONLY_REGISTER
            )
            self.data_modbus["ev_water"] = await self._async_read_int16_from_register(
                CALL_TYPE_REGISTER_HOLDING, IMXW_STATE_READ_EV_WATER_REGISTER
            )
            if self.data_modbus["fan_only"] == MODE_ON:
                self.hvac_mode = HVACMode.FAN_ONLY
                self.hvac_action = HVACAction.FAN
            elif self.data_modbus["summer_winter"] == MODE_SUMMER:
                self.hvac_mode = HVACMode.COOL
                if self.data_modbus["ev_water"] == WATER_CIRCULATING:
                    self.hvac_action = HVACAction.COOLING
                else:
                    self.hvac_action = HVACAction.IDLE
            else:
                self.hvac_mode = HVACMode.HEAT
                if self.data_modbus["ev_water"] == WATER_CIRCULATING:
                    self.hvac_action = HVACAction.HEATING
                else:
                    self.hvac_action = HVACAction.IDLE
        else:
            self.hvac_mode = HVACMode.OFF
            self.hvac_action = HVACAction.OFF

        # fan speed

        fan_auto = await self._async_read_int16_from_register(
            CALL_TYPE_REGISTER_HOLDING, IMXW_STATE_READ_FAN_AUTO_REGISTER
        )
        if fan_auto == MODE_ON:
            self.fan_mode = FAN_AUTO
        else:
            fan_min = await self._async_read_int16_from_register(
                CALL_TYPE_REGISTER_HOLDING, IMXW_STATE_READ_FAN_MIN_SPEED_REGISTER
            )
            if fan_min == MODE_ON:
                self.fan_mode = FAN_LOW
            else:
                fan_med = await self._async_read_int16_from_register(
                    CALL_TYPE_REGISTER_HOLDING, IMXW_STATE_READ_FAN_MED_SPEED_REGISTER
                )
                if fan_med == MODE_ON:
                    self.fan_mode = FAN_MEDIUM
                else:
                    fan_max = await self._async_read_int16_from_register(
                        CALL_TYPE_REGISTER_HOLDING,
                        IMXW_STATE_READ_FAN_MAX_SPEED_REGISTER,
                    )
                    if fan_max == MODE_ON:
                        self.fan_mode = FAN_HIGH
                    else:
                        self.fan_mode = FAN_AUTO  # should never arrive here...

        self.data_modbus["t1_alarm"] = await self._async_read_int16_from_register(
            CALL_TYPE_REGISTER_HOLDING, IMXW_ALARM_T1_REGISTER
        )

        self.data_modbus["t3_alarm"] = await self._async_read_int16_from_register(
            CALL_TYPE_REGISTER_HOLDING, IMXW_ALARM_T3_REGISTER
        )

        self.data_modbus["water_drain"] = await self._async_read_int16_from_register(
            CALL_TYPE_REGISTER_HOLDING, IMXW_ALARM_WATER_DRAIN_REGISTER
        )

        self.data_modbus[
            "exchanger_temperature"
        ] = await self._async_read_temp_from_register(
            CALL_TYPE_REGISTER_HOLDING, IMXW_ACTUAL_WATER_TEMPERATURE_REGISTER
        )

    async def async_update_ilife(self):
        """Fetch data from iLife device."""
        if self.data_modbus is None:
            self.data_modbus = {}

        # setpoint and actuals
        self.data_modbus[
            "target_temperature"
        ] = await self._async_read_temp_from_register(
            CALL_TYPE_REGISTER_HOLDING, ILIFE_STATE_READ_SETPOINT_REGISTER
        )

        self.data_modbus[
            "current_temperature"
        ] = await self._async_read_temp_from_register(
            CALL_TYPE_REGISTER_HOLDING, ILIFE_ACTUAL_AIR_TEMPERATURE_REGISTER
        )

        # state heating/cooling/fan only/off

        man_register = await self._async_read_int16_from_register(
            CALL_TYPE_REGISTER_HOLDING, ILIFE_STATE_MAN_REGISTER
        )

        program_register = await self._async_read_int16_from_register(
            CALL_TYPE_REGISTER_HOLDING, ILIFE_STATE_READ_PROGRAM_REGISTER
        )
        if (program_register & (1 << 7)) == 0b10000000:
            self.data_modbus["on_off"] = 0  # standby
        else:
            self.data_modbus["on_off"] = 1  # normal operation

        if self.data_modbus["on_off"]:
            stat_register = await self._async_read_int16_from_register(
                CALL_TYPE_REGISTER_HOLDING, ILIFE_STATE_READ_REGISTER
            )
            # out_register = await self._async_read_int16_from_register(
            #    CALL_TYPE_REGISTER_HOLDING, ILIFE_STATE_OUT_REGISTER
            # )

            if man_register == 0:
                self.hvac_mode = HVACMode.HEAT_COOL
            elif man_register == 3:
                self.hvac_mode = HVACMode.HEAT
            elif man_register == 5:
                self.hvac_mode = HVACMode.COOL
            else:
                self.hvac_mode = (
                    HVACMode.OFF
                )  # not a valid number, this register should always be 0, 3 or 5.

            if (stat_register & (1 << 1) == 0) and (stat_register & (1 << 0) == 0):
                self.hvac_action = HVACAction.IDLE
            elif stat_register & (1 << 1) == 0:
                self.hvac_action = HVACAction.COOLING
            else:
                self.hvac_action = HVACAction.HEATING

            # fan speed
            if (program_register & 0b111) == 0b000:
                self.fan_mode = FAN_AUTO
            elif (program_register & 0b111) == 0b001:
                self.fan_mode = FAN_LOW
            elif (program_register & 0b111) == 0b010:
                self.fan_mode = FAN_MEDIUM
            elif (program_register & 0b111) == 0b011:
                self.fan_mode = FAN_HIGH
            else:
                self.fan_mode = FAN_OFF  # unknown state
        else:
            self.hvac_mode = HVACMode.OFF
            self.hvac_action = HVACAction.OFF
            self.fan_mode = FAN_OFF

    # Based on _async_read_register in ModbusThermostat class
    async def _async_read_int16_from_register(
        self, register_type: str, register: int
    ) -> int:
        """Read register using the Modbus hub slave."""

        result = await self.hub.async_pb_call(self.slave_id, register, 1, register_type)

        if result is None:
            _LOGGER.error(
                "Error reading value from Climaveneta %s modbus id %d adapter",
                self.device_type,
                self.slave_id,
            )
            return -1

        return int(result.registers[0])

    async def _async_read_temp_from_register(
        self, register_type: str, register: int
    ) -> float:
        result = float(
            await self._async_read_int16_from_register(register_type, register)
        )

        if not result:
            return -1
        return result / 10.0
