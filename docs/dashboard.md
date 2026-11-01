# App-Starts als Markdown-Karten

Die [fertige Kartenkonfiguration](../examples/dashboard-markdown.yaml) enthält
CleanFrame, Fernsehen, Netflix, Disney+, Apple TV, YouTube, Prime Video,
ARD Mediathek, ZDF, Samsung Home und TV-Einstellungen.

Im Home-Assistant-Dashboard **Bearbeiten → Karte hinzufügen → Manuell** wählen
und den vollständigen YAML-Inhalt einfügen. Jede Markdown-Karte startet per
Antippen ihren App-Button. Keine zusätzliche Frontend-Erweiterung erforderlich.
Die Entity-IDs wurden am bestehenden CleanFrame-Gerät geprüft. Bei einer anderen
Installation können sie abweichen; dann unter Entwicklerwerkzeuge → Zustände prüfen.

Voraussetzung: eine HA-Frontend-Version mit `tap_action` für Markdown-Karten,
wie in der [aktuellen HA-Dokumentation](https://www.home-assistant.io/dashboards/markdown/)
beschrieben. Der Fernseher muss eingeschaltet und die Bridge erreichbar sein.
Die Karten wecken den TV nicht automatisch.

## Zusätzliche Streaming-Apps freigeben

In der Konfiguration der **CleanFrame TV Bridge** die folgenden Einträge unter
`additional_apps` ergänzen. Bereits vorhandene zusätzliche Einträge beibehalten.
Diese IDs stammen aus der CleanFrame-Konfiguration des unterstützten Q95T;
auf anderen Modellen/Regionen können die IDs abweichen.

```yaml
additional_apps:
  - app_id: org.tizen.netflix-app
    name: Netflix
  - app_id: MCmYXNxgcu.DisneyPlus
    name: Disney+
  - app_id: com.samsung.tv.aria-video
    name: Apple TV
  - app_id: 9Ur5IzDKqV.TizenYouTube
    name: YouTube
  - app_id: org.tizen.primevideo
    name: Prime Video
```

Die Bridge-App neu starten und warten, bis sie erreichbar ist. Anschließend
unter Geräte & Dienste den CleanFrame-Integrationseintrag neu laden. Erst das
Neuladen legt die zusätzlichen Button-Entitäten an; die normale Statusabfrage
allein genügt nicht. Ein vollständiger HA-Neustart ist nicht erforderlich.

Ein erfolgreicher Startbefehl bestätigt die native Geräteantwort, nicht die
sichtbare App-Oberfläche oder den Anmeldestatus beim Streaming-Dienst.
