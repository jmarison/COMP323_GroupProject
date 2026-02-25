import pygame
from main.bullet import Bullet

class Weapon:
    def __init__(self, name: str, damage: int, maxAmmo: int, clipSize: int, range: int, isProj: bool, bullet: Bullet, fireRate: int) -> None:
        self.name = name
        self.damage = damage
        self.range = range
        self.fireRate = fireRate
        self.sprite = pygame.rect((16, 16)) # TODO : replace with actual sprite

        #A max ammo of -1 is used for a melee/infinite ammo weapon
        self.currAmmo : int
        self.maxAmmo = maxAmmo

        self.reserveClips : int 
        self.clipSize = clipSize

        self.bullet: Bullet = bullet
  
    def reload(self) -> None:
        if self.maxAmmo == -1:
            return
        if self.reserveClips <= 0:
            return
        if self.currAmmo == self.clipSize:
            return
        self.reserveClips -= 1
        self.currAmmo = self.clipSize
        
    def shoot(self) -> None:
        if self.maxAmmo == -1:
            return
        if self.currAmmo > 0:
            # TODO : spawn bullet here
            
            self.currAmmo -= 1
        else:
            reload()
        
        
        