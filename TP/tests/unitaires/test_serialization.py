"""
Auteur: Yelyzaveta YUKHNOVA
Date: Novembre 2025
Description:
Tests unitaires pour la sérialisation/désérialisation binaire.

Ce module teste les conversions entre structures Python et format binaire
pour PointSet et Triangles selon la spécification OpenAPI.
"""

import struct
import pytest
from typing import List, Tuple

# Pour l'instant, on définit des stubs pour que les tests compilent


class PointSet:
    """Représentation interne d'un ensemble de points."""
    
    def __init__(self, points: List[Tuple[float, float]]):
        """
        Initialise un PointSet.
        
        Args:
            points: Liste de tuples (x, y) représentant les coordonnées
        """
        self.points = points
    
    def __eq__(self, other):
        """Compare deux PointSet pour l'égalité."""
        if not isinstance(other, PointSet):
            return False
        return self.points == other.points


class Triangles:
    """Représentation interne d'un ensemble de triangles."""
    
    def __init__(self, vertices: List[Tuple[float, float]], 
                 triangles: List[Tuple[int, int, int]]):
        """
        Initialise un ensemble de triangles.
        
        Args:
            vertices: Liste de tuples (x, y) pour les sommets
            triangles: Liste de tuples (i1, i2, i3) d'indices de sommets
        """
        self.vertices = vertices
        self.triangles = triangles
    
    def __eq__(self, other):
        """Compare deux Triangles pour l'égalité."""
        if not isinstance(other, Triangles):
            return False
        return (self.vertices == other.vertices and 
                self.triangles == other.triangles)


class PointSetSerializer:
    """Sérialiseur pour PointSet."""
    
    @staticmethod
    def serialize(pointset: PointSet) -> bytes:
        """
        Convertit un PointSet en format binaire.
        
        Format:
        - 4 bytes: nombre de points (unsigned long)
        - N * 8 bytes: points (float x, float y pour chaque point)
        
        Args:
            pointset: Le PointSet à sérialiser
            
        Returns:
            Les données binaires
            
        Raises:
            ValueError: Si le PointSet est invalide
        """
        raise NotImplementedError("À implémenter")
    
    @staticmethod
    def deserialize(data: bytes) -> PointSet:
        """
        Convertit des données binaires en PointSet.
        
        Args:
            data: Les données binaires
            
        Returns:
            Le PointSet reconstruit
            
        Raises:
            ValueError: Si les données sont invalides
        """
        raise NotImplementedError("À implémenter")


class TrianglesSerializer:
    """Sérialiseur pour Triangles."""
    
    @staticmethod
    def serialize(triangles: Triangles) -> bytes:
        """
        Convertit des Triangles en format binaire.
        
        Format:
        Partie 1 (vertices):
        - 4 bytes: nombre de sommets (unsigned long)
        - N * 8 bytes: sommets (float x, float y)
        
        Partie 2 (triangles):
        - 4 bytes: nombre de triangles (unsigned long)
        - T * 12 bytes: triangles (3 * unsigned long indices)
        
        Args:
            triangles: Les Triangles à sérialiser
            
        Returns:
            Les données binaires
            
        Raises:
            ValueError: Si les Triangles sont invalides
        """
        raise NotImplementedError("À implémenter")
    
    @staticmethod
    def deserialize(data: bytes) -> Triangles:
        """
        Convertit des données binaires en Triangles.
        
        Args:
            data: Les données binaires
            
        Returns:
            Les Triangles reconstruites
            
        Raises:
            ValueError: Si les données sont invalides
        """
        raise NotImplementedError("À implémenter")


# ============================================================================
# TESTS POINTSET
# ============================================================================

