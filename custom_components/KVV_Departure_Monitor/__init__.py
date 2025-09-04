import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import Platform
from .api import KVVApi
from .sensor import KVVDataCoordinator
from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[str] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Setzt die KVV-Integration auf, wenn der Benutzer sie über den Config Flow einrichtet."""
    _LOGGER.debug("Starte Setup für KVV-Integration: %s", entry.data)

    hass.data.setdefault(DOMAIN, {})

    # API erstellen
    api = KVVApi(hass)
    station_id = entry.data.get("station_id")

    # Testabfrage der API
    try:
        if station_id:
            test_departures = await api.get_departures_by_station_id(
                station_id, limit=1
            )
            _LOGGER.debug("KVV Testabfrage erfolgreich: %s", test_departures)
    except Exception as e:
        _LOGGER.error("KVV API nicht erreichbar: %s", e)
        raise ConfigEntryNotReady from e

    # Coordinator anlegen
    coordinator = KVVDataCoordinator(hass, api, station_id, entry)
    await coordinator.async_config_entry_first_refresh()

    # API + Coordinator gemeinsam in hass.data speichern
    hass.data[DOMAIN][entry.entry_id] = {"api": api, "coordinator": coordinator}

    # Sensor-Plattform laden
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Wird aufgerufen, wenn der Benutzer die Integration entfernt."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Wird bei Optionsänderung aufgerufen."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
