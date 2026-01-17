_session_data: dict = {}
_session_file_path: str = ""


def get_session_data() -> dict:
    return _session_data


def update_session_data(data: dict):
    global _session_data
    _session_data.update(data)


def get_session_file_path() -> str:
    return _session_file_path


def set_session_file_path(path: str):
    global _session_file_path
    _session_file_path = path