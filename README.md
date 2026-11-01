# CleanFrame TV Native – Home Assistant / HACS

Lokale App- und Menüsteuerung für den **Samsung GQ65Q95TDTXZG**, Firmware
**T-NKMDEUC-2743.0**, mit bereits eingerichtetem SDB-Entwicklerzugang und CleanFrame.

Buttons: **CleanFrame, Samsung Home, Fernsehen, TV-Einstellungen, ARD Mediathek,
ZDF**. Zusätzliche App-IDs können in der Bridge freigegeben werden.

**Wichtig:** HACS installiert die Home-Assistant-Integration. Zusätzlich muss die
mitgelieferte Python-Bridge auf dem bereits freigegebenen Entwicklerrechner laufen.
Die Integration verbindet sich mit dieser Bridge; sie benötigt selbst kein SDB.
Es wird kein Samsung-, SmartThings- oder Home-Assistant-Token benötigt. Der
bestehende Entwicklerzugang und die Freigabe der HA-IP in der Bridge sind nötig.

## Installation über HACS

1. HACS öffnen → Menü → **Benutzerdefinierte Repositories**.
2. `https://github.com/Nusssschnipser/ha-cleanframe-tv` eintragen; Typ **Integration**.
3. **CleanFrame TV Native** herunterladen und Home Assistant neu starten.
4. [Die Bridge einrichten](docs/bridge.md), sofern sie noch nicht läuft.
5. **Einstellungen → Geräte & Dienste → Integration hinzufügen → CleanFrame TV Native**.
6. **IP des Bridge-Rechners** und Port **8767** eintragen, nicht die TV-Adresse.

Danach die Buttons des neuen Geräts zum Dashboard hinzufügen. In Automationen
verwenden sie die normale Aktion `button.press` mit ihrer jeweiligen Entity-ID.
Der TV muss eingeschaltet sein; bei ausgeschaltetem TV sind die Buttons nicht
verfügbar. Der Status wird alle 30 Sekunden gelesen.

Dieses Projekt ist ein benutzerdefiniertes HACS-Repository, kein Bestandteil des
HACS-Standardkatalogs. Manuell kann `custom_components/cleanframe_tv` nach
`/config/custom_components/cleanframe_tv` kopiert werden.

## Funktionsumfang und Grenzen

- Startet Apps über `aul_launch_app_for_uid` für den TV-Benutzer 5001.
- TV-Einstellungen: Fernsehen starten, danach das Menü anfordern, ohne auf einen
  JavaScript-Callback in der suspendierten CleanFrame-App zu warten.
- Samsung Home verwendet den **bereits vorhandenen** Alias `org.cleanframe.samsung-home`.
  Die Integration legt diesen Alias nicht an.
- Verändert weder die Home-Tasten-Zuordnung noch CleanFrame-Dateien oder vconf-Werte.
- Kein Einschalten, Lautstärkeregler oder allgemeiner Fernbedienungsersatz enthalten.
- Nur das dokumentierte Modell/Firmwarepaar ist freigegeben.
- Ein bestätigter nativer Startauftrag ist **keine Bestätigung des sichtbaren Bildes**.

## Nachweisstand – 1. November 2026

- Bridge-Protokoll und HA-Client wurden gemeinsam am eingeschalteten TV getestet.
- Alle sechs Startaufträge wurden vom nativen Launcher angenommen.
- CleanFrame wurde anschließend als `running=true`, `visible=true` zurückgelesen.
- ARD/ZDF: Samsung-HTTP-Status meldete beim Test `running=false`, `visible=false`,
  trotz erfolgreicher nativer Rückgabe. Sichtbares Funktionieren noch **nicht bestätigt**.
- Für Systemmenüs liefert diese HTTP-Schnittstelle keinen verwertbaren Status.
  Sichtprüfung von Samsung Home, Fernsehen und TV-Einstellungen steht noch aus.
- 8 Bridge-Tests und 6 Tests mit echten HA-2026.10.4-Klassen und simuliertem I/O
  bestanden; nativer Helfer gebaut. Noch keine Installation in einer realen HA-Instanz.

Diese erste Version bitte entsprechend als experimentell behandeln. Ergebnisse
nicht mit den früheren, unabhängig geprüften CleanFrame-UI-Aktionen verwechseln.

## Zugriff und Fehler

Die Bridge akzeptiert nur konfigurierte Client-IPv4-Adressen und erlaubte Apps.
HTTP ist nicht verschlüsselt; die IP-Freigabe ist keine kryptografische Anmeldung.
Nur im vertrauenswürdigen LAN betreiben, nicht öffentlich oder über einen offenen
Proxy erreichbar machen. Die Bridge stellt keine allgemeine Shell-API bereit.

Bei einem Timeout ist der Ausführungszustand unbekannt. Es gibt keine automatische
Wiederholung; zuerst das TV-Bild prüfen. Persistente Nonce-Guards verhindern
Doppelausführung desselben SDK-Auftrags. Details: [Bridge und Betrieb](docs/bridge.md).

## Entwicklung

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_repo.py
dotnet build native-launcher/Launcher.csproj -o native-launcher/out
# Separates venv: homeassistant==2026.10.4 pytest pytest-asyncio
python -m pytest tests_ha -q
```

Keine Firmware-/SDK-Binaries, Zertifikate, Tokens oder privaten Netzadressen im
Repository. Die Original-CleanFrame-App stammt von
[nthnclrk/CleanFrame](https://github.com/nthnclrk/CleanFrame). Keine offizielle
Samsung-Integration. MIT-Lizenz; siehe [LICENSE](LICENSE).
