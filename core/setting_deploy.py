import os
import sys


def get_resource_path(relative_path: str) -> str:
    """
    Возвращает корректный абсолютный путь к ресурсу как при
    запуске из-под PyInstaller, так и из-под исходников.
    """
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        # __file__ указывает на тот модуль, в котором живёт этот код
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)
