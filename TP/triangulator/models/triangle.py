class Triangle:
    def __init__(self, p1, p2, p3):
        # Vérification colinéarité
        if self._are_collinear(p1, p2, p3):
            raise ValueError("Les trois points sont collinéaires, pas un triangle valide.")

        self.p1 = p1
        self.p2 = p2
        self.p3 = p3

    @staticmethod
    def _are_collinear(a, b, c) -> bool:
        # Aire du triangle = 0 si colinéaire
        return abs((b[0] - a[0]) * (c[1] - a[1]) -
                   (c[0] - a[0]) * (b[1] - a[1])) < 1e-10
