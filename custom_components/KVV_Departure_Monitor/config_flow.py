from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant import config_entries

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from .api import KVVApi
from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class ExampleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Example Integration."""

    VERSION = 1

    def __init__(self) -> None:
        # Zwischenspeicher für den Flow
        self.search_name: str | None = None
        self.found_points: list[dict] = []

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return KVVOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Erster Schritt: Nutzer gibt einen Suchbegriff ein"""
        errors = {}

        if user_input is not None:
            self.search_name = user_input["stop_name"]
            api = KVVApi(self.hass)

            try:
                self.found_points = await api.get_points_by_name(self.search_name)

                if not self.found_points:
                    errors["base"] = "no_points_found"
                else:
                    # Wenn Stationen gefunden wurden, gehe zum nächsten Schritt
                    return await self.async_step_station()
            except Exception as e:
                _LOGGER.error(f"Fehler bei der API-Abfrage: {e}")
                errors["base"] = "api_error"

        schema = vol.Schema(
            {vol.Required("stop_name", default=self.search_name or ""): cv.string}
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_station(
        self, user_input=None
    ) -> config_entries.ConfigFlowResult:
        """Zweiter Schritt: Nutzer wählt eine Station aus"""
        errors = {}

        if not self.found_points:
            return await self.async_step_user()

        # Mapping von Name → ID
        station_mapping = {p["name"]: p["id"] for p in self.found_points}

        if user_input is not None:
            selected_name = user_input["station"]
            selected_station_id = station_mapping[selected_name]

            return self.async_create_entry(
                title=f"KVV: {selected_name}",
                data={
                    "stop_name": selected_name,
                    "station_id": selected_station_id,  # speichert NUR die ID
                },
            )

        schema = vol.Schema(
            {vol.Required("station"): vol.In(list(station_mapping.keys()))}
        )
        return self.async_show_form(
            step_id="station", data_schema=schema, errors=errors
        )


class KVVOptionsFlowHandler(config_entries.OptionsFlow):
    """Options-Flow für KVV Departure Monitor."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialisiert den Options-Flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Zeigt die Optionsseite und verarbeitet Änderungen."""
        if user_input is not None:
            # Speichere die neuen Optionen
            return self.async_create_entry(title="", data=user_input)

        # Standardwert verwenden, falls noch nichts konfiguriert ist
        update_interval = self.config_entry.options.get(
            "update_interval", DEFAULT_UPDATE_INTERVAL
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "update_interval",
                        default=update_interval,
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
                }
            ),
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
