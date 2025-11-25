#!/usr/bin/env python3

import asyncio
import socket
import hashlib
import time
import json
from datetime import datetime

# 설정
TARGET = "127.0.0.1"
PORTS = [21, 22, 23, 25, 53, 80, 110, 143, 443, 3306, 6379, 8000, 8080]  # 필요시 수정
CONCURRENCY = 200
CONNECT_TIMEOUT = 1.0     # seconds
READ_TIMEOUT = 1.0        # seconds
RATE_DELAY = 0.005        # 각 연결 사이 지연 (서비스 방해 최소화)

LOGFILE = f"scan_result_{int(time.time())}.json"

# 동의 확인 (강제)
def require_consent():
    print("주의: 이 도구는 **당신의 로컬 머신(127.0.0.1)** 스케닝 전용 도구입니다.")
    print("외부 시스템/타인 시스템을 스캔하면 불법일 수 있습니다.")
    consent = input('계속하려면 정확히 "I CONSENT" 를 입력하세요: ').strip()
    if consent != "I CONSENT":
        print("동의가 필요합니다. 종료합니다.")
        raise SystemExit(1)

# 로컬 대상 확인 (강제)
def ensure_local_target(target):
    if target not in ("127.0.0.1", "localhost", "::1"):
        print("ERROR: 대상은 오직 로컬호스트만 허용됩니다.")
        raise SystemExit(1)

async def probe_port(semaphore, port, results):
    async with semaphore:
        await asyncio.sleep(RATE_DELAY)  # polite delay
        loop = asyncio.get_event_loop()
        try:
            fut = loop.run_in_executor(None, lambda: socket.create_connection((TARGET, port), CONNECT_TIMEOUT))
            sock = await asyncio.wait_for(fut, timeout=CONNECT_TIMEOUT + 0.1)
            # 연결 성공
            sock.settimeout(READ_TIMEOUT)
            banner = b""
            try:
                # 간단한 배너 수집: recv(1024)
                banner = sock.recv(1024)
            except Exception:
                banner = b""
            try:
                sock.close()
            except Exception:
                pass
            results.append({
                "port": port,
                "status": "open",
                "banner": banner.decode("utf-8", errors="replace"),
            })
        except (asyncio.TimeoutError, socket.timeout):
            results.append({"port": port, "status": "filtered/timeout", "banner": ""})
        except ConnectionRefusedError:
            results.append({"port": port, "status": "closed", "banner": ""})
        except Exception as e:
            results.append({"port": port, "status": f"error: {e}", "banner": ""})

def save_log(data):
    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "target": TARGET,
        "results": data
    }
    txt = json.dumps(payload, ensure_ascii=False, indent=2)
    with open(LOGFILE, "w", encoding="utf-8") as f:
        f.write(txt)
    # 무결성 해시
    h = hashlib.sha256(txt.encode('utf-8')).hexdigest()
    with open(LOGFILE + ".sha256", "w", encoding="utf-8") as f:
        f.write(h)
    return LOGFILE, LOGFILE + ".sha256", h

async def main():
    require_consent()
    ensure_local_target(TARGET)
    print(f"스캔 시작: {TARGET} 포트 {len(PORTS)}개 — 안전 모드(로컬 전용).")
    semaphore = asyncio.Semaphore(CONCURRENCY)
    results = []
    tasks = [probe_port(semaphore, p, results) for p in PORTS]
    await asyncio.gather(*tasks)
    # 정렬
    results_sorted = sorted(results, key=lambda x: x["port"])
    logfile, shafile, h = save_log(results_sorted)
    # 간단 리포트 출력
    print("\n스캔 결과 요약:")
    for r in results_sorted:
        line = f"포트 {r['port']}: {r['status']}"
        if r["banner"]:
            line += f" | 배너: {r['banner'][:120]!s}"
        print(line)
    print(f"\n로그 저장: {logfile} (무결성: {shafile} -> {h})")
    print("권장: 열린 포트에 대해 어떤 서비스가 실행중인지 로컬에서 확인하고 필요시 중지/차단하세요.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
