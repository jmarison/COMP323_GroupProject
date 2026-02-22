import pygame
from main.bullet import Bullet

class Weapon:
    def __init__(self, name: str, damage: int, maxAmmo: int, clipSize: int, range: int, isProj: bool, bullet: Bullet) -> None:
        self.name = name
        self.damage = damage
        self.range = range

        self.currAmmo : int
        self.maxAmmo = maxAmmo

        self.reserveClips : int 
        self.clipSize = clipSize

        self.isProj : bool = isProj
        self.bullet: Bullet = bullet

        