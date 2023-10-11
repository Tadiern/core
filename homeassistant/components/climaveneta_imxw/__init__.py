"""Platform for the climaveneta_imxw AC."""
import logging

from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    HVACAction,
    HVACMode,
)
from homeassistant.components.modbus import (
    CALL_TYPE_REGISTER_HOLDING,
    CONF_HUB,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    CONF_SLAVE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    ACTUAL_AIR_TEMPERATURE_REGISTER,
    ACTUAL_WATER_TEMPERATURE_REGISTER,
    ALARM_T1_REGISTER,
    ALARM_T3_REGISTER,
    ALARM_WATER_DRAIN_REGISTER,
    DOMAIN,
    MODE_ON,
    MODE_SUMMER,
    MODE_WINTER,
    PLATFORMS,
    SCAN_INTERVAL,
    STATE_READ_EV_WATER_REGISTER,
    STATE_READ_FAN_AUTO_REGISTER,
    STATE_READ_FAN_MAX_SPEED_REGISTER,
    STATE_READ_FAN_MED_SPEED_REGISTER,
    STATE_READ_FAN_MIN_SPEED_REGISTER,
    STATE_READ_FAN_ONLY_REGISTER,
    STATE_READ_ON_OFF_REGISTER,
    STATE_READ_SEASON_REGISTER,
    TARGET_TEMPERATURE_SUMMER_REGISTER,
    TARGET_TEMPERATURE_WINTER_REGISTER,
)

# registers


WATER_BYPASS = 0
WATER_CIRCULATING = 1


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up platform from a ConfigEntry."""

    hub = entry.data[CONF_HUB]
    slave_id = entry.data[CONF_SLAVE]
    name = entry.data[CONF_NAME]

    result = await hub.async_pymodbus_call(
        slave_id, CALL_TYPE_REGISTER_HOLDING, 1, STATE_READ_ON_OFF_REGISTER
    )
    if result is None:
        _LOGGER.error("Error reading value from Climaveneta iMXW modbus adapter")
        return False

    coordinator = ClimavenetaIMXWCoordinator(hass, hub, slave_id, name)
    hass.data.setdefault(DOMAIN, {})
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


class ClimavenetaIMXWCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass: HomeAssistant, hub, slaveid, name) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=name,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=SCAN_INTERVAL,
        )
        self.hub = hub
        self.modbus_slave = slaveid
        self.data = []
        self.name = name

    async def _async_update_data(self):
        """Fetch data from API endpoint."""

        # setpoint and actuals
        self.data["summer_winter"] = await self._async_read_int16_from_register(
            CALL_TYPE_REGISTER_HOLDING, STATE_READ_SEASON_REGISTER
        )

        if self.data["summer_winter"] == MODE_WINTER:  # winter
            self.data["winter_temperature"] = await self._async_read_temp_from_register(
                CALL_TYPE_REGISTER_HOLDING, TARGET_TEMPERATURE_WINTER_REGISTER
            )
            self.data["target_temperature"] = self.data["winter_temperature"]
        else:  # summer
            self.data["summer_temperature"] = await self._async_read_temp_from_register(
                CALL_TYPE_REGISTER_HOLDING, TARGET_TEMPERATURE_SUMMER_REGISTER
            )
            self.data["target_temperature"] = self.data["summer_temperature"]

        self.data["current_temperature"] = await self._async_read_temp_from_register(
            CALL_TYPE_REGISTER_HOLDING, ACTUAL_AIR_TEMPERATURE_REGISTER
        )

        # state heating/cooling/fan only/off
        self.data["on_off"] = await self._async_read_int16_from_register(
            CALL_TYPE_REGISTER_HOLDING, STATE_READ_ON_OFF_REGISTER
        )
        if self.data["on_off"]:
            self.data["fan_only"] = await self._async_read_int16_from_register(
                CALL_TYPE_REGISTER_HOLDING, STATE_READ_FAN_ONLY_REGISTER
            )
            self.data["ev_water"] = await self._async_read_int16_from_register(
                CALL_TYPE_REGISTER_HOLDING, STATE_READ_EV_WATER_REGISTER
            )
            if self.data["fan_only"] == MODE_ON:
                self.data["hvac_mode"] = HVACMode.FAN_ONLY
                self.data["hvac_action"] = HVACAction.FAN
            elif self._summer_winter == MODE_SUMMER:
                self.data["hvac_mode"] = HVACMode.COOL
                if self.data["ev_water"] == WATER_CIRCULATING:
                    self.data["hvac_action"] = HVACAction.COOLING
                else:
                    self.data["hvac_action"] = HVACAction.IDLE
            else:
                self.data["hvac_mode"] = HVACMode.HEAT
                if self.data["ev_water"] == WATER_CIRCULATING:
                    self.data["hvac_action"] = HVACAction.HEATING
                else:
                    self.data["hvac_action"] = HVACAction.IDLE
        else:
            self.data["hvac_mode"] = HVACMode.OFF
            self.data["hvac_action"] = HVACAction.OFF

        # fan speed

        fan_auto = await self._async_read_int16_from_register(
            CALL_TYPE_REGISTER_HOLDING, STATE_READ_FAN_AUTO_REGISTER
        )
        if fan_auto == MODE_ON:
            self.data["fan_mode"] = FAN_AUTO
        else:
            fan_min = await self._async_read_int16_from_register(
                CALL_TYPE_REGISTER_HOLDING, STATE_READ_FAN_MIN_SPEED_REGISTER
            )
            if fan_min == MODE_ON:
                self.data["fan_mode"] = FAN_LOW
            else:
                fan_med = await self._async_read_int16_from_register(
                    CALL_TYPE_REGISTER_HOLDING, STATE_READ_FAN_MED_SPEED_REGISTER
                )
                if fan_med == MODE_ON:
                    self.data["fan_mode"] = FAN_MEDIUM
                else:
                    fan_max = await self._async_read_int16_from_register(
                        CALL_TYPE_REGISTER_HOLDING,
                        STATE_READ_FAN_MAX_SPEED_REGISTER,
                    )
                    if fan_max == MODE_ON:
                        self.data["fan_mode"] = FAN_HIGH
                    else:
                        self.data["fan_mode"] = FAN_AUTO  # should never arrive here...

        self.data["t1_alarm"] = await self._async_read_int16_from_register(
            CALL_TYPE_REGISTER_HOLDING, ALARM_T1_REGISTER
        )

        self.data["t3_alarm"] = await self._async_read_int16_from_register(
            CALL_TYPE_REGISTER_HOLDING, ALARM_T3_REGISTER
        )

        self.data["water_drain"] = await self._async_read_int16_from_register(
            CALL_TYPE_REGISTER_HOLDING, ALARM_WATER_DRAIN_REGISTER
        )

        self.data["exchanger_temperature"] = await self._async_read_temp_from_register(
            CALL_TYPE_REGISTER_HOLDING, ACTUAL_WATER_TEMPERATURE_REGISTER
        )

    # Based on _async_read_register in ModbusThermostat class
    async def _async_read_int16_from_register(
        self, register_type: str, register: int
    ) -> int:
        """Read register using the Modbus hub slave."""

        result = await self.hub.async_pymodbus_call(
            self.modbus_slave, register, 1, register_type
        )
        if result is None:
            _LOGGER.error("Error reading value from Climaveneta iMXW modbus adapter")
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
