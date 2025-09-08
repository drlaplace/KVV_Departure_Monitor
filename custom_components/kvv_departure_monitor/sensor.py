import logging
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL
from .api import KVVApi

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Setzt die Sensorplattform für die KVV-Integration auf."""

    stored_data = hass.data[DOMAIN][entry.entry_id]
    api = stored_data["api"]
    coordinator = stored_data.get("coordinator")

    if not coordinator:
        station_id = entry.data.get("station_id")
        coordinator = KVVDataCoordinator(hass, api, station_id, entry)
        await coordinator.async_config_entry_first_refresh()
        hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator

    async_add_entities([KVVDepartureSensor(coordinator, entry)])


class KVVDataCoordinator(DataUpdateCoordinator):
    """Koordiniert das Abrufen und Cachen der KVV-Abfahrtsdaten."""

    def __init__(
        self, hass: HomeAssistant, api: KVVApi, station_id: str, entry: ConfigEntry
    ):
        self.api = api
        self.station_id = station_id
        self.entry = entry

        update_interval = timedelta(
            seconds=entry.options.get("update_interval", DEFAULT_UPDATE_INTERVAL)
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"KVV Departure Monitor {station_id}",
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        """Lädt aktuelle Abfahrtsdaten von der KVV-API."""
        try:
            departures = await self.api.get_departures_by_station_id(
                self.station_id, limit=10
            )
            _LOGGER.debug(
                "Abfahrtsdaten für Station %s: %s", self.station_id, departures
            )
            return departures
        except Exception as e:
            _LOGGER.error("Fehler beim Abrufen der Abfahrtsdaten: %s", e)
            return []


class KVVDepartureSensor(CoordinatorEntity, SensorEntity):
    """Repräsentiert einen Sensor für KVV-Abfahrten."""

    def __init__(self, coordinator: KVVDataCoordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self_station_name = entry.data.get("stop_name", "Unbekannt")
        self._attr_name = f"KVV Abfahrten {entry.data.get('stop_name', 'Unbekannt')}"
        self._attr_unique_id = f"{entry.entry_id}_departures"

    @property
    def native_value(self):
        """Gibt die nächste Abfahrtszeit zurück."""
        data = self.coordinator.data
        if not data:
            return "Keine Daten"

        first_departure = data[0]
        # dateTime nutzen, falls vorhanden
        dt = first_departure.get("dateTime")
        hour = str(dt.get("hour", "??")).zfill(2)
        minute = str(dt.get("minute", "??")).zfill(2)
        countdown = first_departure.get("countdown")
        line = first_departure.get("line", "?")
        direction = first_departure.get("direction", "?")
        if countdown is not None:
            return f"{line} → {direction} {hour}:{minute} in {countdown} Min"

        _LOGGER.warning("Unbekanntes Abfahrtsformat: %s", first_departure)
        return "Unbekannt"

    @property
    def extra_state_attributes(self):
        """Gibt zusätzliche Infos über die nächsten Abfahrten zurück."""
        return {
            "station_name": self._station_name,
            "abfahrten": self.coordinator.data or []}
