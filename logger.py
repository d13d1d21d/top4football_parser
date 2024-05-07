import os.path
from datetime import datetime


def datetime_to_str(x: datetime) -> datetime: 
    return x.strftime("%Y-%m-%d %H:%M:%S")

class LogType:
    ERROR = "ERROR"
    INFO = "INFO"

class SimpleLogger:
    def __init__(self, name: str, file: str, **kwargs) -> None:
        if not os.path.exists("logs"):
            os.makedirs("logs")

        self.name = name
        self.file_name = "logs/" + file
        self.file = open("logs/" + file, **kwargs)

    def log_new_run(self) -> None:
        if os.path.isfile(self.file_name) and open(self.file_name).read(): prefix = "\n"
        else: prefix = ""
        
        self.file.write(f"{prefix}=== New run of {self.name} at {datetime_to_str(datetime.now())} ===\n")
        self.file.flush()

    def log(self, log_type: LogType, text: str, *, exc: str | None = None) -> None:
        now = datetime_to_str(datetime.now())
        self.file.write(f"[{now}] {log_type}: {text}\n")
        if log_type == LogType.ERROR and exc:
            self.file.write(f"[{now}] Python Exception: {exc}\n")

        self.file.flush()

    def close(self) -> None:
        self.file.close()