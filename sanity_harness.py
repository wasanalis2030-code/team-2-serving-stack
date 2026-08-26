import os
import sys

import httpx


BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")


def fail(message):
    print(f"[FAIL] {message}")
    print("\nGREEN CHECK: FAIL")
    sys.exit(1)


health = httpx.get(f"{BASE_URL}/health", timeout=10)

if health.status_code != 200:
    fail(f"/health returned {health.status_code}")

device = health.json().get("device")

if device not in ("cpu", "cuda"):
    fail(f"invalid device: {device}")

print(f"[PASS] /health reports device: {device}")


normal = httpx.post(
    f"{BASE_URL}/v1/chat/completions",
    json={"prompt": "hello"},
    timeout=30,
)

if normal.status_code != 200:
    fail(f"normal request returned {normal.status_code}")

print("[PASS] normal request succeeds")


gpu_only = httpx.post(
    f"{BASE_URL}/v1/chat/completions",
    json={
        "prompt": "hello",
        "require_gpu": True,
    },
    timeout=30,
)

if device == "cpu":
    if gpu_only.status_code != 400:
        fail(
            "GPU-only request should return 400 on CPU, "
            f"but returned {gpu_only.status_code}"
        )

    detail = gpu_only.json().get("detail", "")

    if "GPU" not in detail:
        fail("the 400 response does not contain a clear GPU message")

    print("[PASS] GPU-only request fails cleanly on CPU")

else:
    if gpu_only.status_code != 200:
        fail(
            "GPU-only request should succeed on CUDA, "
            f"but returned {gpu_only.status_code}"
        )

    print("[PASS] GPU-only request succeeds on CUDA")


print("\nGREEN CHECK: PASS")