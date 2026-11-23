# Enterprise AI Agent

Assistant documentaire : import de PDF, questions en langage naturel, agent LangGraph
avec RAG, outils et auto-vérification. Voir le cahier des charges pour le détail.

## Démarrage rapide

```bash
cp .env.example .env
make up                 # backend + Qdrant
curl localhost:8000/health
```

- API et documentation : http://localhost:8000/docs
- Tableau de bord Qdrant : http://localhost:6333/dashboard

## Développement

```bash
make install            # dépendances de dev
make hooks              # pre-commit
make check              # ruff + mypy + pytest (comme la CI)
make up-dev             # Docker avec rechargement automatique
make samples            # télécharge les PDF de démonstration
```

## Structure

`backend/app/` : api, core, ingestion, retrieval, agent, tools, evaluation, models.
`eval/` : jeu d'évaluation. `data/` : documents (non versionnés).

## Feuille de route (7 jours)

J1 socle · J2 ingestion · J3 RAG · J4 agent · J5 frontend · J6 évaluation · J7 finitions.