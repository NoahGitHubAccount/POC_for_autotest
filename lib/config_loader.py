from pathlib import Path
import os
import yaml

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
_EXAMPLE = _CONFIG_DIR / "config.example.yaml"


def load_config(env: str | None = None) -> dict:
    """載入設定檔。

    優先序：config.<env>.yaml → config.local.yaml（local 覆寫）
    env 來源（高到低）：參數 > TEST_ENV 環境變數 > 預設 local
    """
    if env is None:
        env = os.environ.get("TEST_ENV", "local")

    env_file = _CONFIG_DIR / f"config.{env}.yaml"
    local_file = _CONFIG_DIR / "config.local.yaml"

    if env == "local":
        # local 模式：只讀 config.local.yaml（原有行為，向下相容）
        if not local_file.exists():
            raise FileNotFoundError(
                f"找不到 {local_file}\n"
                f"請複製 {_EXAMPLE.name} 成 config.local.yaml 並填入帳密。\n"
                f"PowerShell：Copy-Item {_EXAMPLE} {local_file}"
            )
        with local_file.open(encoding="utf-8") as f:
            return yaml.safe_load(f)
    else:
        # 非 local 模式：只讀 config.<env>.yaml，不與 local.yaml 合併
        # 理由：各環境設定檔應自成體（base_url / 帳密全在 env 檔），
        #       local.yaml 僅供 local 模式個人覆寫，不應蓋掉 QA/PROD 的帳密。
        if not env_file.exists():
            raise FileNotFoundError(
                f"找不到 {env_file}\n"
                f"請複製 {_EXAMPLE.name} 成 config.{env}.yaml 並填入帳密。\n"
                f"PowerShell：Copy-Item {_EXAMPLE} {env_file}"
            )
        with env_file.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}


