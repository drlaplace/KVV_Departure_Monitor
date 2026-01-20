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
        self.search_name = None
        self.found_points = []
        self.selected_station_id = None
        self.selected_station_name = None
        self.serving_lines = []

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

            # ✅ DEBUG HIER
            _LOGGER.info(
                "KVV ConfigFlow: ausgewählte Station: name='%s', id='%s'",
                selected_name,
                selected_station_id,
            )
            self.selected_station_name = selected_name
            self.selected_station_id = selected_station_id

            # api = KVVApi(self.hass)
            # self._serving_lines = await api.get_serving_lines(selected_station_id)

            return await self.async_step_lines()

        schema = vol.Schema(
            {vol.Required("station"): vol.In(list(station_mapping.keys()))}
        )
        return self.async_show_form(
            step_id="station", data_schema=schema, errors=errors
        )

    async def async_step_lines(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Dritter Schritt: Auswahl der Serving Lines (Line + Direction)"""

        errors = {}

        if not getattr(self, "selected_station_id", None):
            return self.async_abort(reason="station_not_set")

        api = KVVApi(self.hass)

        raw: list[dict] = []

        try:
            # ✅ RICHTIGE QUELLE
            raw = await api.get_serving_lines(self.selected_station_id)
        except Exception as e:
            _LOGGER.error("Fehler beim Laden der Serving Lines: %s", e)
            errors["base"] = "api_error"

        if not raw:
            errors["base"] = "no_lines_found"

        options: dict[str, str] = {}
        self._line_map: dict[str, dict] = {}

        _LOGGER.info(
            "RAW: %s",
            raw,
        )

        for entry in raw:
            mode = entry.get("mode", {})
            diva = mode.get("diva", {})

            line_id = diva.get("line")  # z.B. "22305"
            dir_code = diva.get("dir")  # "H" / "R"

            number = mode.get("number")  # "S5"
            destination = mode.get("destination")  # "Wörth (Rhein)"

            _LOGGER.info(
                "KVV ConfigFlow: ausgewählte Linien: %s → %s %s %s",
                number,
                destination,
                dir_code,
                line_id,
            )

            if not all([line_id, dir_code, number, destination]):
                continue

            label = f"{number} → {destination}"
            options[label] = label

            self._line_map[label] = {
                "line": number,
                "line_id": line_id,
                "dir": dir_code,  # Richtungscode
            }

        if not options:
            return self.async_show_form(step_id="lines", errors=errors)

        if user_input is not None:
            selected = user_input["lines"]

            selected_lines = [self._line_map[k] for k in selected]

            return self.async_create_entry(
                title=f"KVV: {self.selected_station_name}",
                data={
                    "stop_name": self.selected_station_name,
                    "station_id": self.selected_station_id,
                    "serving_lines": selected_lines,
                },
            )

        return self.async_show_form(
            step_id="lines",
            data_schema=vol.Schema({vol.Required("lines"): cv.multi_select(options)}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return KVVOptionsFlowHandler(config_entry)


class KVVOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        super().__init__()
        self._entry_id = config_entry.entry_id

    @property
    def config_entry(self):
        """Liefert das aktuelle ConfigEntry."""
        return self.hass.config_entries.async_get_entry(self._entry_id)

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
