import os
import sys


def get_resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def get_nicknames():
    nicknames_file = "assets/nicknames.txt"
    if os.path.exists(get_resource_path(nicknames_file)):
        with open(nicknames_file, "r", encoding="utf-8") as file:
            nicknames = [line.strip() for line in file.readlines()]
            return nicknames
    else:
        return ["Игрок1", "Игрок2", "Игрок3", "Игрок4"]
