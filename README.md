# CleanFrame TV Native – Home Assistant / HACS

Lokale App- und Menüsteuerung für den **Samsung GQ65Q95TDTXZG**, Firmware
**T-NKMDEUC-2743.0**, mit bereits eingerichtetem SDB-Entwicklerzugang und CleanFrame.

Buttons: **CleanFrame, Samsung Home, Fernsehen, TV-Einstellungen, ARD Mediathek,
ZDF**. Zusätzliche App-IDs können in der Bridge freigegeben werden.

**Wichtig:** HACS installiert die Home-Assistant-Integration. Zusätzlich muss die
mitgelieferte Python-Bridge laufen: bevorzugt als HA-App, alternativ auf einem
freigegebenen separaten Rechner.
Die Integration verbindet sich mit dieser Bridge; sie benötigt selbst kein SDB.
Für App- und Menüsteuerung wird kein Samsung-, SmartThings- oder Home-Assistant-Token benötigt. Der
bestehende Entwicklerzugang und die Freigabe der HA-IP in der Bridge sind nötig.

## Bridge direkt auf Home Assistant (ab 0.2.0)

Für **Home Assistant OS/Supervised auf Intel/AMD 64 Bit** gibt es jetzt die
[App CleanFrame TV Bridge](cleanframe_tv_bridge/DOCS.md). Dieselbe Repository-URL
im **App-/Add-on-Store unter Repositories** hinzufügen und die App installieren.
So braucht der laufende Betrieb keinen Entwicklungsserver mehr. ARM/Green/Pi
werden von diesem SDB-Paket noch nicht unterstützt.

Für den Umzug anschließend die HACS-Integration aktualisieren, HA neu starten
und den Integrationseintrag **neu konfigurieren**: HA-LAN-IP statt bisheriger
Bridge-IP eintragen. Vorhandene Button-IDs bleiben erhalten. Der TV muss den
HA-Rechner als Entwicklerhost akzeptieren. Details stehen in der App-Anleitung.

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

## Ein/Aus und Lautstärke (Integration 0.3.0)

Unter **Einstellungen → Geräte & Dienste → CleanFrame TV → Neu konfigurieren**
zusätzlich die vorhandene `samsungtv`-Mediaplayer-Entität auswählen und die
MAC-Adresse der aktiven TV-Netzwerkschnittstelle für Wake-on-LAN eintragen.
Als Wake-on-LAN-Ziel kann die TV-IP (Unicast) oder eine Broadcast-Adresse
verwendet werden. Am Eigentümergerät wurde die direkte TV-IP konfiguriert.
Die Samsung-Integration muss bereits gekoppelt sein. Bridge-App 0.2.0 genügt.

Am selben CleanFrame-Gerät erscheint **TV-Steuerung** mit Einschalten,
Ausschalten und den von Samsung unterstützten Lautstärkeaktionen einschließlich
Regler und Stummschaltung. Bestehende App-Buttons und ihre IDs bleiben erhalten.
Das Einschalten sendet ein Magic Packet aus Home Assistant, keinen Power-Toggle.
Bei fehlendem Samsung-Status wird der Zustand als unbekannt angezeigt; eine
optimistische Einschaltbestätigung gibt es nicht. Offline-Lautstärkebefehle werden
abgewiesen. Wake-on-LAN setzt die entsprechende Netzwerkbereitschaft am TV voraus.

## Funktionsumfang und Grenzen

- Startet Apps über `aul_launch_app_for_uid` für den TV-Benutzer 5001.
- TV-Einstellungen: Fernsehen starten, danach das Menü anfordern, ohne auf einen
  JavaScript-Callback in der suspendierten CleanFrame-App zu warten.
- Samsung Home verwendet den **bereits vorhandenen** Alias `org.cleanframe.samsung-home`.
  Die Integration legt diesen Alias nicht an.
- Verändert weder die Home-Tasten-Zuordnung noch CleanFrame-Dateien oder vconf-Werte.
- Ab Integration 0.3.0: optionaler Mediaplayer für Ein/Aus, Lautstärke und Stummschaltung.
  Einschalten verwendet Wake-on-LAN. Ausschalten und Lautstärke verwenden die bereits
  gekoppelte offizielle Samsung-TV-Integration; deren lokale Kopplung bleibt erforderlich.
  In CleanFrame wird dafür kein zusätzlicher Token eingegeben.
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
- 11 Bridge-/App-Tests und 8 Tests mit echten HA-2026.10.4-Klassen und simuliertem I/O
  bestanden; nativer Helfer gebaut.
- HA-App und HACS-Integration 0.2.0 sind auf Home Assistant OS 18.4 (amd64/KVM),
  Core 2026.10.4 installiert. Die App läuft mit Autostart; die Integration ist geladen
  und alle sechs Buttons sind angelegt.
- Integration 0.3.1 ergänzt den am selben Gerät angelegten Mediaplayer. Auf dem
  tatsächlichen HA-Host getestet: Ausschalten und erneutes Einschalten, Lautstärke
  8 → 9 → 8, Lauter/Leiser und Stummschaltung mit Rückstellung.
- Wake-on-LAN wurde zuletzt mit der TV-IP als Ziel erfolgreich geprüft. Der TV
  benötigte länger als das zehnsekündige Prüfzeitfenster für die On-Rückmeldung.
- Native App-/Menüsteuerung vom HA-Host ist noch nicht bestätigt: SDB meldet einen
  Befehlsfehler. Die sechs Buttons sind angelegt, aber noch nicht erfolgreich
  vom HA-Host am TV ausgeführt. Der Entwicklungsdienst bleibt deaktiviert.

Diese erste Version bitte entsprechend als experimentell behandeln. Ergebnisse
nicht mit den früheren, unabhängig geprüften CleanFrame-UI-Aktionen verwechseln.

Die HA-App 0.2.0 wurde als Docker-Image gebaut und lokal gestartet; Status-API,
SDB-Start, persistente Konfiguration und Ablehnung unzulässiger Apps wurden geprüft.
Die Installation auf dem tatsächlichen HA-Host ist erfolgt; die native
TV-Steuerung von dort ist noch nicht bestätigt.

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
