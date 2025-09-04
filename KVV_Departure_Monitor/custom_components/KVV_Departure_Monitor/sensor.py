import logging
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .api import KVVApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=30)  # Sensor aktualisiert sich alle 30 Sekunden


async def async_setup_entry(hass: HomeAssistant, entry: ConfigType, async_add_entities):
    """
    Einrichtung des Sensors über den Config Flow.
    """
    api = KVVApi(hass)
    station_id = entry.data["station_id"]
    stop_name = entry.data["stop_name"]

    coordinator = KVVDataCoordinator(hass, api, station_id)

    await coordinator.async_config_entry_first_refresh()

    async_add_entities([KVVSensor(coordinator, stop_name, station_id)], True)


class KVVDataCoordinator(DataUpdateCoordinator):
    """Koordiniert die API-Abfragen und speichert die letzten bekannten Daten."""

    def __init__(self, hass: HomeAssistant, api: KVVApi, station_id: str):
        """Initialisiert den Coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="KVV Departures Coordinator",
            update_interval=SCAN_INTERVAL,
        )
        self.api = api
        self.station_id = station_id
        self._last_successful_data = []  # Hier speichern wir die letzten bekannten Daten
        self.api_status = "unknown"

    async def _async_update_data(self):
        """Holt die aktuellen Abfahrtsdaten von der API."""
        try:
            departures = await self.api.get_departures_by_station_id(
                self.station_id, limit=10
            )

            # Prüfen, ob wir Daten erhalten haben
            if departures:
                self._last_successful_data = departures
                self.api_status = "ok"
                return departures
            else:
                self.api_status = "unreachable"
                _LOGGER.warning("KVV API lieferte keine Daten zurück, nutze Cache.")
                return self._last_successful_data

        except Exception as e:
            self.api_status = "unreachable"
            _LOGGER.error(f"KVV API nicht erreichbar: {e}")
            # Nutze zuletzt bekannte Daten, falls vorhanden
            return self._last_successful_data


class KVVSensor(SensorEntity):
    """Sensor für die nächsten Abfahrten an einer Station."""

    def __init__(
        self, coordinator: KVVDataCoordinator, stop_name: str, station_id: str
    ):
        """Initialisiert den Sensor."""
        self.coordinator = coordinator
        self._attr_name = f"KVV Abfahrten {stop_name}"
        self._station_id = station_id
        self._stop_name = stop_name
        self._attr_unique_id = f"kvv_{station_id}"
        self._attr_icon = "mdi:train"
        self._attr_extra_state_attributes = {}

    @property
    def native_value(self):
        """Zeigt die nächste Abfahrt an."""
        departures = self.coordinator.data
        if departures and len(departures) > 0:
            dep = departures[0]
            line = dep.get("line", "?")
            direction = dep.get("direction", "Unbekannt")
            countdown = dep.get("countdown", "?")
            return f"{line} → {direction} ({countdown} Min)"
        return "Keine Abfahrten"

    @property
    def extra_state_attributes(self):
        """Zusätzliche Infos im Sensor anzeigen."""
        departures = self.coordinator.data or []
        attrs = {
            "station": self._stop_name,
            "station_id": self._station_id,
            "api_status": self.coordinator.api_status,
            "abfahrten": [],
        }

        for dep in departures:
            attrs["abfahrten"].append(
                {
                    "linie": dep.get("line"),
                    "richtung": dep.get("direction"),
                    "countdown_minuten": dep.get("countdown"),
                    "echtzeit": dep.get("realtime"),
                }
            )

        return attrs

    async def async_update(self):
        """Manuelles Update."""
        await self.coordinator.async_request_refresh()

    async def async_added_to_hass(self):
        """Callback, wenn der Sensor hinzugefügt wird."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
