# Agenten-Übergabe

Dieses Repository enthält die HACS-Integration und ihre separat betriebene SDB-Bridge.
Vor Gerätezugriff README und docs/bridge.md lesen.
Nur dokumentiertes Modell und Firmware akzeptieren; Guards nicht umgehen.
Keine AUL-Aliase, Home-/Autostart-vconf-Werte oder CleanFrame-Pakete verändern.
Für eine vom Besitzer beauftragte Migration des Entwicklerhosts darf ausschließlich
`db/sdk/develop/ip` nach gesichertem Readback gezielt geändert werden. Vorherigen
Wert lokal sichern; bestehenden SDB-Client danach trennen und vom Zielhost testen.
Kein pauschales Zurücksetzen und keine gleichzeitigen SDB-Verbindungen.
Befehle nie automatisch wiederholen, wenn ihr Ausgang unklar ist.
SDB kann Aufträge wiederholen: persistente Nonce-Guards erhalten.
Shell-Dateien auf dieser Firmware über `cat <Pfad>|bash` einspeisen; direktes
`bash <Pfad>` wird wegen fehlender Dateisignatur verweigert.
Die bestehende CleanFrame-App wird aktiv vom Besitzer verändert: nicht überschreiben.
Keine Tokens, privaten Adressen, SDK-/Firmware-Binaries oder Rohlogs committen.
Tests: `python3 -m unittest discover -s tests -v`, `python3 scripts/check_repo.py`,
`python -m pytest tests_ha -q` mit Home Assistant 2026.10.4; nativen Helfer bauen.
Nach Änderungen Softwaretests, Geräteantwort und Sichtprüfung getrennt berichten.

App-Build-Kontext nach Bridge-/Launcher-Änderungen mit `python3 scripts/prepare_addon.py`
aktualisieren; CI prüft mit `--check`, dass die Kopien nicht abweichen.
Den Entwicklungsserver nicht dauerhaft als Produktions-Bridge verwenden.
