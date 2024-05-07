import json

class Settings:
    def __init__(self) -> None:
        self.__raw = json.loads(open("settings/settings.json").read())

    @property
    def threads(self) -> int:
        return int(self.__raw.get("threads"))
    
    @property
    def csv_sep(self) -> str:
        return self.__raw.get("csv_sep")
    
settings = Settings()