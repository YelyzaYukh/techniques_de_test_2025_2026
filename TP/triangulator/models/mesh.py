from .edge import Edge


class Mesh:
    def __init__(self, points=None):
        self.points = points or []
        self.edges = []

    def add_point(self, p):
        self.points.append(p)

    def add_edge(self, p1, p2):
        edge = Edge(p1, p2)
        self.edges.append(edge)
        return edge

    def segment_exists(self, p1, p2) -> bool:
        return any(
            (e.p1 == p1 and e.p2 == p2) or (e.p1 == p2 and e.p2 == p1)
            for e in self.edges
        )
