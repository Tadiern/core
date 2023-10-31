"""Platform for the climaveneta iMXW and iLife2 AC."""
import logging

from pymodbus.exceptions import ModbusException

from homeassistant.components.modbus import CALL_TYPE_REGISTER_HOLDING, get_hub
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_SLAVE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CLIMAVENETA_IMXW,
    CONF_HUB,
    DEVICE_TYPE,
    DOMAIN,
    ILIFE_STATE_READ_REGISTER,
    IMXW_STATE_READ_ON_OFF_REGISTER,
)
from .coordinator import ClimavenetaCoordinator

PLATFORMS = [Platform.CLIMATE]


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up platform from a ConfigEntry."""

    device_type = entry.data[DEVICE_TYPE]
    hub = get_hub(hass, entry.data[CONF_HUB])
    slave_id = entry.data[CONF_SLAVE]
    name = entry.data[CONF_NAME]
    try:
        if device_type == CLIMAVENETA_IMXW:
            result = await hub.async_pb_call(
                slave_id, IMXW_STATE_READ_ON_OFF_REGISTER, 1, CALL_TYPE_REGISTER_HOLDING
            )
        else:
            result = await hub.async_pb_call(
                slave_id, ILIFE_STATE_READ_REGISTER, 1, CALL_TYPE_REGISTER_HOLDING
            )
    except ModbusException as exception_error:
        _LOGGER.error(str(exception_error))
        raise ConfigEntryNotReady("Climaveneta device error") from exception_error

    if result is None:
        _LOGGER.error("Error reading value from Climaveneta modbus adapter")
        raise ConfigEntryNotReady("Climaveneta API timed out")

    coordinator = ClimavenetaCoordinator(hass, device_type, hub, slave_id, name)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload Climaveneta config entry."""

    # our components don't have unload methods so no need to look at return values
    for platform in PLATFORMS:
        await hass.config_entries.async_forward_entry_unload(config_entry, platform)

    return True
