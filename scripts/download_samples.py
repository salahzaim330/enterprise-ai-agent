#!/usr/bin/env python3
"""Télécharge les PDF publics de démonstration dans data/sample_pdfs/.

Usage : python scripts/download_samples.py [--include-optional]
Ne dépend que de la bibliothèque standard.
"""

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

DEST = Path(__file__).resolve().parent.parent / "data" / "sample_pdfs"
MAX_BYTES = 50 * 1024 * 1024  # même limite que l'upload de l'application

SOURCES = [
    {
        "file": "nist-sp-800-190-containers.pdf",
        "title": "NIST SP 800-190, Application Container Security Guide",
        "url": "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-190.pdf",
        "lang": "en",
        "optional": False,
    },
    {
        "file": "nist-ai-100-1-ai-rmf.pdf",
        "title": "NIST AI 100-1, AI Risk Management Framework",
        "url": "https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf",
        "lang": "en",
        "optional": False,
    },
    {
        "file": "anssi-guide-hygiene-informatique-fr.pdf",
        "title": "ANSSI, Guide d'hygiène informatique (FR)",
        "url": "https://draaf.nouvelle-aquitaine.agriculture.gouv.fr/IMG/pdf/guide_hygiene_informatique_anssi_cle04b262.pdf",
        "lang": "fr",
        "optional": False,
    },
    {
        "file": "owasp-asvs-4.0.3.pdf",
        "title": "OWASP Application Security Verification Standard 4.0.3",
        "url": "https://github.com/OWASP/ASVS/raw/v4.0.3/4.0/OWASP%20Application%20Security%20Verification%20Standard%204.0.3-en.pdf",
        "lang": "en",
        "optional": False,
    },
    {
        "file": "nist-sp-800-53r5.pdf",
        "title": "NIST SP 800-53 Rev. 5 (test de charge, ~480 pages)",
        "url": "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf",
        "lang": "en",
        "optional": True,
    },
]


def download(url: str, target: Path) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "enterprise-ai-agent/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("fichier trop volumineux (> 50 Mo)")
    if not data.startswith(b"%PDF"):
        raise ValueError("le contenu n'est pas un PDF (page HTML ou redirection ?)")
    target.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-optional", action="store_true")
    args = parser.parse_args()

    DEST.mkdir(parents=True, exist_ok=True)
    manifest, failures = [], 0
    for source in SOURCES:
        if source["optional"] and not args.include_optional:
            print(f"- {source['file']}: ignoré (optionnel, utilise --include-optional)")
            continue
        target = DEST / source["file"]
        try:
            if target.exists():
                sha = hashlib.sha256(target.read_bytes()).hexdigest()
                print(f"= {source['file']}: déjà présent")
            else:
                sha = download(source["url"], target)
                print(f"+ {source['file']}: téléchargé ({target.stat().st_size // 1024} Ko)")
            manifest.append({**source, "sha256": sha})
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"! {source['file']}: ÉCHEC ({exc})\n  Télécharge-le à la main : {source['url']}")
    (DEST / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())