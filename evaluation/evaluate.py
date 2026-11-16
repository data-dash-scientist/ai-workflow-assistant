"""Évaluation du classifieur de tickets sur le jeu de données synthétique.

Exécution :
    python -m evaluation.evaluate

Produit :
    - Un tableau de métriques par catégorie (precision / recall / f1)
    - Une matrice de confusion simple (dict imbriqué)
    - Un fichier evaluation/results.md avec les résultats horodatés

Les résultats sont entièrement reproductibles : le jeu de données est
généré avec une graine fixe (voir src/synthetic_data.py).
"""
from __future__ import annotations

import datetime
from collections import defaultdict

from src.classifier import RuleBasedClassifier
from src.synthetic_data import CATEGORIES, generate_tickets

N_TICKETS = 200
SEED = 42


def evaluate() -> dict:
    tickets = generate_tickets(n=N_TICKETS, seed=SEED)
    classifier = RuleBasedClassifier()

    confusion: dict[str, dict[str, int]] = {
        true_cat: {pred_cat: 0 for pred_cat in CATEGORIES} for true_cat in CATEGORIES
    }

    for ticket in tickets:
        result = classifier.classify(ticket.text, ticket.sender_name)
        confusion[ticket.true_category][result.category] += 1

    metrics = {}
    for cat in CATEGORIES:
        tp = confusion[cat][cat]
        fp = sum(confusion[other][cat] for other in CATEGORIES if other != cat)
        fn = sum(confusion[cat][other] for other in CATEGORIES if other != cat)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        metrics[cat] = {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "support": tp + fn,
        }

    total_correct = sum(confusion[cat][cat] for cat in CATEGORIES)
    accuracy = round(total_correct / N_TICKETS, 3)

    return {
        "n_tickets": N_TICKETS,
        "seed": SEED,
        "accuracy": accuracy,
        "metrics_by_category": metrics,
        "confusion_matrix": confusion,
    }


def format_report(results: dict) -> str:
    lines = []
    lines.append("# Résultats d'évaluation — AI Workflow Assistant")
    lines.append("")
    lines.append(f"Généré le {datetime.date.today().isoformat()}.")
    lines.append("")
    lines.append(
        f"Jeu de données synthétique : {results['n_tickets']} tickets, "
        f"graine `seed={results['seed']}` (reproductible)."
    )
    lines.append("")
    lines.append(f"**Exactitude globale (accuracy) : {results['accuracy']}**")
    lines.append("")
    lines.append("| Catégorie | Précision | Rappel | F1 | Support |")
    lines.append("|---|---|---|---|---|")
    for cat, m in results["metrics_by_category"].items():
        lines.append(
            f"| {cat} | {m['precision']} | {m['recall']} | {m['f1']} | {m['support']} |"
        )
    lines.append("")
    lines.append("## Matrice de confusion")
    lines.append("")
    header = "| Réel \\ Prédit | " + " | ".join(results["confusion_matrix"].keys()) + " |"
    sep = "|---" * (len(results["confusion_matrix"]) + 1) + "|"
    lines.append(header)
    lines.append(sep)
    for true_cat, row in results["confusion_matrix"].items():
        lines.append(f"| {true_cat} | " + " | ".join(str(v) for v in row.values()) + " |")
    lines.append("")
    lines.append(
        "## Limites\n\n"
        "- Le classifieur par défaut (`RuleBasedClassifier`) est un classifieur "
        "par mots-clés, déterministe et sans apprentissage : ses bonnes "
        "performances sur ce jeu de données s'expliquent par la proximité entre "
        "les gabarits de génération et les règles de classification. Il ne "
        "mesure pas la capacité à généraliser à des textes réels et variés.\n"
        "- Un backend `LLMClassifier` est fourni dans `src/classifier.py` pour "
        "évaluer un vrai modèle de langage, au prix d'une clé d'API et d'une "
        "perte de déterminisme strict.\n"
        "- Le jeu de données est entièrement synthétique et fictif ; il ne "
        "reflète pas la diversité et le bruit des messages clients réels."
    )
    return "\n".join(lines)


if __name__ == "__main__":
    results = evaluate()
    report = format_report(results)
    print(report)
    with open("evaluation/results.md", "w", encoding="utf-8") as f:
        f.write(report)
