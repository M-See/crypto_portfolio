# Crypto Portfolio for Home Assistant
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

### Powered by CoinGecko API

#### Portfolio sensors and a Lovelace dashboard card for crypto investments

Crypto Portfolio is a Home Assistant custom integration. It fetches current
coin prices from CoinGecko, calculates portfolio value, invested amount, profit
and profit percentage, and exposes the result as Home Assistant sensors.

The integration is configured through the Home Assistant UI. You do not need to
maintain long REST sensors or template sensors in `configuration.yaml`.

## Features

- UI-based setup through **Settings > Devices & services**
- Portfolio holdings with CoinGecko ID or known ticker symbol, amount and
  invested amount
- Options flow for general settings, adding a coin, editing one coin, removing
  one coin and advanced JSON editing
- Summary sensors for total value, invested amount, profit and profit percent
- Per-coin value sensors
- Lovelace card with portfolio overview, profit/loss coloring and a value
  history chart
- Local development setup with Docker Compose on port `8124`

## Installation step 1

There are two ways to install Crypto Portfolio.

### HACS custom repository

1. Open HACS.
2. Open the three-dot menu and choose **Custom repositories**.
3. Add this repository:

   ```text
   https://github.com/M-See/crypto_portfolio
   ```

4. Select category **Integration**.
5. Install **Crypto Portfolio**.
6. Restart Home Assistant.

### Manual installation

Copy this folder:

```text
custom_components/crypto_portfolio/
```

to:

```text
[homeassistant]/config/custom_components/crypto_portfolio/
```

Then restart Home Assistant.

## Installation step 2

Add the integration in Home Assistant:

1. Open **Settings > Devices & services**.
2. Click **Add integration**.
3. Search for **Crypto Portfolio**.
4. Enter portfolio name, currency, update interval and holdings.

Example holdings:

```json
[
  {
    "coin_id": "bitcoin",
    "symbol": "BTC",
    "amount": 0.05,
    "invested": 1200
  },
  {
    "coin_id": "ETH",
    "symbol": "ETH",
    "amount": 1.2,
    "invested": 2500
  }
]
```

`coin_id` should normally be the CoinGecko coin ID, for example `bitcoin`,
`ethereum`, `cardano`, `ripple` or `solana`. Common ticker symbols such as
`BTC`, `ETH`, `ADA`, `XRP`, `SOL`, `BNB`, `DOGE`, `DOT`, `LINK`, `USDT` and
`USDC` are also accepted and will be normalized internally.

CoinGecko IDs are still the safest option because ticker symbols can be
ambiguous. If a coin does not show a price, use the exact CoinGecko ID.

## Options

After setup, open:

```text
Settings > Devices & services > Crypto Portfolio > Configure
```

The options menu contains:

- General settings
- Add coin
- Edit coin
- Remove coin
- Advanced JSON editor

When editing or removing a holding, you can select the coin from a dropdown.
Home Assistant reloads the integration after saving the options.

The integration also keeps a JSON file for each portfolio:

```text
/config/crypto_portfolio/holdings.json
```

The Home Assistant File editor displays the same path as
`/homeassistant/crypto_portfolio/holdings.json`.

The exact relative path is shown in the options menu and advanced JSON editor.
UI changes update this file automatically. After editing the file externally,
reopen the advanced JSON editor and save it to apply the changes. Reloading the
integration or restarting Home Assistant also imports valid file changes.

Additional portfolios use simple numbered filenames such as `holdings-2.json`.
The directory is outside `custom_components`, so HACS updates and integration
reinstalls do not overwrite the portfolio files. Removing and recreating a
config entry also reuses the first existing file that is not assigned to
another active portfolio.

There is no universal direct link to the Home Assistant File editor. It is a
Supervisor add-on and is not available on every installation type. When it is
installed, open the displayed relative path manually.

## Properties

