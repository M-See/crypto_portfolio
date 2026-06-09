# Crypto Portfolio for Home Assistant

Crypto Portfolio ist eine Custom Integration fuer Home Assistant. Sie holt
aktuelle Preise von CoinGecko und erzeugt Portfolio-Sensoren fuer Wert, Invest,
Gewinn und Gewinn in Prozent.

Die Integration ist so strukturiert, dass sie als HACS-Integration verwendet
werden kann:

```text
custom_components/crypto_portfolio/
hacs.json
README.md
```

## Lokal testen

Du brauchst kein eigenes Dockerfile. Die `docker-compose.yml` startet ein
fertiges Home-Assistant-Image und bindet diese Integration in die Testinstanz
ein.

Die lokale Testinstanz laeuft auf Port `8124`, damit sie nicht mit einer echten
Home-Assistant-Instanz auf Port `8123` kollidiert.

```powershell
docker compose up -d
```

Danach Home Assistant oeffnen:

```text
http://localhost:8124
```

Stoppen:

```powershell
docker compose stop
```

## Integration per UI hinzufuegen

1. In Home Assistant: **Einstellungen > Geraete & Dienste**.
2. **Integration hinzufuegen**.
3. Nach **Crypto Portfolio** suchen.
4. Portfolio-Name, Waehrung, Aktualisierungsintervall und Investments eintragen.

Die Investments werden als JSON in der Integrations-UI gepflegt, nicht in
`configuration.yaml`.

Beispiel:

```json
[
  {
    "coin_id": "bitcoin",
    "symbol": "BTC",
    "amount": 0.05,
    "invested": 1200
  },
  {
    "coin_id": "ethereum",
    "symbol": "ETH",
    "amount": 1.2,
    "invested": 2500
  }
]
```

`coin_id` ist die CoinGecko-ID, nicht zwingend das Symbol. Beispiele:

- `bitcoin`
- `ethereum`
- `cardano`
- `ripple`
- `solana`

Spaeter bearbeiten:

```text
Einstellungen > Geraete & Dienste > Crypto Portfolio > Konfigurieren
```

Darueber bekommst du ein kleines Menue:

- Allgemeine Einstellungen
- Coin hinzufuegen
- Coin bearbeiten
- Coin loeschen
- Erweiterter JSON-Editor
- JSON-Datei bearbeiten/importieren

Beim Bearbeiten oder Loeschen waehlt du den Coin per Dropdown aus. Nach dem
Speichern laedt Home Assistant die Integration neu.

Fuer jedes Portfolio legt die Integration zusaetzlich eine JSON-Datei an:

```text
/config/crypto_portfolio/<config-entry-id>.json
```

Der genaue relative Pfad und ein Link zum Home-Assistant-File-Editor werden im
Optionsmenue angezeigt. Aenderungen ueber die UI aktualisieren die Datei
automatisch. Nach einer Bearbeitung im File Editor kannst du die Datei ueber
**JSON-Datei bearbeiten/importieren > JSON-Datei importieren** einlesen.
Alternativ werden Aenderungen beim Neuladen der Integration oder beim Neustart
von Home Assistant uebernommen.

Die Datei liegt bewusst ausserhalb von `custom_components`, damit HACS-Updates
die Portfolio-Daten nicht loeschen.

## Erzeugte Sensoren

Bei Portfolio-Name `Crypto Portfolio` entstehen zum Beispiel:

- `sensor.crypto_portfolio_value`
- `sensor.crypto_portfolio_invested`
- `sensor.crypto_portfolio_profit`
- `sensor.crypto_portfolio_profit_percent`
- `sensor.crypto_portfolio_bitcoin_value`
- `sensor.crypto_portfolio_ethereum_value`

Der Hauptsensor `sensor.crypto_portfolio_value` enthaelt zusaetzlich das Attribut
`positions`. Darin stehen alle Coins mit Menge, aktuellem Preis, Wert, Invest,
Gewinn, Gewinn-Prozent und 24h-Aenderung.

## Dashboard-Karte

Die Integration liefert eine einfache Portfolio-Karte mit aus:

```text
/crypto_portfolio/crypto-portfolio-card.js?v=4
```

Wenn die Integration geladen ist, registriert sie diese Datei automatisch als
Frontend-Modul. Danach sollte die Karte im Karten-Picker als **Crypto Portfolio
Card** erscheinen. Falls dein Browser noch den alten Frontend-Cache nutzt:

```text
Strg + F5
```

Manuell kannst du die Resource weiterhin hinzufuegen:

1. Profil > **Erweiterter Modus** aktivieren.
2. **Einstellungen > Dashboards > Drei-Punkte-Menue > Ressourcen**.
3. Resource hinzufuegen:
   - URL: `/crypto_portfolio/crypto-portfolio-card.js?v=4`
   - Typ: `JavaScript module`

Danach eine manuelle Karte im Dashboard:

```yaml
type: custom:crypto-portfolio-card
entity: sensor.crypto_portfolio_value
title: Crypto Portfolio
sort_by: profit
show_graph: true
history_hours: 168
```

Die Karte nutzt die Home-Assistant-Historie des Portfolio-Wert-Sensors fuer den
Verlaufsgraphen. In Sections-Dashboards schlaegt sie eine volle Breite vor; bei
bereits vorhandenen Karten kannst du die Breite im Layout-Tab nachziehen.

## Lokale Checks

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest discover -s tests
python -m compileall -q custom_components tests
node --check custom_components\crypto_portfolio\frontend\crypto-portfolio-card.js
docker compose config
```
