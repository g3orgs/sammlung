---
name: spritmonitor
description: Use when reading Spritmonitor vehicles, tanks, fuelings, or creating/updating/deleting fuel and cost entries through the Spritmonitor API.
---

# Spritmonitor

Use this skill when the user asks to inspect or update Spritmonitor data, especially vehicle lists, tanks, fuelings, costs, odometer entries, or API/token setup.

## Safety

- Treat Spritmonitor credentials and bearer tokens as secrets. Do not repeat tokens in chat or logs.
- Store local API config in `.openclaw/secrets/spritmonitor.env` with mode `600`.
- Never store the user's Spritmonitor password. If a password or token was pasted into a group chat, warn the user to rotate it.
- Do not invent fuel quantity, price, odometer, or station data. If Spritmonitor requires a missing field, ask for it or create only the exact entry the user requested and report any API-side limitations.
- API writes are real changes. After creating or updating an entry, read back the latest fuelings and report the resulting entry id and key fields.

## Local Config

Expected env file:

```sh
SPRITMONITOR_APP_TOKEN=...
SPRITMONITOR_BEARER_TOKEN=...
```

The current workspace location is `.openclaw/secrets/spritmonitor.env`. Source it before API calls:

```sh
set -a
. /home/claw/.openclaw/workspace/.openclaw/secrets/spritmonitor.env
set +a
```

Required headers:

- `Application-ID: $SPRITMONITOR_APP_TOKEN`
- `Authorization: Bearer $SPRITMONITOR_BEARER_TOKEN`
- `User-Agent: OpenClaw Spritmonitor`

## Token Setup

If the personal bearer token is missing, tell the user:

1. Open `https://www.spritmonitor.de/` and log in.
2. Open `https://www.spritmonitor.de/en/my_account/change_password.html`.
3. In the API/token area, choose `create new token`.
4. Copy only the bearer token into `SPRITMONITOR_BEARER_TOKEN=` in `.openclaw/secrets/spritmonitor.env`.

Cloudflare may block non-browser access to this page, so a human may need to generate the bearer token interactively.

## API Basics

Base URL: `https://api.spritmonitor.de/v1`

Read vehicles:

```sh
curl -s 'https://api.spritmonitor.de/v1/vehicles.json' \
  -H "Application-ID: $SPRITMONITOR_APP_TOKEN" \
  -H "Authorization: Bearer $SPRITMONITOR_BEARER_TOKEN" \
  -H 'User-Agent: OpenClaw Spritmonitor'
```

Read tanks for a vehicle:

```sh
curl -s "https://api.spritmonitor.de/v1/vehicle/$VEHICLE_ID/tanks.json" ...
```

Read recent fuelings:

```sh
curl -s "https://api.spritmonitor.de/v1/vehicle/$VEHICLE_ID/tank/$TANK_ID/fuelings.json?limit=5" ...
```

Diesel was observed as `fuelsortid=1`; liter is `quantityunitid=1`; EUR is `currencyid=0`. Confirm from the account if uncertain:

- `/fuelsorts.json`
- `/quantityunits.json`
- `/currencies.json`
- `/costtypes.json`

## Creating Or Updating Fuelings

Spritmonitor uses GET endpoints for writes.

Create:

`/vehicle/{vehicleId}/tank/{tankId}/fueling.json`

Update:

`/vehicle/{vehicleId}/tank/{tankId}/fueling/{fuelingId}.json`

Common query fields:

- `date`: `DD.MM.YYYY`
- `type`: `full`, `notfull`, `first`, or `invalid`
- `odometer`: current odometer
- `trip`: distance since previous fueling, usually current odometer minus last fueling odometer
- `quantity`: fuel amount
- `quantityunitid`: `1` for liter
- `fuelsortid`: account-specific fuel sort id; Diesel observed as `1`
- `price`: total price when `pricetype=0`
- `currencyid`: `0` for EUR
- `pricetype`: `0` total price, `1` unit/liter price
- `note`, `stationname`, `location`, `country` optional

When the user provides only an odometer reading, the API may create an `invalid` entry and omit cost/quantity. Report that clearly and update the same entry if the user later supplies liters.

## Verification Pattern

After a write:

1. Read `/vehicle/{vehicleId}/tank/{tankId}/fuelings.json?limit=3`.
2. Locate the returned id or newest entry.
3. Check `date`, `odometer`, `trip`, `quantity`, `cost`, `currencyid`, `type`, `fuelsortid`, and `note`.
4. Report concise results to the user.

## Current Known Account Context

Do not treat these as universal constants, but they were observed in this workspace on 2026-07-05:

- Ford Ranger: vehicle id `1205519`, main tank `1`, diesel tank type.
- Volkswagen Tiguan: vehicle id `815108`, main tank `1`.
- Mini Cooper S: vehicle id `518628`, main tank `1`.
- Example updated Ford Ranger fueling: id `63828418`, date `05.07.2026`, odometer `79508`, quantity `60`, cost `114`, EUR.

## Useful Helper

Use `scripts/spritmonitor_api.py` when available. It loads the local env file, keeps secrets out of output, and supports listing vehicles/fuelings plus creating/updating fuelings.
