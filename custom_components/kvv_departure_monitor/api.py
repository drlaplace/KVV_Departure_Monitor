import logging
import asyncio
from aiohttp import ClientError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)


class KVVApi:
    # Stopfinder-URL (Stationssuche)
    BASE_URL = "https://www.kvv.de/tunnelEfaDirect.php"
    # Abfahrtsmonitor-URL
    DEPARTURE_URL = "https://projekte.kvv-efa.de/sl3-alone/XSLT_DM_REQUEST"

    def __init__(self, hass):
        """Initialisiert die API und nutzt die Home Assistant HTTP-Session."""
        self._hass = hass
        self._session = async_get_clientsession(hass)

    async def _get(self, url, params):
        """Generische GET-Anfrage mit Fehlerbehandlung."""
        try:
            async with self._session.get(url, params=params, timeout=15) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status} bei Anfrage an {url}")
                content_type = response.headers.get("Content-Type", "")
                if (
                    "application/json" not in content_type
                    and "text/json" not in content_type
                ):
                    text_preview = await response.text()
                    raise Exception(
                        f"Unerwarteter Content-Type ({content_type}). "
                        f"URL: {response.url} - Antwort: {text_preview[:150]}"
                    )
                return await response.json()
        except asyncio.TimeoutError:
            raise Exception("Timeout bei der API-Anfrage")
        except ClientError as e:
            raise Exception(f"Fehler bei der API-Anfrage: {e}")

    async def get_points_by_name(self, name: str):
        """Sucht Haltestellen anhand eines Namens."""
        params = {
            "action": "XSLT_STOPFINDER_REQUEST",
            "coordOutputFormat": "WGS84[dd.ddddd]",
            "name_sf": name,
            "outputFormat": "JSON",
            "type_sf": "any",
        }

        data = await self._get(self.BASE_URL, params)
        if not data:
            return []

        try:
            stop_finder = data.get("stopFinder", {})
            points_data = stop_finder.get("points", {})

            if isinstance(points_data, dict):
                points = points_data.get("point", [])
                if isinstance(points, dict):
                    points = [points]
            elif isinstance(points_data, list):
                points = points_data
            else:
                points = []

            results = []
            for p in points:
                if not isinstance(p, dict):
                    continue

                # Nur echte Haltestellen
                if p.get("anyType") != "stop":
                    continue

                raw_name = p.get("name", "")
                if not raw_name:
                    continue

                ref = p.get("ref", {})
                if not isinstance(ref, dict):
                    continue

                station_id = ref.get("id")
                if not station_id:
                    continue

                results.append(
                    {
                        "name": raw_name,
                        "id": station_id,
                    }
                )
            return results

        except Exception as e:
            raise Exception(f"Fehler beim Verarbeiten der Daten: {e}")

    async def get_departures_by_station_id(
        self,
        station_id: str,
        limit: int = 10,
        allowed_lines: list[dict] | None = None,
    ):
        """
        Holt die nächsten Abfahrten an einer bestimmten Haltestelle.
        WICHTIG: Nutzt ausschließlich DEPARTURE_URL.
        """
        params = {
            "outputFormat": "JSON",
            "coordOutputFormat": "WGS84[dd.ddddd]",
            "depType": "stopEvents",
            "locationServerActive": "1",
            "mode": "direct",
            "name_dm": station_id,
            "type_dm": "stop",
            "useOnlyStops": "1",
            "useRealtime": "1",
            "limit": limit,
        }

        departures: list[dict] = []  # ✅ IMMER initialisieren

        data = await self._get(self.DEPARTURE_URL, params)
        if not data:
            _LOGGER.warning("Keine Daten von der KVV-Abfahrts-API erhalten")
            return departures

        try:
            departure_list = data.get("departureList", [])
            if not isinstance(departure_list, list):
                return departures

            # 🔑 Filter-Set vorbereiten
            allowed = None
            if allowed_lines:
                allowed = {(l["line_id"], l["dir"]) for l in allowed_lines}

            for dep in departure_list:
                serving = dep.get("servingLine", {})
                proj = serving.get("liErgRiProj", {})
                # mode = dep.get("mode", {})

                line_id = proj.get("line")
                dir_code = proj.get("direction")

                if allowed and (line_id, dir_code) not in allowed:
                    continue

                departures.append(
                    {
                        "line": serving.get("number", "?"),
                        "direction": serving.get("direction", "Unbekannt"),
                        "countdown": dep.get("countdown", "?"),
                        "realtime": bool(dep.get("realtime", False)),
                        "dateTime": dep.get("dateTime"),
                        "realDateTime": dep.get("realDateTime"),
                    }
                )
            return departures

        except Exception as e:
            _LOGGER.error("Fehler beim Verarbeiten der Abfahrtsdaten: %s", e)
            return departures

    async def get_serving_lines(self, station_id: str):
        """
        Liefert alle Serving Lines einer Haltestelle
        Quelle: servingLines.lines (NICHT departureList)
        """
        params = {
            "outputFormat": "JSON",
            "coordOutputFormat": "WGS84[dd.ddddd]",
            "depType": "stopEvents",
            "locationServerActive": "1",
            "mode": "direct",
            "name_dm": station_id,
            "type_dm": "stop",
            "useOnlyStops": "1",
            "useRealtime": "1",
            "limit": 1,  # reicht – servingLines ist unabhängig von limit
        }

        data = await self._get(self.DEPARTURE_URL, params)
        if not data:
            return []

        serving = data.get("servingLines", {})
        lines = serving.get("lines", [])

        if not isinstance(lines, list):
            return []

        return lines
