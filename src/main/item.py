import pygame

class Item:
    def __init__(self, name: str, tier: int) -> None:
        self.name = name
        self.tier: int = tier
