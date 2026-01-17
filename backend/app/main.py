import logging
import os
import json
from pathlib import Path
import sys
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.api.v1.router import api_router
from app.storage.cognitive_map_store import CognitiveMapStore
from core.logging_config import setup_logging
from app.dependencies.cognitive_map_dependencies import (
    set_cognitive_map_store,
    get_cognitive_map_store,
)
from app.dependencies.session_data_dependencies import (
    set_session_file_path,
    update_session_data,
)

setup_logging()
logger = logging.getLogger("app")


def load_session_data(session_path: str) -> dict:
    try:
        with open(session_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Session file not found at {session_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {session_path}: {e}")
        return {}


def save_session_data(session_path: str, data: dict) -> bool:
    try:
        with open(session_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving session data to {session_path}: {e}")
        return False


def get_default_projects_dir() -> Path:
    if sys.platform == "win32":
        base_dir = Path(os.environ.get("USERPROFILE", ""))
        projects_dir = base_dir / "Documents" / "CognitiveMaps"
    else:
        base_dir = Path.home()
        xdg_data_home = os.environ.get("XDG_DATA_HOME")
        if xdg_data_home:
            projects_dir = Path(xdg_data_home) / "CognitiveMaps"
        else:
            projects_dir = base_dir / ".local" / "share" / "CognitiveMaps"

    try:
        projects_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Projects directory: {projects_dir}")
    except Exception as e:
        logger.error(f"Failed to create projects directory {projects_dir}: {e}")
        projects_dir = Path.cwd() / "projects"
        projects_dir.mkdir(parents=True, exist_ok=True)
        logger.warning(f"Using fallback projects directory: {projects_dir}")

    return projects_dir


def get_default_project_path() -> Path:
    projects_dir = get_default_projects_dir()
    default_file = projects_dir / "default_map.json"
    return default_file


@asynccontextmanager
async def lifespan(app: FastAPI):
    session_file_path = os.getenv("SESSION_FILE_PATH")
    logger.info(f"Using config filepath: {session_file_path}")

    if not session_file_path:
        logger.info("Warning: SESSION_FILE_PATH not set, using default")
        session_file_path = "session.json"
    session_data = load_session_data(session_file_path)

    last_opened = session_data.get("lastOpened")

    if last_opened:
        project_path = Path(last_opened)
        logger.info(f"Last opened file: {project_path}")
        if not project_path.exists():
            logger.warning(f"Last opened file not found: {project_path}")
            project_path = get_default_project_path()
            logger.info(f"Using default project path: {project_path}")
    else:
        project_path = get_default_project_path()
        logger.info(f"No last opened file, using default: {project_path}")

    try:
        cognitive_map_store = CognitiveMapStore(path=project_path, history_limit=20)
        logger.info(f"CognitiveMapStore initialized with path: {project_path}")
    except Exception as e:
        logger.error(f"Failed to initialize CognitiveMapStore: {e}")
        raise

    await cognitive_map_store.load()
    set_cognitive_map_store(cognitive_map_store)
    set_session_file_path(session_file_path)
    update_session_data(session_data)

    yield

    print("Shutting down gracefully...")

    cognitive_map_store = get_cognitive_map_store()

    try:
        await cognitive_map_store.save_to_file()
        logger.info("Cognitive map store saved successfully")
    except Exception as e:
        logger.error(f"Failed to save cognitive map store: {e}")

    if session_file_path:
        current_opened_file = cognitive_map_store.path.resolve()
        save_session_data(
            session_file_path,
            {
                "settings": session_data.get("settings", {}),
                "lastOpened": str(current_opened_file),
            },
        )
        print(f"Session data saved to: {session_file_path}")

    print("Shutdown complete")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

count = 0


@app.get("/")
@app.head("/")
def health_check():
    return {"status": "ok"}


@app.get("/api/count")
def read_count():
    global count
    count += 1
    return {"count": count}


app.include_router(
    api_router,
    prefix="/api/v1",
)

if __name__ == "__main__":
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8001"))
    uvicorn.run(app, host=host, port=port)
