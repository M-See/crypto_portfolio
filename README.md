# Crypto Portfolio for Home Assistant
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

### Powered by CoinGecko API

#### Portfolio-Sensoren und Dashboard-Karte fuer deine Crypto-Investments in Home Assistant

Crypto Portfolio ist eine Home-Assistant-Custom-Integration. Sie holt aktuelle
Coin-Preise von CoinGecko, berechnet Wert, Invest, Gewinn und Gewinn in Prozent
und stellt die Daten als Sensoren sowie als eigene Lovelace-Karte bereit.

Die Konfiguration laeuft ueber die Home-Assistant-UI. Du musst keine
`configuration.yaml` mit langen REST-Sensoren oder Template-Sensoren pflegen.

## Features

- Einrichtung als Home-Assistant-Integration per UI
- Investments pro Coin mit CoinGecko-ID, Symbol, Menge und investiertem Betrag
- Options-Flow mit Menue fuer allgemeine Einstellungen, Coin hinzufuegen,
  Coin bearbeiten, Coin loeschen und erweiterten JSON-Editor
- Portfolio-Sensoren fuer Gesamtwert, Invest, Gewinn und Gewinn in Prozent
- Einzelsensoren fuer den aktuellen Wert jeder Coin-Position
- Dashboard-Karte mit Uebersicht, Farblogik fuer Gewinn/Verlust und
  Portfolio-Verlauf aus der Home-Assistant-Historie
- Lokales Testgeruest mit Docker Compose auf Port `8124`

## Installation step 1

Es gibt zwei Wege, Crypto Portfolio zu installieren:

1. HACS als Custom Repository verwenden
   - HACS oeffnen
   - Drei-Punkte-Menue > Custom repositories
   - Repository: `https://github.com/M-See/crypto_portfolio`
   - Category: `Integration`
   - Danach **Crypto Portfolio** installieren
2. Manuell installieren
   - Den Ordner `custom_components/crypto_portfolio/` nach
     `[homeassistant]/config/custom_components/crypto_portfolio/` kopieren

Starte Home Assistant nach der Installation neu.

## Installation step 2

Fuege die Integration in Home Assistant hinzu:

1. **Einstellungen > Geraete & Dienste** oeffnen
2. **Integration hinzufuegen** anklicken
3. Nach **Crypto Portfolio** suchen
4. Portfolio-Name, Waehrung, Aktualisierungsintervall und Investments eintragen

Beispiel fuer Investments:

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
`bitcoin`, `ethereum`, `cardano`, `ripple`, `solana`.

## Options

Nach der Einrichtung kannst du dein Portfolio jederzeit bearbeiten:

```text
Einstellungen > Geraete & Dienste > Crypto Portfolio > Konfigurieren
```

Das Options-Menue bietet:

- Allgemeine Einstellungen
- Coin hinzufuegen
- Coin bearbeiten
- Coin loeschen
- Erweiterter JSON-Editor

Beim Bearbeiten oder Loeschen waehlst du die einzelne Coin-Position per
Dropdown aus. Nach dem Speichern laedt Home Assistant die Integration neu.

## Properties

<pre>
- Portfolio name                         Anzeigename fuer Sensoren und Geraet
- Currency                               Zielwaehrung fuer CoinGecko, z.B. eur oder usd
- Update frequency (minutes)             Aktualisierungsintervall fuer Preisabrufe
- Cryptocurrency id                      CoinGecko-ID, z.B. bitcoin oder ethereum
- Symbol                                 Kurzes Symbol fuer die Karte, z.B. BTC
- Amount                                 Anzahl deiner Coins oder Tokens
- Invested                               Dein investierter Betrag in der gewaehlten Waehrung
</pre>

CoinGecko-Listen:

- Coin-IDs: https://api.coingecko.com/api/v3/coins/list
- Unterstuetzte Waehrungen: https://api.coingecko.com/api/v3/simple/supported_vs_currencies

## Sensors

Bei Portfolio-Name `Crypto Portfolio` entstehen zum Beispiel:

```text
sensor.crypto_portfolio_value
sensor.crypto_portfolio_invested
sensor.crypto_portfolio_profit
sensor.crypto_portfolio_profit_percent
sensor.crypto_portfolio_bitcoin_value
sensor.crypto_portfolio_ethereum_value
```

## Attributes

Der Hauptsensor `sensor.crypto_portfolio_value` enthaelt diese wichtigen
Attribute:

```text
- invested                  Gesamt investierter Betrag
- priced_invested           Investierter Betrag fuer Positionen mit aktuellem Preis
- profit                    Absoluter Gewinn oder Verlust
- profit_percent            Gewinn oder Verlust in Prozent
- missing_prices            Coin-IDs ohne aktuellen Preis
- positions_count           Anzahl der Positionen
- positions                 Liste aller Coin-Positionen
```

Jede Position in `positions` enthaelt:

```text
- coin_id                   CoinGecko-ID
- symbol                    Symbol aus deiner Konfiguration
- amount                    Anzahl Coins oder Tokens
- invested                  Investierter Betrag
- current_price             Aktueller Preis pro Coin
- value                     Aktueller Wert der Position
- profit                    Gewinn oder Verlust der Position
- profit_percent            Gewinn oder Verlust in Prozent
- change_24h_percent        24h-Aenderung laut CoinGecko
```

Die Einzelsensoren pro Coin enthalten ebenfalls `coin_id`, `symbol`, `amount`,
`invested`, `current_price`, `profit`, `profit_percent` und
`change_24h_percent`.

## Dashboard card

Die Integration liefert eine eigene Lovelace-Karte mit:

```text
/crypto_portfolio/crypto-portfolio-card.js?v=4
```

Wenn die Integration geladen ist, registriert sie diese Datei automatisch als
Frontend-Modul. Danach sollte die Karte im Karten-Picker als
**Crypto Portfolio Card** erscheinen.

Manuelle Kartenkonfiguration:

```yaml
type: custom:crypto-portfolio-card
entity: sensor.crypto_portfolio_value
title: Crypto Portfolio
sort_by: profit
show_graph: true
history_hours: 168
```

Optionen:

<pre>
- entity                                  Hauptsensor mit positions-Attribut
- title                                   Titel der Karte
- sort_by                                 Sortierung: value, profit, invested oder profit_percent
- show_graph                             Portfolio-Verlauf anzeigen
- history_hours                          Zeitraum fuer den Verlauf in Stunden
</pre>

Die Karte nutzt die Home-Assistant-Historie des Portfolio-Wert-Sensors. Direkt
nach dem Einrichten kann der Graph deshalb leer sein, bis genug Historie
aufgezeichnet wurde.

## Local testing

Du brauchst kein eigenes Dockerfile. Die `docker-compose.yml` nutzt ein
fertiges Home-Assistant-Image und bindet die Integration lokal ein.

Die Testinstanz laeuft auf Port `8124`, damit sie nicht mit einer echten
Home-Assistant-Instanz auf Port `8123` kollidiert.

```powershell
docker compose up -d
```

Home Assistant oeffnen:

```text
http://localhost:8124
```

Stoppen:

```powershell
docker compose stop
```

## Local checks

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest discover -s tests
python -m compileall -q custom_components tests
node --check custom_components\crypto_portfolio\frontend\crypto-portfolio-card.js
docker compose config
```

## API limit

CoinGecko begrenzt die Public API je nach Auslastung. Verwende deshalb ein
realistisches Update-Intervall. Der Standard ist `10` Minuten.

## Issues and new functionality

Probleme und Ideen bitte als Issue melden:

https://github.com/M-See/crypto_portfolio/issues
