import csv
import pathlib
import logging
from datetime import datetime as dt


COLORS = {
    "white": "белый",
    "rouge foncé": "бордовый",
    "blue": "голубой",
    "orange": "оранжевый",
    "red": "красный",
    "silver": "серебряный",
    "black": "чёрный",
    "yellow": "жёлтый",
    "green": "зелёный",
    "saddlebrown": "коричневый",
    "nan": "разноцветный",
    "pink": "розовый",
    "purple": "фиолетовый"
}


def date_str(date: dt) -> str:
	return date.strftime("%Y-%m-%d")

def dom_color_name(r: int, g: int, b: int) -> str:
    csv_reader = csv.reader(
        open("colors.csv", newline="", encoding="utf-8"),
        delimiter=","
    )
    next(csv_reader)
    color_match = { }

    for row in csv_reader:
        name, rd, gd, bd = row
        color_match[name] = (int(rd) - int(r)) ** 2 + (int(gd) - int(g)) ** 2 + (int(bd) - int(b)) ** 2

    return min(color_match, key=color_match.get)

def init_logger(path: str, format: str, level: int | str) -> logging.Logger:
    pathlib.Path("logs/").mkdir(exist_ok=True) 

    logger = logging.Logger("parser_errors")
    logger.setLevel(level)

    ch_file = logging.FileHandler(path, delay=True, encoding="utf-8")
    ch_file.setLevel(level)
    logger.addHandler(ch_file)

    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(logging.Formatter(format))
    logger.addHandler(ch)

    return logger

def unicode_to_float(s: str) -> str:
    unicode_fraction = {
        "½": ".5", "⅓": ".3", "⅔": ".7", "¼": ".25", "¾": ".75", "⅕": ".2",
        "⅖": ".4", "⅗": ".6", "⅘": ".8", "⅙": ".167", "⅚": ".833", "⅐": ".143",
        "⅛": ".125", "⅜": ".375", "⅝": ".625", "⅞": ".875"
    }
    for k, v in unicode_fraction.items():
        s = s.replace(k, v)

    return s.replace(".0", "")
