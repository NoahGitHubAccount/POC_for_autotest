"""互動式登入並儲存 session 至 .auth/<role>.json。

用法：
    python tools/warm_login.py
    python tools/warm_login.py --role admin
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright

from lib.auth import (
    perform_interactive_login,
    save_session_storage,
    save_storage_state,
)
from lib.config_loader import load_config


def main() -> int:
    parser = argparse.ArgumentParser(description="互動式登入並儲存 session")
    parser.add_argument("--role", default="admin", help="config.accounts 的 key")
    args = parser.parse_args()

    cfg = load_config()
    if cfg["captcha"]["mode"] == "reuse":
        print("config 設定 captcha.mode=reuse，warm-login 不適用此模式。", file=sys.stderr)
        return 2

    if cfg["accounts"][args.role]["username"] == "REPLACE_ME":
        print(
            f"config.local.yaml 的 accounts.{args.role} 仍為預設值，請填入真實帳密。",
            file=sys.stderr,
        )
        return 2

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=cfg.get("browser", {}).get("slow_mo_ms", 0),
        )
        ctx = browser.new_context(
            viewport=cfg.get("browser", {}).get("viewport", {"width": 1440, "height": 900}),
        )
        page = ctx.new_page()
        try:
            perform_interactive_login(page, cfg, role=args.role)
            # 等 SPA 完成所有 post-login 寫入（token、UserProfile…）
            page.wait_for_timeout(2500)
            sp = save_storage_state(ctx, role=args.role)
            ssp = save_session_storage(page, role=args.role)
            print(f"\n登入成功")
            print(f"  storage_state（cookies + localStorage）：{sp}")
            print(f"  sessionStorage 補全：{ssp}")
            print(f"視為新鮮的有效期：{cfg['captcha']['session_max_age_min']} 分鐘")
            return 0
        finally:
            ctx.close()
            browser.close()


if __name__ == "__main__":
    raise SystemExit(main())
