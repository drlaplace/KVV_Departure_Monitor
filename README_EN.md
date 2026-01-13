
# **KVV Departure Monitor** 🚆

![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-blue)
![Version](https://img.shields.io/github/v/tag/<dein-user>/kvv-departure-monitor?label=Release)

[![Deutsch](https://img.shields.io/badge/Sprache-Deutsch-blue)](README.md)
[![English](https://img.shields.io/badge/Language-English-green)](README_EN.md)

The **KVV Departure Monitor** is a custom **Home Assistant** integration  
that displays real-time departure times for **Karlsruher Verkehrsverbund (KVV)** stations.  
The data is fetched directly from the official **KVV API** and integrated into sensors and Lovelace cards.

---

## **Features**
✅ Live departure data for any KVV station  
✅ Supports trains, trams, S-Bahn & buses  
✅ Lovelace dashboard integration  
✅ Configurable update interval  
✅ Fully HACS compatible

---

## **Installation via HACS**
1. Open **HACS**
2. search KVV Departure Monitor and download
3. Restart Home Assistant
4. Then go to **Settings → Devices & Services → Add Integration → KVV Departure Monitor → Install**

---

## **Manual Installation**
If you prefer not to use HACS:
1. Download the repository as a `.zip`
2. Extract it into:
   ```
   /config/custom_components/kvv_departure_monitor/
   ```
3. Restart Home Assistant
4. Go to **Settings → Integrations → Add Integration → KVV Departure Monitor**

---

## **Configuration**
After installation, configure the integration via the Home Assistant UI:

1. Go to **Settings → Integrations**
2. Click **Add Integration**
3. Select **KVV Departure Monitor**
4. Enter the desired **station name**
5. Select the correct station from the suggestions
6. Done 🎉

---

## **Sensors**
Each configured station creates its own sensor.

**Example Sensor:**
```yaml
sensor.kvv_abfahrten_berghausen_baden_hummelberg
```

**Example Attributes:**
```yaml
departures:
  - line: "S5"
    direction: "Karlsruhe-Durlach"
    countdown: "2"
    realtime: true
    dateTime:
      year: "2025"
      month: "09"
      day: "05"
      hour: "10"
      minute: "24"
```

---

## **Lovelace Example Card**
You can display departures in Lovelace using my **kvv-departures-card**:

```yaml
type: custom:kvv-departures-card
entity: sensor.kvv_abfahrten_berghausen_baden_hummelberg
```

![Screenshot](https://github.com/drlaplace/kvv-departures-card/blob/main/images/kvv_departures_card.png)

---

## **Changelog**
### **v1.0.0**
- First stable release
- Fully HACS compatible
- Live departure monitor with countdown & direction
- Integrated Lovelace card support

---

## **License**
This project is licensed under the [MIT License](LICENSE).
