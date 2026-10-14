from pydantic import BaseModel, Field
from typing import Optional, List
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
WORKSPACE_DIR = BASE_DIR.parent
DATA_DIR = WORKSPACE_DIR / "data"
DEMO_DATA_DIR = WORKSPACE_DIR / "demo_data"
INVOICES_DIR = DEMO_DATA_DIR / "invoices"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"

DATA_DIR.mkdir(parents=True, exist_ok=True)
DEMO_DATA_DIR.mkdir(parents=True, exist_ok=True)
INVOICES_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(WORKSPACE_DIR / ".env")
load_dotenv(BASE_DIR / ".env")

DB_PATH = (DATA_DIR / "centralign.db").resolve().as_posix()

class Settings(BaseModel):
    PROJECT_NAME: str = "CentrAlign Operator"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
    
    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "demo")  # 'demo', 'openai', 'anthropic', 'gemini'
    LLM_API_KEY: Optional[str] = os.getenv("LLM_API_KEY", None)
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
    
    # Execution & Safety Controls
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")
    MAX_TOOL_CALLS_PER_TASK: int = int(os.getenv("MAX_TOOL_CALLS_PER_TASK", "15"))
    MAX_RETRIES_PER_ACTION: int = int(os.getenv("MAX_RETRIES_PER_ACTION", "2"))
    TOOL_TIMEOUT_SECONDS: int = int(os.getenv("TOOL_TIMEOUT_SECONDS", "30"))
    
    # Policy controls
    AUTO_APPROVE_FINANCIAL_RECORDS: bool = os.getenv("AUTO_APPROVE_FINANCIAL_RECORDS", "false").lower() in ("true", "1", "yes")
    
    # Demo environment origins
    PORTAL_BASE_URL: str = os.getenv("PORTAL_BASE_URL", "http://127.0.0.1:8000/portal")
    ALLOWED_ORIGINS: List[str] = [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://localhost:5173"
    ]

settings = Settings()
