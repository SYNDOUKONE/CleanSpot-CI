# CleanSpot CI

**Détection intelligente des dépôts sauvages de déchets à Abidjan** — Computer Vision, Deep Learning et Smart City.

L'IA détecte les déchets abandonnés dans l'espace public (bouteilles plastiques, sachets, canettes, cartons, amas), distingue une zone propre d'une accumulation, associe chaque observation à une position GPS et cartographie les zones à inspecter en priorité.

> ⚠️ Un système ne déclare jamais un dépôt illégal tout seul : la catégorie « dépôt suspect » déclenche une **vérification humaine** sur le terrain.

---

## Architecture

```
Application React / PWA (Scanner, Carte, Dashboard, Gestion)
        │
FastAPI ── détection YOLO ── segmentation YOLO-Seg ── classification de zone
        │                                    │
DBSCAN + haversine (hotspots)          MinIO / stockage local
        │
PostgreSQL (+PostGIS en production) / SQLite (proto)
```

| Domaine | Outil |
| --- | --- |
| Deep Learning | PyTorch (Ultralytics YOLOv8n / YOLO11n) |
| Segmentation | YOLO-Seg / Mask R-CNN / U-Net |
| Annotation | CVAT (format COCO → YOLO via `scripts/taco_to_yolo.py`) |
| API | FastAPI |
| Frontend | React + Vite + Leaflet |
| Clustering | DBSCAN (métrique haversine) |
| Dashboard | Streamlit + Plotly |
| Déploiement | Docker Compose |

## Structure

```
CleanSpot-CI/
├── datasets/            # taco/, plitterstreet/, cleanspot_ci/ (jamais committés)
├── notebooks/           # 01 exploration … 05 évaluation
├── models/              # poids détecteur / segmenteur (non committés)
├── backend/             # API FastAPI + logique métier + tests
│   └── app/
│       ├── detection.py       # YOLO + encodage image
│       ├── segmentation.py    # amas de déchets (masques, surface souillée)
│       ├── zones.py           # 4 situations : propre / isolé / accumulation / suspect
│       ├── geolocation.py     # fusion des passages + DBSCAN + scoring hotspots
│       ├── storage.py         # MinIO/S3 ou système de fichiers
│       └── routes/            # /api/analyze, /api/observations, /api/hotspots, /api/stats
├── frontend/            # app web React (Scanner, Carte, Dashboard, Gestion)
├── dashboard/           # Streamlit + Plotly
├── evaluation/          # métriques (P/R/F1, IoU, Dice, cartographie)
├── scripts/             # téléchargement datasets, conversion TACO→YOLO, démo
├── configs/             # hyperparamètres d'entraînement
└── docker-compose.yml   # api, db (PostGIS), minio
```

## Classes détectées

| Classe | Élément |
| --- | --- |
| `plastic_bottle` | Bouteilles plastiques |
| `plastic_bag` | Sachets et films plastiques |
| `metal_can` | Canettes métalliques |
| `paper_cardboard` | Papier et cartons |
| `mixed_waste` | Déchets mélangés, amas |

Quatre situations par zone : `clean_zone`, `isolated_waste`, `accumulation`, `suspect_deposit`.

## Démarrage rapide (sans GPU ni entraînement)

Les poids YOLOv8n COCO (`yolov8n.pt`, 6 Mo) sont vendus dans le dépôt : l'API fait **de la vraie inférence** via `CocoTrashDetector` (bouteilles, gobelets/canettes, cartons projetés sur les 5 classes). Les classes absentes de COCO (sachets, amas) nécessitent des poids entraînés sur TACO/pLitterStreet/CleanSpot — voir ci-dessous. Chaîne de repli : `best.pt` entraîné → `yolov8n.pt` COCO → détecteur de démonstration.

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload          # http://localhost:8000/docs

python ../scripts/seed_demo_data.py    # observations + hotspots de démonstration

cd ../frontend && npm install && npm run dev   # http://localhost:5173
```

Dashboard analytique :

```bash
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

## Entraînement réel

1. **Données** : `python scripts/download_datasets.py --taco` (TACO, ~1,1 Go) puis `--plitterstreet` (13,7 Go, long).
2. **Conversion** : `python scripts/taco_to_yolo.py --taco-dir datasets/taco --out-dir datasets/taco/yolo_cleanspot`.
3. **Annotation CVAT** du dataset ivoirien (Yopougon, Abobo, Adjamé) — inclure aussi des **rues propres** comme exemples négatifs.
4. **Entraînement** : `notebooks/03_object_detection.ipynb` (config dans `configs/train_detection.yaml`).
5. **Poids** : copier `best.pt` dans `models/detection/` et `best-seg.pt` dans `models/segmentation/`, puis redémarrer l'API.

## Métriques suivies

- **Détection** : Precision, Recall, F1, mAP@50, mAP@50-95 (`evaluation/metrics.py`).
- **Segmentation** : IoU, Dice, mAP de segmentation.
- **Cartographie** : taux de signalements confirmés, faux signalements par parcours, couverture des zones d'accumulation connues.

**Point scientifique** : splits séparés par parcours et par zone géographique — aucune image d'un même parcours dans train et test.

## API principale

| Méthode | Route | Rôle |
| --- | --- | --- |
| POST | `/api/analyze` | Analyser une image (+GPS optionnel) → détections + zone + observation |
| GET | `/api/observations` | Lister / filtrer les observations |
| PATCH | `/api/observations/{id}/validate` | Validation humaine (confirmée / rejetée) |
| POST | `/api/hotspots/refresh` | Recalculer les hotspots DBSCAN |
| GET | `/api/hotspots` | Zones d'accumulation classées par score |
| GET | `/api/stats` | Agrégats pour le dashboard |

## Docker Compose (API + PostGIS + MinIO)

```bash
docker compose up --build
```

Identifiants de démonstration dans `docker-compose.yml` — à changer avant tout déploiement réel.

## Datasets & licences

- [TACO — Trash Annotations in Context](https://zenodo.org/records/3354286)
- [pLitterStreet](https://zenodo.org/records/8288500)
- `models/detection/yolov8n.pt` : poids YOLOv8n pré-entraînés COCO, © Ultralytics sous [AGPL-3.0](https://github.com/ultralytics/ultralytics/blob/main/LICENSE) — utilisés uniquement pour l'inférence de démonstration ; pour un usage commercial, entraîner/servir des poids sans AGPL ou obtenir une licence Ultralytics

Vérifier les licences fichier par fichier avant toute redistribution ou usage commercial ; la fiche pLitterStreet ne renseigne pas de licence globale.

## Références

- Rapport annuel de performance 2024, Gouvernement de Côte d'Ivoire (dgbf.ci) — 1 578 234 t collectées vers Kossihouen, 75,3 % de la prévision.
