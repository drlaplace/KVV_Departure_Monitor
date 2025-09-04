from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from .api import KVVApi
from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
    CONF_STOP,
    CONF_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class ExampleConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Example Integration."""

    VERSION = 1

    def __init__(self) -> None:
        # Zwischenspeicher für den Flow
        self.search_name: str | None = None
        self.found_points: list[dict] = []

    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        # Remove this method and the ExampleOptionsFlowHandler class
        # if you do not want any options for your integration.
        return ExampleOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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

    async def async_step_station(self, user_input=None) -> ConfigFlowResult:
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


class ExampleOptionsFlowHandler(OptionsFlow):
    """Handles the options flow."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if user_input is not None:
            options = self.config_entry.options | user_input
            return self.async_create_entry(title="", data=options)

        # It is recommended to prepopulate options fields with default values if available.
        # These will be the same default values you use on your coordinator for setting variable values
        # if the option has not been set.
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): (vol.All(vol.Coerce(int), vol.Clamp(min=MIN_SCAN_INTERVAL))),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
