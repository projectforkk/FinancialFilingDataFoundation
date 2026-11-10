from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    script_dir = str(Path(__file__).resolve().parent)
    sys.path[:] = [entry for entry in sys.path if entry != script_dir]
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from financial_filing_data_foundation.us_sec.http import _network_transport, validate_sec_url


def main(argv: list[str] | None = None) -> int:
    operation = (argv or sys.argv[1:])[:1]
    payload = json.loads(sys.stdin.read() or "{}")
    if operation == ["doctor"]:
        print(json.dumps({"status": "OK", "runtime": "p11-sec-stdlib-runtime-v1"}))
        return 0
    if operation != ["fetch"] or not isinstance(payload, dict):
        print(json.dumps({"status": "ERROR", "reason_code": "P11_SEC_DISCOVERY_FAILED", "message": "unsupported SEC runner request"}))
        return 2
    url = str(payload.get("url", ""))
    try:
        validate_sec_url(url)
        response = _network_transport(
            url,
            {str(key): str(value) for key, value in dict(payload.get("headers") or {}).items()},
            float(payload.get("timeout", 30.0)),
            max_bytes=int(payload.get("max_bytes", 512 * 1024 * 1024)),
            max_redirects=int(payload.get("max_redirects", 3)),
            read_timeout=float(payload.get("read_timeout", payload.get("timeout", 30.0))),
            total_timeout=float(payload.get("total_timeout", payload.get("timeout", 30.0))),
        )
        print(
            json.dumps(
                {
                    "status": response.status,
                    "headers": dict(response.headers),
                    "body_b64": base64.b64encode(response.body).decode("ascii"),
                    "final_url": response.final_url,
                },
                ensure_ascii=False,
            )
        )
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "ERROR",
                    "reason_code": getattr(exc, "reason_code", "P11_SEC_DISCOVERY_FAILED"),
                    "message": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
