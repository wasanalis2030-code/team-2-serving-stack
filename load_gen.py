import argparse
import json
import time

import httpx


def run(base_url: str, duration_s: float, interval_s: float):
    end = time.time() + duration_s
    total = 0
    ok = 0

    with httpx.Client(timeout=1.0) as client:
        while time.time() < end:
            total += 1

            try:
                response = client.get(f"{base_url}/health")

                if response.status_code == 200:
                    ok += 1

            except httpx.HTTPError:
                pass

            time.sleep(interval_s)

    return ok, total


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=60.0,
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.2,
    )

    args = parser.parse_args()

    ok, total = run(
        args.base_url,
        args.duration,
        args.interval,
    )

    uptime_pct = ok / total * 100 if total else 0.0

    print(
        f"requests: {total}, "
        f"successful: {ok}, "
        f"uptime: {uptime_pct:.1f}%"
    )

    with open("uptime_report.json", "w") as file:
        json.dump(
            {
                "total": total,
                "ok": ok,
                "uptime_pct": round(uptime_pct, 1),
            },
            file,
            indent=2,
        )