# local_scanner

local_scanner.py
로컬 전용 포트 + 베너 스케너
규칙:
 - 대상은 오직 localhost (127.0.0.1)만 허용
 - 실행 전에 명시적 동의 필요 (I CONSENT 입력)
 - rate limit 및 타임아웃 적용
 - 결과는 로그 파일 + SHA256 해시로 무결성 보존

Local dedicated port + banner scanner
 rules:
 - The target only allows localhost (127.0.0.1)
 - Explicit consent required before execution (enter I CONSENT)
 - Apply rate limits and timeouts
 - Results are integrity preserved with log file + SHA256 hash
