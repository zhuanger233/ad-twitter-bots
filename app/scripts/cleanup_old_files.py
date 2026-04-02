from app.core.config import get_settings


if __name__ == "__main__":
    settings = get_settings()
    root = settings.workdir / settings.temp_dir_name
    root.mkdir(parents=True, exist_ok=True)
    for child in root.iterdir():
        if child.is_dir() and not any(child.iterdir()):
            child.rmdir()
