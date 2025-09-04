import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from .api import KVVApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


PLATFORMS: list[str] = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """
    Wird aufgerufen, wenn der Benutzer die Integration über den Config Flow einrichtet.
    """
    _LOGGER.debug("Starte Setup für KVV-Integration: %s", entry.data)

    # Erzeuge API-Instanz und speichere sie global
    api = KVVApi(hass)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"api": api}

    try:
        # Testabfrage: Ist die API erreichbar?
        station_id = entry.data.get("station_id")
        if station_id:
            departures = await api.get_departures_by_station_id(station_id, limit=1)
            _LOGGER.debug("KVV Testabfrage erfolgreich: %s", departures)
    except Exception as e:
        _LOGGER.error("KVV API nicht erreichbar: %s", e)
        raise ConfigEntryNotReady from e

    # Lade Sensor-Plattform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """
    Wird aufgerufen, wenn der Benutzer die Integration entfernt.
    """
    _LOGGER.debug("Entlade KVV-Integration: %s", entry.entry_id)

    # Sensoren entladen
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