<pre>
- Portfolio name                         Display name for the device and sensors
- Currency                               Target currency for CoinGecko, for example eur or usd
- Update frequency (minutes)             How often prices should be refreshed
- CoinGecko coin ID or symbol            CoinGecko ID, for example bitcoin, or a known ticker such as BTC
- Symbol                                 Short display symbol for the dashboard card
- Amount                                 Number of coins or tokens held
- Invested                               Invested amount in the selected currency
</pre>

Useful CoinGecko lists:

- Coin IDs: https://api.coingecko.com/api/v3/coins/list
- Supported currencies: https://api.coingecko.com/api/v3/simple/supported_vs_currencies

## Sensors

For a portfolio named `Crypto Portfolio`, Home Assistant creates sensors such
as:

```text
sensor.crypto_portfolio_value
sensor.crypto_portfolio_invested
sensor.crypto_portfolio_profit
sensor.crypto_portfolio_profit_percent
sensor.crypto_portfolio_bitcoin_value
sensor.crypto_portfolio_ethereum_value
```

Entity IDs may differ if Home Assistant already has entities with the same
names.

## Attributes

The main value sensor, usually `sensor.crypto_portfolio_value`, contains these
attributes:

```text
- invested                  Total invested amount
- priced_invested           Invested amount for positions with a current price
- profit                    Absolute profit or loss
- profit_percent            Profit or loss in percent
- missing_prices            Coin IDs without a current price
- positions_count           Number of positions
- positions                 List of all coin positions
```

Each item in `positions` contains:

```text
- coin_id                   CoinGecko ID
- symbol                    Display symbol from your configuration
- amount                    Number of coins or tokens
- invested                  Invested amount
- current_price             Current price per coin
- value                     Current value of the position
- profit                    Profit or loss of the position
- profit_percent            Profit or loss in percent
- change_24h_percent        24h change reported by CoinGecko
```

The per-coin sensors also expose `coin_id`, `symbol`, `amount`, `invested`,
`current_price`, `profit`, `profit_percent` and `change_24h_percent`.

## Dashboard card

The integration bundles a Lovelace card:

```text
/crypto_portfolio/crypto-portfolio-card.js?v=8
```

The integration tries to load the card automatically after it is set up. If the
card does not appear in the card picker, add the dashboard resource manually.

### Manual resource setup

1. Open your Home Assistant user profile and enable **Advanced mode**.
2. Open **Settings > Dashboards**.
3. Open the three-dot menu and choose **Resources**.
4. Add a resource:

   ```text
   URL:  /crypto_portfolio/crypto-portfolio-card.js?v=8
   Type: JavaScript module
   ```

5. Refresh the browser tab with a hard reload.
6. Reopen the card picker.

You can also test the file directly in your browser:

```text
https://your-home-assistant-url/crypto_portfolio/crypto-portfolio-card.js?v=8
```

If this URL returns `404`, the integration is not loaded yet. Restart Home
Assistant and make sure the Crypto Portfolio integration exists under
**Settings > Devices & services**.

### Manual card configuration

If the card picker still does not list the card, add a manual card:

```yaml
type: custom:crypto-portfolio-card
entity: sensor.crypto_portfolio_value
title: Crypto Portfolio
sort_by: profit
show_graph: true
history_hours: 168
```

Card options:

<pre>
- entity                                  Main portfolio sensor with the positions attribute
- title                                   Card title
- sort_by                                 Sort by value, profit, invested or profit_percent
- show_graph                             Show the portfolio history chart
- history_hours                          Time range for the chart in hours
</pre>

The chart uses the Home Assistant history of the portfolio value sensor. Right
after setup, the chart can be empty until Home Assistant has recorded enough
states.

## Local testing

No custom Dockerfile is required. The included `docker-compose.yml` starts a
stock Home Assistant container and mounts this integration into the test
instance.

The local test instance uses port `8124` so it does not conflict with a real
Home Assistant instance running on port `8123`.

```powershell
docker compose up -d
```

Open Home Assistant:

```text
http://localhost:8124
```

Stop the test instance:

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

CoinGecko rate limits the public API depending on current usage conditions.
Use a realistic update interval. The default is `10` minutes.

## Issues and feature requests

Please use GitHub issues:

https://github.com/M-See/crypto_portfolio/issues
