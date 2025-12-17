# Un carré composé de 2 triangles

from .triangle import Triangle


class Carre:
    def __init__(self, p1, p2, p3, p4):
        # Tu peux vérifier que c'est un carré si tu veux
        # mais pas obligatoire pour le TP.

        self.points = [p1, p2, p3, p4]

        # Triangulation classique d’un carré
        self.triangle1 = Triangle(p1, p2, p3)
        self.triangle2 = Triangle(p1, p3, p4)

    def triangles(self):
        return [self.triangle1, self.triangle2]
