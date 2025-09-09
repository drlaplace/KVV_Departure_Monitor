
# **KVV Departure Monitor** 🚆

![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-blue)
![Version](https://img.shields.io/github/v/tag/<dein-user>/kvv-departure-monitor?label=Release)

[![Deutsch](https://img.shields.io/badge/Sprache-Deutsch-blue)](README.md)
[![English](https://img.shields.io/badge/Language-English-green)](README_EN.md)

Der **KVV Departure Monitor** ist eine benutzerdefinierte Home Assistant Integration,  
die Live-Abfahrtszeiten der **Karlsruher Verkehrsverbund (KVV)**-Haltestellen anzeigt.  
Die Daten stammen von der offiziellen **KVV API** und werden in Sensoren und Lovelace-Karten integriert.

---

## **Funktionen**
✅ Live-Abfahrtsdaten für jede KVV-Haltestelle  
✅ Unterstützung von Bahn, S-Bahn, Bus & Tram  
✅ Integration in Lovelace-Dashboards  
✅ Konfigurierbares Aktualisierungsintervall  
✅ Vollständige HACS-Unterstützung

---

## **Installation über HACS**
1. **HACS öffnen** → **Integrationen** → ⚙️ → **Benutzerdefiniertes Repository hinzufügen**
2. Repository-URL hinzufügen:

   ```
   https://github.com/dr_laplace/kvv-departure-monitor
   ```

3. Kategorie: **Integration** auswählen
4. Auf **Hinzufügen** klicken
5. Anschließend in Einstellungen → Geräte&Dienste → Integration hinzufügen → **KVV Departure Monitor** → **Installieren**


---

## **Manuelle Installation**
Falls du HACS nicht nutzen möchtest:
1. Lade das Repository als `.zip` herunter
2. Entpacke es nach:
   ```
   /config/custom_components/kvv_departure_monitor/
   ```
3. Home Assistant neu starten
4. Integration über **Einstellungen → Integrationen → Integration hinzufügen** auswählen

---

## **Konfiguration**
Nach der Installation kannst du die Integration über die Home Assistant Oberfläche konfigurieren:

1. Gehe zu **Einstellungen → Integrationen**
2. Klicke auf **Integration hinzufügen**
3. Wähle **KVV Departure Monitor**
4. Gib deine gewünschte **Haltestelle** ein
5. Wähle die Station aus der Vorschlagsliste
6. Fertig 🎉

---

## **Sensoren**
Jede konfigurierte Haltestelle erzeugt einen eigenen Sensor.

**Beispiel-Sensor:**
```yaml
sensor.kvv_abfahrten_berghausen_baden_hummelberg
```

**Beispiel-Attribute:**
```yaml
abfahrten:
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

## **Lovelace Beispielkarte**
Du kannst die Abfahrten in Lovelace anzeigen, z. B. mit meiner **kvv-departures-card**:

```yaml
type: custom:kvv-departure-card
entity: sensor.kvv_abfahrten_berghausen_baden_hummelberg
title: "Abfahrten an Berghausen Hummelberg"
max_items: 10
```
![Screenshot](https://github.com/drlaplace/kvv-departures-card/blob/main/images/kvv_departures_card.png)
## **Changelog**
### **v1.0.0**
- Erste stabile Version
- HACS-kompatibel
- Abfahrtsmonitor mit Countdown & Richtung
- Lovelace-Karte integriert

---

## **Lizenz**
Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).