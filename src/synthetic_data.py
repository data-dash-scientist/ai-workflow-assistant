"""Génération de tickets clients 100% synthétiques pour "Atelier Nimba",
une entreprise fictive utilisée uniquement à des fins de démonstration.

Aucune donnée réelle, aucun client réel, aucune entreprise réelle n'est
utilisée dans ce module. Les textes sont générés par combinaison de
gabarits et de valeurs aléatoires contrôlées (graine fixée -> reproductible).
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Literal

Category = Literal["devis", "reclamation", "support_technique", "facturation", "spam"]

CATEGORIES: list[Category] = [
    "devis",
    "reclamation",
    "support_technique",
    "facturation",
    "spam",
]

_PRODUITS = ["étagère sur mesure", "table basse", "banc d'entrée", "bibliothèque", "meuble TV"]
_PRENOMS = ["Awa", "Moussa", "Fatou", "Ibrahima", "Khady", "Cheikh", "Aissatou", "Modou"]

_GABARITS: dict[Category, list[str]] = {
    "devis": [
        "Bonjour, je souhaiterais un devis pour {produit}. Pouvez-vous me "
        "indiquer le prix et le délai de fabrication ?",
        "Bonjour, combien coûterait {produit} en chêne massif ? Merci de me "
        "recontacter rapidement.",
    ],
    "reclamation": [
        "Bonjour, {produit} livré(e) la semaine dernière présente une rayure. "
        "Je souhaite un geste commercial ou un échange.",
        "Je ne suis pas satisfait(e) de {produit} reçu(e), la finition ne "
        "correspond pas à la commande initiale.",
    ],
    "support_technique": [
        "Bonjour, je n'arrive pas à assembler {produit}, la notice me semble "
        "incomplète. Pouvez-vous m'aider ?",
        "Un des pieds de {produit} est manquant dans le colis, comment "
        "procéder ?",
    ],
    "facturation": [
        "Bonjour, je n'ai pas reçu la facture pour ma commande de {produit}, "
        "pouvez-vous me la renvoyer ?",
        "Le montant prélevé pour {produit} ne correspond pas au devis signé, "
        "merci de vérifier.",
    ],
    "spam": [
        "Félicitations ! Vous avez gagné un bon d'achat, cliquez ici pour le "
        "récupérer avant expiration.",
        "Promotion exceptionnelle sur des produits sans rapport avec votre "
        "activité, profitez-en maintenant.",
    ],
}


@dataclass
class Ticket:
    ticket_id: str
    sender_name: str
    text: str
    true_category: Category
    metadata: dict = field(default_factory=dict)


def generate_tickets(n: int = 60, seed: int = 42) -> list[Ticket]:
    """Génère `n` tickets synthétiques, répartis équitablement entre catégories.

    La graine (`seed`) fixe la génération pour garantir la reproductibilité
    des résultats annoncés dans le README (même jeu de données à chaque
    exécution).
    """
    rng = random.Random(seed)
    tickets: list[Ticket] = []
    for i in range(n):
        category = CATEGORIES[i % len(CATEGORIES)]
        gabarit = rng.choice(_GABARITS[category])
        produit = rng.choice(_PRODUITS)
        prenom = rng.choice(_PRENOMS)
        text = gabarit.format(produit=produit)
        tickets.append(
            Ticket(
                ticket_id=f"TCK-{i + 1:04d}",
                sender_name=prenom,
                text=text,
                true_category=category,
                metadata={"produit": produit},
            )
        )
    rng.shuffle(tickets)
    return tickets


if __name__ == "__main__":
    for t in generate_tickets(10):
        print(t.ticket_id, t.true_category, "->", t.text)
