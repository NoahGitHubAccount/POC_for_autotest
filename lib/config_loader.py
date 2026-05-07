from pathlib import Path
import yaml

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
_LOCAL = _CONFIG_DIR / "config.local.yaml"
_EXAMPLE = _CONFIG_DIR / "config.example.yaml"


def load_config() -> dict:
    """載入設定檔，優先讀 config.local.yaml；找不到時提示如何建立。"""
    if not _LOCAL.exists():
        raise FileNotFoundError(
            f"找不到 {_LOCAL}\n"
            f"請複製 {_EXAMPLE.name} 成 config.local.yaml 並填入帳密。\n"
            f"PowerShell：copy {_EXAMPLE} {_LOCAL}"
        )
    with _LOCAL.open(encoding="utf-8") as f:
        return yaml.safe_load(f)