class TestPointSetSerialization:
    """Tests de sérialisation pour PointSet."""
    
    def test_serialize_simple_pointset(self):
        """Test sérialisation d'un PointSet simple (3 points)."""
        points = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
        pointset = PointSet(points)
        
        data = PointSetSerializer.serialize(pointset)
        
        # Vérifier le nombre de points
        num_points = struct.unpack('<I', data[0:4])[0]
        assert num_points == 3
        
        # Vérifier la taille totale: 4 + 3*8 = 28 bytes
        assert len(data) == 28
        
        # Vérifier les coordonnées
        x1, y1 = struct.unpack('<ff', data[4:12])
        assert x1 == 0.0 and y1 == 0.0
        
        x2, y2 = struct.unpack('<ff', data[12:20])
        assert x2 == 1.0 and y2 == 0.0
        
        x3, y3 = struct.unpack('<ff', data[20:28])
        assert x3 == 0.0 and y3 == 1.0
    
    def test_deserialize_simple_pointset(self):
        """Test désérialisation d'un PointSet simple."""
        # Construire manuellement les bytes
        data = struct.pack('<I', 3)  # 3 points
        data += struct.pack('<ff', 0.0, 0.0)
        data += struct.pack('<ff', 1.0, 0.0)
        data += struct.pack('<ff', 0.0, 1.0)
        
        pointset = PointSetSerializer.deserialize(data)
        
        assert len(pointset.points) == 3
        assert pointset.points[0] == (0.0, 0.0)
        assert pointset.points[1] == (1.0, 0.0)
        assert pointset.points[2] == (0.0, 1.0)
    
    def test_roundtrip_pointset(self):
        """Test round-trip: serialize puis deserialize doit donner l'identité."""
        original = PointSet([(1.5, 2.5), (-1.0, 3.0), (0.0, 0.0)])
        
        data = PointSetSerializer.serialize(original)
        restored = PointSetSerializer.deserialize(data)
        
        assert restored == original
    
    @pytest.mark.parametrize("points", [
        [(0.0, 0.0)],  # Un seul point
        [(0.0, 0.0), (1.0, 1.0)],  # Deux points
        [(i * 0.1, i * 0.2) for i in range(10)],  # 10 points
        [(i * 1.0, i * 1.0) for i in range(100)],  # 100 points
    ])
    def test_serialize_various_sizes(self, points):
        """Test sérialisation avec différentes tailles de PointSet."""
        pointset = PointSet(points)
        data = PointSetSerializer.serialize(pointset)
        
        expected_size = 4 + len(points) * 8
        assert len(data) == expected_size
        
        # Vérifier qu'on peut désérialiser
        restored = PointSetSerializer.deserialize(data)
        assert len(restored.points) == len(points)


class TestPointSetEdgeCases:
    """Tests des cas limites pour PointSet."""
    
    def test_empty_pointset(self):
        """Test avec un PointSet vide (0 points)."""
        pointset = PointSet([])
        
        data = PointSetSerializer.serialize(pointset)
        
        # Doit contenir juste le nombre 0
        assert len(data) == 4
        num_points = struct.unpack('<I', data)[0]
        assert num_points == 0
        
        # Round-trip
        restored = PointSetSerializer.deserialize(data)
        assert len(restored.points) == 0
    
    def test_negative_coordinates(self):
        """Test avec des coordonnées négatives."""
        points = [(-5.5, -10.2), (-0.1, -100.0)]
        pointset = PointSet(points)
        
        data = PointSetSerializer.serialize(pointset)
        restored = PointSetSerializer.deserialize(data)
        
        assert restored.points[0][0] == pytest.approx(-5.5)
        assert restored.points[0][1] == pytest.approx(-10.2)
    
    def test_extreme_float_values(self):
        """Test avec des valeurs float extrêmes."""
        import sys
        points = [
            (sys.float_info.max, sys.float_info.min),
            (-sys.float_info.max, 0.0),
            (1e-10, 1e10)
        ]
        pointset = PointSet(points)
        
        data = PointSetSerializer.serialize(pointset)
        restored = PointSetSerializer.deserialize(data)
        
        # Les valeurs très grandes peuvent perdre en précision
        assert len(restored.points) == 3
    
    def test_very_close_points(self):
        """Test avec des points très proches (précision float)."""
        points = [
            (0.0, 0.0),
            (1e-7, 1e-7),
            (2e-7, 0.0)
        ]
        pointset = PointSet(points)
        
        data = PointSetSerializer.serialize(pointset)
        restored = PointSetSerializer.deserialize(data)
        
        assert len(restored.points) == 3


class TestPointSetErrorCases:
    """Tests des cas d'erreur pour PointSet."""
    
    def test_deserialize_truncated_data(self):
        """Test désérialisation avec données tronquées."""
        # Annoncer 3 points mais donner seulement 2
        data = struct.pack('<I', 3)  # 3 points annoncés
        data += struct.pack('<ff', 0.0, 0.0)
        data += struct.pack('<ff', 1.0, 1.0)
        # Manque le 3ème point
        
        with pytest.raises(ValueError, match="tronqué|incomplet|invalid"):
            PointSetSerializer.deserialize(data)
    
    def test_deserialize_too_short(self):
        """Test avec données trop courtes (moins de 4 bytes)."""
        data = b'\x01\x00'  # Seulement 2 bytes
        
        with pytest.raises(ValueError):
            PointSetSerializer.deserialize(data)
    
    def test_deserialize_empty_bytes(self):
        """Test avec bytes vides."""
        with pytest.raises(ValueError):
            PointSetSerializer.deserialize(b'')
    
    def test_deserialize_inconsistent_size(self):
        """Test avec taille de données incohérente."""
        # Annoncer 2 points mais données pour 2.5 points
        data = struct.pack('<I', 2)
        data += struct.pack('<ff', 0.0, 0.0)
        data += struct.pack('<ff', 1.0, 1.0)
        data += b'\x00\x00\x00\x00'  # 4 bytes en trop
        
        with pytest.raises(ValueError, match="taille|size|length"):
            PointSetSerializer.deserialize(data)


