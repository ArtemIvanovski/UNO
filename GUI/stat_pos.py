import os

from core.setting_deploy import get_resource_path


def get_name_positions():
    return [
        (750, 570, 0),
        (750, 180, 180),
        (1310, 375, 270),
        (180, 375, 90)
    ]


def get_arc_config():
    return {
        0: {"cx": 750, "cy": 2100, "r": 1500, "start_angle": 260, "end_angle": 280},
        1: {"cx": 750, "cy": -1350, "r": 1500, "start_angle": 75, "end_angle": 95},
        2: {"cx": 2850, "cy": 400, "r": 1500, "start_angle": -5, "end_angle": 5},
        3: {"cx": -1350, "cy": 400, "r": 1500, "start_angle": -180, "end_angle": -190},
    }


def get_color_map():
    return {
        "red": "#ff5555",
        "blue": "#5555ff",
        "yellow": "#ffaa00",
        "green": "#55aa55",
    }


def get_nicknames():
    nicknames_file = "assets/nicknames.txt"
    if os.path.exists(get_resource_path(nicknames_file)):
        with open(nicknames_file, "r", encoding="utf-8") as file:
            nicknames = [line.strip() for line in file.readlines()]
            return nicknames
    else:
        return ["Игрок1", "Игрок2", "Игрок3", "Игрок4"]
