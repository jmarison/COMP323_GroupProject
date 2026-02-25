
import pygame

class Bullet:
    def __init__(self, name: str, bulletSpeed: int, bulletScale: int, pierceCount: int) -> None:
        self.name = name
        self.bulletSpeed: int = bulletSpeed
        self.bulletScale: int = bulletScale
        self.pierceCount: int = pierceCount