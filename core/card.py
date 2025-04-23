from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from core.setting_deploy import get_resource_path


@dataclass
class Card:
    color: str
    value: str
    action: Optional[str] = None
    image_path: str = field(init=False, repr=False)

    def __post_init__(self):
        self.color = self.color.lower()
        self.value = self.value.lower()
        if self.value in ("skip", "reverse", "draw two", "draw four", "wild"):
            self.action = self.value
        else:
            self.action = None
        self.image_path = get_resource_path(self._compute_image_path())

    def _compute_image_path(self) -> str:
        base = "assets/cards"
        file_name = f"{self.value}.svg"
        if " " in file_name:
            file_name = file_name.replace(" ", "-")
        if self.color == "black":
            return os.path.join(base, "black", file_name)
        return os.path.join(base, self.color, file_name)

    @property
    def as_dict(self) -> dict:
        return {"color": self.color, "value": self.value, "action": self.action}

    def can_play_on(self, other: "Card | None") -> bool:  # пригодится позже
        if other is None:
            return False
        if other.action in ["draw four", "wild"]:
            return True
        return (
                self.color == "black"
                or self.color == other.color
                or self.value == other.value
        )

    def __hash__(self) -> int:
        return hash((self.color, self.value, self.action))

    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        return cls(
            color=data.get("color"),
            value=data.get("value"),
            action=data.get("action"),
        )
