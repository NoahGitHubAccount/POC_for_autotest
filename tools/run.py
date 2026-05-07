"""統一 CLI 入口。

P1 階段提供：
    python tools/run.py --warm-login    # 互動式登入並儲存 session
    python tools/run.py --smoke         # 跑冒煙測試（驗證 session 可用）

後續階段（P2/P5）會擴充：
    python tools/run.py --wbs 2-2-2-B
    python tools/run.py --since-run <id> --failed-only
"""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser()
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--warm-login", action="store_true", help="互動式登入並儲存 session")
    g.add_argument("--smoke", action="store_true", help="跑冒煙測試")

    parser.add_argument("--role", default="admin")

    args = parser.parse_args()

    if args.warm_login:
        return subprocess.call(
            [sys.executable, str(PROJECT_ROOT / "tools" / "warm_login.py"), "--role", args.role],
            cwd=PROJECT_ROOT,
        )

    if args.smoke:
        return subprocess.call(
            [sys.executable, "-m", "pytest", "-m", "smoke", "-s", "-v"],
            cwd=PROJECT_ROOT,
        )

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