# ============================================================================
# TESTS TRIANGLES
# ============================================================================

class TestTrianglesSerialization:
    """Tests de sérialisation pour Triangles."""
    
    def test_serialize_simple_triangle(self):
        """Test sérialisation d'un triangle unique."""
        vertices = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
        triangles_list = [(0, 1, 2)]
        triangles = Triangles(vertices, triangles_list)
        
        data = TrianglesSerializer.serialize(triangles)
        
        # Partie 1: vertices
        num_vertices = struct.unpack('<I', data[0:4])[0]
        assert num_vertices == 3
        
        # Partie 2: triangles (commence après vertices: 4 + 3*8 = 28)
        offset = 4 + 3 * 8
        num_triangles = struct.unpack('<I', data[offset:offset+4])[0]
        assert num_triangles == 1
        
        # Vérifier les indices du triangle
        i1, i2, i3 = struct.unpack('<III', data[offset+4:offset+16])
        assert (i1, i2, i3) == (0, 1, 2)
    
    def test_deserialize_simple_triangle(self):
        """Test désérialisation d'un triangle unique."""
        # Partie 1: vertices
        data = struct.pack('<I', 3)  # 3 vertices
        data += struct.pack('<ff', 0.0, 0.0)
        data += struct.pack('<ff', 1.0, 0.0)
        data += struct.pack('<ff', 0.0, 1.0)
        
        # Partie 2: triangles
        data += struct.pack('<I', 1)  # 1 triangle
        data += struct.pack('<III', 0, 1, 2)
        
        triangles = TrianglesSerializer.deserialize(data)
        
        assert len(triangles.vertices) == 3
        assert len(triangles.triangles) == 1
        assert triangles.triangles[0] == (0, 1, 2)
    
    def test_roundtrip_triangles(self):
        """Test round-trip pour Triangles."""
        vertices = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        triangles_list = [(0, 1, 2), (0, 2, 3)]
        original = Triangles(vertices, triangles_list)
        
        data = TrianglesSerializer.serialize(original)
        restored = TrianglesSerializer.deserialize(data)
        
        assert restored == original
    
    def test_serialize_square_triangulation(self):
        """Test sérialisation d'un carré triangulé (2 triangles)."""
        vertices = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        triangles_list = [(0, 1, 2), (0, 2, 3)]
        triangles = Triangles(vertices, triangles_list)
        
        data = TrianglesSerializer.serialize(triangles)
        
        # Taille attendue: 4 + 4*8 + 4 + 2*12 = 4 + 32 + 4 + 24 = 64
        assert len(data) == 64
    
    @pytest.mark.parametrize("num_triangles", [1, 5, 10, 50])
    def test_serialize_various_triangle_counts(self, num_triangles):
        """Test avec différents nombres de triangles."""
        # Créer suffisamment de vertices
        vertices = [(float(i), float(i)) for i in range(num_triangles + 2)]
        # Créer des triangles arbitraires (peu importe s'ils sont valides)
        triangles_list = [(i, i+1, i+2) for i in range(num_triangles)]
        
        triangles = Triangles(vertices, triangles_list)
        data = TrianglesSerializer.serialize(triangles)
        
        # Vérifier la taille
        expected_size = 4 + len(vertices) * 8 + 4 + num_triangles * 12
        assert len(data) == expected_size
        
        # Vérifier qu'on peut désérialiser
        restored = TrianglesSerializer.deserialize(data)
        assert len(restored.triangles) == num_triangles


