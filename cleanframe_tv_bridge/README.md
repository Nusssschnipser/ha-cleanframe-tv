# CleanFrame TV Bridge auf Home Assistant

Die App betreibt die bisher externe Bridge direkt auf Home Assistant OS oder
Supervised. **Intel/AMD 64 Bit (`amd64`)** wird unterstützt; ARM/Raspberry Pi/Green
wird mit diesem Samsung-SDB-Paket nicht unterstützt. Home Assistant Container/Core
hat keinen App-/Add-on-Store; dort ist ein separater Docker-Container erforderlich.

## Einrichtung

1. Unter **Einstellungen → Apps/Add-ons → App-/Add-on-Store → Repositories**
   `https://github.com/Nusssschnipser/ha-cleanframe-tv` hinzufügen.
2. **CleanFrame TV Bridge** installieren. Beim lokalen Image-Build werden der
   native Helfer gebaut und das SDB-Paket direkt von Tizen heruntergeladen. Kein
   Entwicklungssystem oder SDK muss auf dem HA-Host manuell installiert werden.
3. In der Konfiguration ausfüllen:
   - `tv_host`: LAN-IPv4 des Fernsehers;
   - `ha_host`: LAN-IPv4 des Home-Assistant-Rechners, keine Loopback-/Container-IP;
   - `port`: 8767;
   - `additional_apps`: optional zusätzliche Einträge mit `app_id` und `name`.
4. Der TV muss diesen HA-Rechner als Entwicklerhost akzeptieren. Falls nötig in
   Samsungs Apps-Entwicklermodus die bisherige Entwickler-IP durch die HA-LAN-IP
   ersetzen und den TV gemäß Samsung-Anleitung neu starten. Die bestehende
   CleanFrame-App weder deinstallieren noch neu installieren.
5. App starten, **Beim Booten starten** aktivieren und das Protokoll prüfen.
6. HACS-Integration **CleanFrame TV Native** auf Version 0.2.0 aktualisieren und
   HA neu starten. Unter Geräte & Dienste beim Eintrag **Neu konfigurieren**
   auswählen und die HA-LAN-IP mit Port 8767 eingeben. Die bestehende Config Entry
   und damit die Button-IDs bleiben dabei erhalten.
7. CleanFrame und die benötigten Apps/Menüs testen. Erst nach einem bestätigten
   Wechsel den alten externen Dienst stilllegen, falls dieser noch läuft.

HACS installiert die Buttons, der App-Store installiert die Bridge: dieselbe
Repository-URL wird dafür in zwei verschiedenen Bereichen eingetragen.

## Zugriffsrechte und Speicherung

Kein Samsung-/HA-Token erforderlich. Die App benötigt kein Supervisor-API-Token,
keine HA-Konfigurationsfreigabe und keinen privilegierten Container. Host-Netzwerk
ist für den dynamischen Rückkanal vom TV notwendig. HTTP-Befehle werden nur von
der konfigurierten HA-LAN-Adresse angenommen. HA Core verwendet sein Host-Netzwerk.

Diagnosen und generierte Bridge-Konfiguration liegen persistent unter `/data`.
Die App kann unabhängig vom Entwicklungsrechner starten. Das Samsung-SDB wird
beim Image-Build aus dem offiziellen Paket `sdb_4.2.35_ubuntu-64.zip` geladen und
gegen dessen SHA256 geprüft. SDK-Binaries werden nicht ins Git-Repository kopiert.

## Grenzen

Nur Samsung GQ65Q95TDTXZG mit T-NKMDEUC-2743.0. Ein anderer Firmwarestand wird vom
nativen Helfer abgelehnt. Die App konfiguriert weder Home-Tasten-Aliase noch vconf.
Alle bisherigen Einschränkungen bei Sichtbarkeit und Gerätetests aus der
Repository-README gelten weiter. Die Migration auf einen echten HA-Host muss
separat getestet werden; ein Container-Test auf dem Entwicklungsrechner ist dafür
kein Ersatz.
