## PLAN DE TEST — Projet Triangulator
### 1. Contexte et Contraintes
#### 1.1 Ressources

**Temps disponible** : 21 heures (7 séances de TP)

**Équipe** : Individuel

**Environnement technique** : Python 3.10+, Flask, pytest, coverage, ruff

**Contraintes** : Implémentation de la triangulation “from scratch”, dépendances minimales

**Mécanismes de test** : Gestion de configuration, intégration continue, évaluation de couverture

**Expérience** : Niveau junior

#### 1.2 Objectifs du projet

Développement selon une approche test-first

Validation du comportement conforme aux spécifications OpenAPI

Mesure de la performance et de la qualité du code

Atteindre une couverture de code maximale avec des tests pertinents


---
### 2. Stratégie Globale de Test
#### 2.1 Approche

La stratégie suivra une pyramide de tests :

1) Base large : **tests unitaires** exhaustifs
   
2) Niveau intermédiaire : **tests d’intégration**
   
3) Sommet : **tests de bout-en-bout sur l’API REST**

Cette approche est justifiée par :

- La nature algorithmique du composant de triangulation
  
- Les interactions HTTP avec le module PointSetManager
  
- La nécessité de valider les formats binaires produits

#### 2.2 Principe "Test-First"

* Rédiger les tests avant l’implémentation
* Coder pour faire passer les tests
* Refactoriser avec validation continue
---
### 3. Types de Tests à Implémenter
Structure des répertoires

tests/
├── unit/
│ ├── test_serialization.py
│ ├── test_triangulation.py
│ └── test_pointset_client.py

├── integration/
│ ├── test_pipeline.py
│ └── test_api.py

├── performance/
│ └── test_perf.py

├── fixtures/
│ └── geometry_fixtures.py
└── conftest.py

---

### 3.1 Tests Unitaires

#### 3.1.1 Sérialisation / Désérialisation binaire
**Objectif :** Vérifier la conversion correcte entre structures Python et format binaire.  

**Composants testés :**
- `PointSetSerializer` : conversion *PointSet ↔ binaire*  
- `TrianglesSerializer` : conversion *Triangles ↔ binaire*  

**Cas à couvrir :**
  *Cas normaux* :  
  - Sérialiser/désérialiser un petit ensemble de points  
  - Vérifier l’identité après un aller-retour binaire  
  - Tester différentes tailles (3, 10, 100 éléments)  
  *Cas limites* :  
  - Ensemble vide, un seul point, deux points  
  - Coordonnées extrêmes ou négatives  
   *Cas d’erreur* :  
  - Données binaires tronquées ou corrompues  
  - Incohérences de taille ou d’indices  

**Méthode :**  
Tests paramétrés avec `pytest.mark.parametrize` pour couvrir plusieurs tailles et formats.

---

#### 3.1.2 Algorithme de Triangulation
**Objectif :** Vérifier la justesse géométrique et la robustesse de l’algorithme.  

**Composant testé :** `Triangulator.triangulate(pointset) → triangles`

**Cas à couvrir :**
-  *Cas géométriques connus* :  
  - Triangle → 1 triangle  
  - Carré → 2 triangles  
  - Formes convexes et non-convexes  
  - Points alignés correctement gérés  
- *Propriétés mathématiques* :  
  - Tous les points sont utilisés  
  - Aucun chevauchement  
  - Pas de triangles dégénérés (aire nulle)  
  - Vérification de la formule d’Euler  
  - Orientation cohérente  
- *Cas limites* :  
  - Points dupliqués ou très proches  
  - Ensemble partiellement colinéaire  
- *Cas impossibles* :  
  - Moins de 3 points  
  - Tous les points colinéaires  

**Méthode :**  
Utilisation de *fixtures* géométriques de référence (`geometry_fixtures.py`).

---

#### 3.1.3 Client HTTP vers PointSetManager
**Objectif :** Vérifier le comportement du client face aux réponses HTTP.  

**Composant testé :** `PointSetManagerClient.get_pointset(pointset_id)`

