import os

from core.setting_deploy import get_resource_path


class Card:
    def __init__(self, color: str, value: str, action: str = None):
        self.color = color.lower()
        self.value = value.lower()
        self.action = action if action else None
        self.image_path = get_resource_path(self.get_image_path())

    def get_image_path(self):
        base_path = "assets\cards"
        filename = f"{self.value}.svg"

        if self.value in ["draw two", "draw four", "wild", "reverse", "skip"]:
            filename = filename.replace(" ", "-")

        if self.color == "black":
            return os.path.join(base_path, "black", filename)
        return os.path.join(base_path, self.color, filename)

    def __repr__(self):
        return f"Card({self.color.capitalize()}, {self.value.capitalize()}, {self.action}, Image: {self.image_path})"

    def can_play_on(self, other_card):
        if other_card is None:
            return False
        if self.color == "black":
            return True

        if self.color == other_card.color or self.value == other_card.value:
            return True
