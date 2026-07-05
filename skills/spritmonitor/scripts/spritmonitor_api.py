#!/usr/bin/env python3
"""Small Spritmonitor API helper for OpenClaw/Codex skills."""

from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = "https://api.spritmonitor.de/v1"
DEFAULT_ENV = Path("/home/claw/.openclaw/workspace/.openclaw/secrets/spritmonitor.env")


def load_env(path: Path = DEFAULT_ENV) -> None:
    if not path.exists():
        raise SystemExit(f"Missing env file: {path}")
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def request(path: str, params: dict[str, str] | None = None):
    app = os.environ.get("SPRITMONITOR_APP_TOKEN")
    bearer = os.environ.get("SPRITMONITOR_BEARER_TOKEN")
    if not app or not bearer:
        raise SystemExit("Missing SPRITMONITOR_APP_TOKEN or SPRITMONITOR_BEARER_TOKEN")
    url = BASE_URL + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={
            "Application-ID": app,
            "Authorization": "Bearer " + bearer,
            "User-Agent": "OpenClaw Spritmonitor",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        text = response.read().decode("utf-8", "replace")
        if not text:
            return None
        return json.loads(text)


def print_json(value) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("vehicles")

    fuelings = sub.add_parser("fuelings")
    fuelings.add_argument("vehicle_id")
    fuelings.add_argument("tank_id")
    fuelings.add_argument("--limit", default="5")

    create = sub.add_parser("create-fueling")
    update = sub.add_parser("update-fueling")
    for p in (create, update):
        p.add_argument("vehicle_id")
        p.add_argument("tank_id")
        p.add_argument("--date", required=True)
        p.add_argument("--type", default="full")
        p.add_argument("--odometer", required=True)
        p.add_argument("--trip", required=True)
        p.add_argument("--quantity")
        p.add_argument("--quantityunitid", default="1")
        p.add_argument("--fuelsortid", required=True)
        p.add_argument("--price")
        p.add_argument("--currencyid", default="0")
        p.add_argument("--pricetype", default="0")
        p.add_argument("--note")
    update.add_argument("fueling_id")

    args = parser.parse_args()
    load_env()

    if args.cmd == "vehicles":
        print_json(request("/vehicles.json"))
    elif args.cmd == "fuelings":
        print_json(request(f"/vehicle/{args.vehicle_id}/tank/{args.tank_id}/fuelings.json", {"limit": args.limit}))
    elif args.cmd in {"create-fueling", "update-fueling"}:
        params = {
            "date": args.date,
            "type": args.type,
            "odometer": args.odometer,
            "trip": args.trip,
            "quantityunitid": args.quantityunitid,
            "fuelsortid": args.fuelsortid,
            "currencyid": args.currencyid,
            "pricetype": args.pricetype,
        }
        for key in ("quantity", "price", "note"):
            value = getattr(args, key)
            if value is not None:
                params[key] = value
        if args.cmd == "create-fueling":
            path = f"/vehicle/{args.vehicle_id}/tank/{args.tank_id}/fueling.json"
        else:
            path = f"/vehicle/{args.vehicle_id}/tank/{args.tank_id}/fueling/{args.fueling_id}.json"
        print_json(request(path, params))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
