#!/usr/bin/env python
"""Télécharge les datasets ouverts TACO et pLitterStreet.

Usage :
    python scripts/download_datasets.py --taco
    python scripts/download_datasets.py --plitterstreet   # 13,7 Go, long

Attention aux licences : vérifier fichier par fichier avant toute
redistribution ou utilisation commerciale. La fiche Zenodo de
pLitterStreet ne renseigne pas de licence globale.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TACO_URL = "https://zenodo.org/records/3354286/files/TACO.zip"
PLITTER_URL = "https://zenodo.org/records/8288500/files/plitterstreet.zip"


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    print(f"Téléchargement de {url} vers {destination}...")
    subprocess.run(
        [
            "curl",
            "-L",
            "--fail",
            "--progress-bar",
            "-o",
            str(destination),
            url,
        ],
        check=True,
    )


def unzip(archive: Path, target: Path) -> None:
    print(f"Décompression de {archive} vers {target}...")
    subprocess.run(["unzip", "-q", str(archive), "-d", str(target)], check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--taco", action="store_true", help="Télécharger TACO (~1,1 Go)")
    parser.add_argument(
        "--plitterstreet", action="store_true", help="Télécharger pLitterStreet (~13,7 Go)"
    )
    args = parser.parse_args()
    if not (args.taco or args.plitterstreet):
        parser.error("Choisir au moins un dataset (--taco, --plitterstreet)")

    if args.taco:
        archive = ROOT / "datasets" / "taco" / "TACO.zip"
        download(TACO_URL, archive)
        unzip(archive, ROOT / "datasets" / "taco")

    if args.plitterstreet:
        archive = ROOT / "datasets" / "plitterstreet" / "plitterstreet.zip"
        download(PLITTER_URL, archive)
        unzip(archive, ROOT / "datasets" / "plitterstreet")

    print("Vérifier les licences avant toute redistribution.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
