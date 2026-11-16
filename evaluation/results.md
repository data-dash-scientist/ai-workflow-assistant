# Résultats d'évaluation — AI Workflow Assistant

Généré le 2026-11-13.

Jeu de données synthétique : 200 tickets, graine `seed=42` (reproductible).

**Exactitude globale (accuracy) : 1.0**

| Catégorie | Précision | Rappel | F1 | Support |
|---|---|---|---|---|
| devis | 1.0 | 1.0 | 1.0 | 40 |
| reclamation | 1.0 | 1.0 | 1.0 | 40 |
| support_technique | 1.0 | 1.0 | 1.0 | 40 |
| facturation | 1.0 | 1.0 | 1.0 | 40 |
| spam | 1.0 | 1.0 | 1.0 | 40 |

## Matrice de confusion

| Réel \ Prédit | devis | reclamation | support_technique | facturation | spam |
|---|---|---|---|---|---|
| devis | 40 | 0 | 0 | 0 | 0 |
| reclamation | 0 | 40 | 0 | 0 | 0 |
| support_technique | 0 | 0 | 40 | 0 | 0 |
| facturation | 0 | 0 | 0 | 40 | 0 |
| spam | 0 | 0 | 0 | 0 | 40 |

## Limites

- Le classifieur par défaut (`RuleBasedClassifier`) est un classifieur par mots-clés, déterministe et sans apprentissage : ses bonnes performances sur ce jeu de données s'expliquent par la proximité entre les gabarits de génération et les règles de classification. Il ne mesure pas la capacité à généraliser à des textes réels et variés.
- Un backend `LLMClassifier` est fourni dans `src/classifier.py` pour évaluer un vrai modèle de langage, au prix d'une clé d'API et d'une perte de déterminisme strict.
- Le jeu de données est entièrement synthétique et fictif ; il ne reflète pas la diversité et le bruit des messages clients réels.