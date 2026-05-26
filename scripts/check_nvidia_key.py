#!/usr/bin/env python3
"""Check whether a NVIDIA API key can reach hosted API Catalog endpoints."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def api_key() -> str:
    for name in ("NVIDIA_API_KEY", "NGC_API_KEY", "ALCHEMI_BMD_API_KEY"):
        value = os.getenv(name)
        if value:
            return value
    raise RuntimeError("Set NVIDIA_API_KEY or NGC_API_KEY before running this check.")


def main() -> int:
    key = api_key()
    request = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/models",
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"Hosted NVIDIA API check failed: HTTP {exc.code}", file=sys.stderr)
        return 1

    model_ids = [
        item["id"]
        for item in data.get("data", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    ]
    alchemi_like = [
        model_id
        for model_id in model_ids
        if any(term in model_id.lower() for term in ("alchemi", "bmd", "molecular"))
    ]

    print(json.dumps({
        "hosted_api_catalog_ok": True,
        "model_count": len(model_ids),
        "alchemi_like_models": alchemi_like,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
