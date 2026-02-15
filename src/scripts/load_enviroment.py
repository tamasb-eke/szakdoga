from dotenv import load_dotenv
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / "config" / ".env")
APP_ENV = os.getenv("APP_ENV", "dev")
AUTHOR = os.getenv("AUTHOR")

env_file = ROOT / "config" / f"{APP_ENV}.env"
if env_file.exists():
    load_dotenv(env_file, override=True)


print(f"-------------------------------")
print(f"------------- {APP_ENV.upper()} -------------")
print(f"-------------------------------")
