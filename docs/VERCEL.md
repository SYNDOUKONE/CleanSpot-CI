# Déployer CleanSpot CI sur Vercel

Cette branche rend le projet déployable sur Vercel en mode **démonstration** :
frontend React (statique) + API FastAPI en fonction serverless Python, servis
depuis le même domaine.

## Ce qui tourne sur Vercel

| Composant | Comportement sur Vercel |
| --- | --- |
| Frontend React | Build Vite statique (`frontend/dist`), servi à la racine |
| API FastAPI | `api/index.py` → toutes les routes `/api/*` via rewrite |
| Base de données | SQLite dans `/tmp` — **éphémère**, réinitialisée à chaque cold start |
| Détection | `MockDetector` (aucun poids embarqué) ; YOLO ne tient pas en serverless |
| Images | `/tmp` (éphémère) ou MinIO/S3 via variables d'environnement |

Le clustering des hotspots utilise une implémentation pur NumPy (haversine),
sans scikit-learn, et le traitement d'image utilise Pillow au lieu d'OpenCV —
les deux pour rester sous la limite de taille des fonctions serverless.

## Étapes de déploiement

1. **Importer le projet** : [vercel.com/new](https://vercel.com/new) → sélectionner
   `SYNDOUKONE/CleanSpot-CI`, puis la branche `vibe/vercel-deploy-583070`.
2. **Framework Preset** : Other (la config `vercel.json` suffit).
3. **Variables d'environnement** (optionnel) :
   - `CLEANSPOT_DATABASE_URL` : URL Neon/Vercel Postgres en `postgresql+psycopg2://...`
     pour garder les observations entre les redémarrages.
   - `CLEANSPOT_S3_ENDPOINT`, `CLEANSPOT_S3_BUCKET`, `CLEANSPOT_S3_ACCESS_KEY`,
     `CLEANSPOT_S3_SECRET_KEY` : stockage MinIO/S3 persistant des images.
4. **Deploy**. L'app est disponible sur `https://<projet>.vercel.app`
   (scanner + carte + hotspots fonctionnels en mode démo).

## Limitations du mode démo

- La base est vidée à chaque cold start (sauf Postgres configuré).
- Le détecteur `MockDetector` produit des détections synthétiques : les
  résultats ne sont pas de vraies inférences. Utiliser le backend complet
  (Docker / uvicorn + `models/detection/best.pt`) pour de l'inférence réelle.
- La segmentation renvoie des masques grossiers dérivés des boîtes détectées.

## Alternative pour le backend complet

Pour un backend réel (YOLO + persistance) : Render, Railway ou un VPS avec
`docker compose up` — le frontend dessus pointe alors vers ce backend via la
variable `VITE_API_URL`.
