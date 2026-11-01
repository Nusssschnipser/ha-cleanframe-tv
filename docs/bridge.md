# Die lokale Steuerbrücke

Für den Betrieb direkt auf Home Assistant siehe zuerst die
[HA-App-Anleitung](../cleanframe_tv_bridge/DOCS.md). Die folgenden Schritte betreffen
den alternativen separaten Rechner.

HACS installiert nur `custom_components/cleanframe_tv`. Die Bridge läuft separat
auf dem Rechner, der bereits als Entwicklerhost des TVs freigegeben ist.

## Voraussetzungen

- Samsung GQ65Q95TDTXZG, Firmware T-NKMDEUC-2743.0, Tizen 5.5.
- TV eingeschaltet und bestehender SDB-Entwicklerzugang.
- Python 3.12 oder neuer, vorhandenes Samsung-SDB und .NET SDK zum Bauen.
- CleanFrame bereits installiert; Samsung-Escape-Alias bereits eingerichtet.
- Die vorhandene TV-.NET-3-Laufzeit wird genutzt, keine neue Runtime installieren.

## Einrichtung

```sh
git clone https://github.com/Nusssschnipser/ha-cleanframe-tv.git
cd ha-cleanframe-tv
dotnet build native-launcher/Launcher.csproj -o native-launcher/out
mkdir -p .local
cp examples/bridge.json .local/bridge.json
```

In der lokalen JSON-Datei die Platzhalter ersetzen:

| Feld | Inhalt |
| --- | --- |
| `tv` | IPv4 des TVs |
| `host` | LAN-IPv4 dieses Entwicklerrechners, vom TV erreichbar |
| `listen` | gleiche Adresse wie `host` |
| `sdb` | absoluter Pfad zur vorhandenen SDB-Datei |
| `port` | 8767 |
| `allow_clients` | konkrete IPv4-Adresse des Home-Assistant-Rechners als Liste |
| `apps` | optionales Objekt `App-ID: Anzeigename`, ersetzt den Standardkatalog |

```sh
python3 -m bridge.server --config .local/bridge.json
```

Die Bridge startet ohne App-Start oder Konfigurationsänderung auf dem TV. Erst
beim Button-Aufruf wird der versionsgebundene native Helfer bei Bedarf übertragen.
Für einen dauerhaften Dienst die [systemd-Vorlage](../examples/cleanframe-tv-bridge.service)
an Pfade und den bestehenden SDB-Benutzer anpassen. Nur eine Bridge pro TV betreiben.

Verbindungen: HA → Bridge TCP 8767; Bridge → TV TCP 8001 und 26101;
TV → Bridge dynamischer TCP-Rückkanal. Der TV muss weiterhin diesen Rechner als
Entwicklerhost freigeben. Eine Container-IP darf nicht mit der erreichbaren
LAN-IP verwechselt werden.

Bei Änderung von `apps`: Bridge neu starten und Integration in Home Assistant
neu laden. Die bei der Einrichtung bekannten Apps werden als Buttons angelegt.

## Technischer Ablauf

Der native Launcher prüft UID 901, Firmware und einen bekannten Kontrollalias.
Die eigentlichen Starts erfolgen für UID 5001. Er schreibt keine Aliase und keine
vconf-Werte. Der Escape-Alias wird nur geprüft, wenn Samsung Home angefordert wird.

SDB-Shell-Befehle sind auf dieser Firmware eingeschränkt. Die Bridge verwendet den
zuvor am Eigentümergerät untersuchten Appinstall-Dateinamen-/Callback-Transport.
Shell-Dateien werden über `cat <Pfad>|bash` eingespeist: `bash <Pfad>` wird von der
Firmware wegen fehlender Dateisignatur verweigert. Dies ist kein offizielles
Samsung-Steuerprotokoll und kann durch Firmwareänderungen ausfallen.

Die Bridge nimmt nur App-IDs aus ihrer lokalen Freigabeliste oder den festen
TV-Einstellungsablauf an. Keine allgemeinen Shell-Befehle über HTTP.

Jeder Auftrag hat eine Zufalls-ID. Der native Helfer legt exklusiv einen Guard an,
damit SDB-Wiederholungen nicht mehrfach Apps starten. Aufträge werden nicht
automatisch wiederholt; bei ausbleibender Bestätigung das Bild und lokale Logs
prüfen. Erfolgreiche Rückgabe bedeutet angenommener Startauftrag, nicht sichtbare App.

## Dateien und Rücknahme

Private Diagnosen stehen in `.local/evidence/` und bleiben außerhalb von Git.
Auf dem TV entstehen im SDK-Temporärverzeichnis:

- `cf-ha-<Buildhash>/`: Launcher-Dateien;
- `ha-<Request-ID>.sh`: Auftrag;
- `cf-ha-once-<Request-ID>`: Wiederholungsschutz;
- `cf-ha-result-<Request-ID>.txt`: Ergebnis.

Nicht während laufender SDK-Aufträge löschen. Bei längerer Nutzung nach Stoppen
der Bridge konkrete alte IDs prüfen und aufräumen. Keine pauschale Löschung des
SDK-Verzeichnisses. Pro Bridge-Prozess werden maximal 10.000 Aufträge angenommen.

Zum Entfernen: HA-Integration entfernen, Bridge-Dienst stoppen/deaktivieren,
Integration in HACS deinstallieren und HA neu starten. Die bestehende native
Home-Zuordnung und CleanFrame-App bleiben unverändert.