class TestTrianglesEdgeCases:
    """Tests des cas limites pour Triangles."""
    
    def test_empty_triangles(self):
        """Test avec 0 triangles (mais des vertices)."""
        vertices = [(0.0, 0.0), (1.0, 1.0)]
        triangles_list = []
        triangles = Triangles(vertices, triangles_list)
        
        data = TrianglesSerializer.serialize(triangles)
        restored = TrianglesSerializer.deserialize(data)
        
        assert len(restored.vertices) == 2
        assert len(restored.triangles) == 0
    
    def test_no_vertices_no_triangles(self):
        """Test avec structure complètement vide."""
        triangles = Triangles([], [])
        
        data = TrianglesSerializer.serialize(triangles)
        restored = TrianglesSerializer.deserialize(data)
        
        assert len(restored.vertices) == 0
        assert len(restored.triangles) == 0
    
    def test_shared_vertices(self):
        """Test où plusieurs triangles partagent des vertices."""
        vertices = [(0.0, 0.0), (1.0, 0.0), (0.5, 1.0)]
        # Deux triangles partageant un edge
        triangles_list = [(0, 1, 2), (1, 2, 0)]
        triangles = Triangles(vertices, triangles_list)
        
        data = TrianglesSerializer.serialize(triangles)
        restored = TrianglesSerializer.deserialize(data)
        
        assert restored == triangles


class TestTrianglesErrorCases:
    """Tests des cas d'erreur pour Triangles."""
    
    def test_deserialize_truncated_vertices(self):
        """Test avec vertices tronqués."""
        data = struct.pack('<I', 3)  # Annoncer 3 vertices
        data += struct.pack('<ff', 0.0, 0.0)
        # Manquent 2 vertices
        
        with pytest.raises(ValueError):
            TrianglesSerializer.deserialize(data)
    
    def test_deserialize_truncated_triangles(self):
        """Test avec triangles tronqués."""
        # Vertices complets
        data = struct.pack('<I', 3)
        data += struct.pack('<ff', 0.0, 0.0)
        data += struct.pack('<ff', 1.0, 0.0)
        data += struct.pack('<ff', 0.0, 1.0)
        
        # Triangles incomplets
        data += struct.pack('<I', 2)  # Annoncer 2 triangles
        data += struct.pack('<III', 0, 1, 2)  # Un seul triangle
        
        with pytest.raises(ValueError):
            TrianglesSerializer.deserialize(data)
    
    def test_deserialize_invalid_indices(self):
        """Test avec indices de vertices hors limites."""
        # 3 vertices
        data = struct.pack('<I', 3)
        data += struct.pack('<ff', 0.0, 0.0)
        data += struct.pack('<ff', 1.0, 0.0)
        data += struct.pack('<ff', 0.0, 1.0)
        
        # Triangle avec indice 5 (> 2, hors limites)
        data += struct.pack('<I', 1)
        data += struct.pack('<III', 0, 1, 5)
        
        with pytest.raises(ValueError, match="indice|index|out of bounds"):
            TrianglesSerializer.deserialize(data)
    
    def test_deserialize_negative_indices(self):
        """Test avec indices négatifs (si interprétés comme signed)."""
        # Note: struct '<I' est unsigned, mais on peut forcer avec de grands nombres
        data = struct.pack('<I', 3)
        data += struct.pack('<ff', 0.0, 0.0)
        data += struct.pack('<ff', 1.0, 0.0)
        data += struct.pack('<ff', 0.0, 1.0)
        
        data += struct.pack('<I', 1)
        # Utiliser un très grand unsigned int (interprété comme négatif en signed)
        data += struct.pack('<III', 0, 1, 4294967295)
        
        with pytest.raises(ValueError):
            TrianglesSerializer.deserialize(data)


# ============================================================================
# TESTS DE PROPRIÉTÉS
# ============================================================================

class TestSerializationProperties:
    """Tests des propriétés générales de la sérialisation."""
    
    def test_deterministic_serialization(self):
        """La sérialisation doit être déterministe."""
        pointset = PointSet([(1.0, 2.0), (3.0, 4.0)])
        
        data1 = PointSetSerializer.serialize(pointset)
        data2 = PointSetSerializer.serialize(pointset)
        
        assert data1 == data2
    
    def test_binary_format_is_compact(self):
        """Vérifier que le format binaire est bien compact."""
        # 10 points = 4 + 10*8 = 84 bytes
        points = [(float(i), float(i)) for i in range(10)]
        pointset = PointSet(points)
        
        data = PointSetSerializer.serialize(pointset)
        assert len(data) == 84
    
    def test_endianness_consistency(self):
        """Vérifier la cohérence du little-endian."""
        pointset = PointSet([(1.0, 2.0)])
        data = PointSetSerializer.serialize(pointset)
        
        # Premier byte de 1 (le nombre de points) doit être 1 en little-endian
        assert data[0] == 1
        assert data[1] == 0
        assert data[2] == 0
        assert data[3] == 0