**Cas à couvrir :**
- 200 → Succès, désérialisation correcte  
- 400 → UUID invalide  
- 404 → PointSet inexistant  
- 503 → Service indisponible  
- Timeout / erreur réseau  

**Méthode :**  
Mocks avec `unittest.mock` ou `responses` pour simuler les requêtes sortantes.

---

### 3.2 Tests d’Intégration

#### 3.2.1 Pipeline interne complet
**Objectif :** Vérifier la cohérence du flux complet sans HTTP.  

**Flux testé :**  
`pointset_id → récupération → désérialisation → triangulation → sérialisation → binaire final`

**Vérifications :**
- Fonctionnement nominal du pipeline  
- Propagation correcte des erreurs  
- Cohérence des transformations  

**Méthode :** Tests d’intégration avec mocks partiels.

---

#### 3.2.2 API REST (End-to-End)
**Objectif :** Vérifier la conformité de l’API à la spécification OpenAPI.  

**Endpoint :** `GET /triangulation/{pointSetId}`

**Cas à couvrir :**
- 200 → Triangulation réussie, format binaire correct  
- 400 → UUID malformé  
- 404 → PointSet inexistant  
- 500 → Échec de triangulation  
- 503 → Service PointSetManager inaccessible  

**Vérifications :**
- `Content-Type: application/octet-stream` en cas de succès  
- `Content-Type: application/json` pour les erreurs  

**Méthode :**  
Tests avec `Flask.app.test_client()` et mocks du PointSetManager.

---

### 3.3 Tests de Performance
**Objectif :** Mesurer les temps de traitement et identifier les goulots d’étranglement.  
**Marquage :** `@pytest.mark.performance` pour exclusion via `make unit_test`  

**Scénarios :**
- Triangulation avec 10, 100, 1 000 et 10 000 points  
- Sérialisation/désérialisation de structures volumineuses  
- Requêtes HTTP concurrentes simulées  

---

## 4. Qualité et Documentation

### 4.1 Couverture de Code
- **Objectif :** ≥ 95 % de couverture  
- **Commande :** `make coverage` → rapport HTML  

**Zones critiques à couvrir :**
- Chemins d’erreur  
- Branches conditionnelles  
- Gestion des exceptions  

---

### 4.2 Qualité du Code (Linting)
- **Outil :** `ruff check`  
- **Règles :**  
  - Docstrings obligatoires  
  - Convention PEP 8  
  - Complexité raisonnable  
  - Aucun code mort  
- **Commande :** `make lint` (0 erreur attendue)  

---

## 5. Gestion des Risques et Priorisation

### 5.1 Risques Identifiés
- Complexité de la triangulation → commencer simple  
- Manipulation du format binaire → tests exhaustifs  
- Temps limité → priorité aux tests unitaires  

### 5.2 Priorisation
| Priorité | Composants | Justification |
|-----------|-------------|----------------|
| **Haute** | Sérialisation / API / Triangulation simple | Bloquants |
| **Moyenne** | Triangulation complexe / Pipeline / Erreurs | Secondaire |
| **Basse** | Tests de performance / Optimisations | Optionnels |

---

## 6. Critères de Succès

### 6.1 Fonctionnels
- Tous les tests unitaires passent  
- API conforme à OpenAPI  
- Triangulation correcte pour ≤ 100 points  
- Format binaire valide  

### 6.2 Qualité
- Couverture ≥ 90 %  
- `make lint` sans erreur  
- Documentation complète  

### 6.3 Performance
- Triangulation < 1 s pour 1 000 points  

---

## 7. Planning Prévisionnel

| Séance | Durée | Objectifs |
|---------|--------|------------|
| **1** | 3h | Rédaction du plan (✓), structure du projet |
| **2** | 3h | Tests de sérialisation et triangulation simples |
| **3** | 3h | Tests API, mocks PointSetManager |
| **4** | 3h | Mise en place complète des tests |
| **5** | 3h | Implémentation finale et corrections |
| **6** | 3h | Tests de performance, documentation |
| **7** | 3h | Rendu final + retour d’expérience (RETEX) |

