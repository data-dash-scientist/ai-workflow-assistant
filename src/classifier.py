"""Couche de classification et de rédaction de réponse pour les tickets.

Deux implémentations sont fournies derrière une interface commune
`TicketClassifier` :

1. `RuleBasedClassifier` : classifieur local par mots-clés, déterministe,
   sans dépendance réseau ni clé d'API. C'est le backend par défaut du
   projet afin que toute personne qui clone le dépôt puisse exécuter la
   démonstration immédiatement, sans compte ni coût d'API.
2. `LLMClassifier` : backend optionnel s'appuyant sur un modèle de chat
   compatible `langchain_core.language_models.BaseChatModel` (OpenAI,
   Anthropic, Mistral, modèle local via Ollama, etc.), activé uniquement
   si un modèle est explicitement injecté par l'appelant.

Ce choix est documenté dans le README (section "Choix techniques") :
il permet de démontrer l'architecture de l'agent (LangGraph, état,
validation humaine) de façon reproductible, tout en gardant la porte
ouverte à un vrai LLM en production.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.synthetic_data import Category

_KEYWORDS: dict[Category, list[str]] = {
    "devis": ["devis", "prix", "coûterait", "coute", "tarif"],
    "reclamation": ["rayure", "satisfait", "réclamation", "finition", "endommagé"],
    "support_technique": ["assembler", "notice", "manquant", "pied", "panne"],
    "facturation": ["facture", "prélevé", "montant", "paiement", "remboursement"],
    "spam": ["gagné", "bon d'achat", "cliquez", "promotion exceptionnelle"],
}

_SUGGESTED_RESPONSES: dict[Category, str] = {
    "devis": (
        "Bonjour {prenom}, merci pour votre intérêt. Je vous propose un "
        "devis sous 48h pour le produit demandé. Pouvez-vous préciser les "
        "dimensions souhaitées ?"
    ),
    "reclamation": (
        "Bonjour {prenom}, nous sommes désolés pour ce désagrément. Un geste "
        "commercial ou un échange va être étudié par notre équipe sous 24h."
    ),
    "support_technique": (
        "Bonjour {prenom}, merci de nous signaler ce problème. Nous vous "
        "envoyons la notice complète / la pièce manquante dans les meilleurs "
        "délais."
    ),
    "facturation": (
        "Bonjour {prenom}, nous vérifions votre dossier de facturation et "
        "revenons vers vous sous 24h avec le document ou la correction "
        "nécessaire."
    ),
    "spam": "Ticket identifié comme indésirable, aucune réponse ne sera envoyée.",
}


@dataclass
class Classification:
    category: Category
    confidence: float
    suggested_response: str


class TicketClassifier(Protocol):
    def classify(self, text: str, sender_name: str) -> Classification: ...


class RuleBasedClassifier:
    """Classifieur déterministe par mots-clés (backend par défaut, sans API)."""

    def classify(self, text: str, sender_name: str) -> Classification:
        text_lower = text.lower()
        scores: dict[Category, int] = {cat: 0 for cat in _KEYWORDS}
        for category, keywords in _KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    scores[category] += 1

        best_category: Category = max(scores, key=lambda c: scores[c])
        total_hits = sum(scores.values())
        # Confiance = proportion des indices trouvés attribuable à la
        # catégorie gagnante ; 0.34 (1/len(categories)) si aucun indice.
        confidence = (
            scores[best_category] / total_hits if total_hits > 0 else 1 / len(_KEYWORDS)
        )
        response = _SUGGESTED_RESPONSES[best_category].format(prenom=sender_name)
        return Classification(
            category=best_category, confidence=round(confidence, 2), suggested_response=response
        )


class LLMClassifier:
    """Backend optionnel basé sur un vrai modèle de chat (LangChain).

    `chat_model` doit implémenter l'interface `BaseChatModel` de
    `langchain_core`. Non utilisé par défaut : voir README pour
    l'activer avec vos propres identifiants d'API.
    """

    def __init__(self, chat_model) -> None:  # chat_model: BaseChatModel
        self.chat_model = chat_model

    def classify(self, text: str, sender_name: str) -> Classification:
        from langchain_core.messages import HumanMessage, SystemMessage

        categories = ", ".join(_KEYWORDS.keys())
        system = SystemMessage(
            content=(
                "Tu classes un ticket client dans une des catégories suivantes : "
                f"{categories}. Réponds uniquement par la catégorie."
            )
        )
        human = HumanMessage(content=text)
        result = self.chat_model.invoke([system, human])
        category = str(result.content).strip().lower()
        if category not in _KEYWORDS:
            category = "support_technique"
        response = _SUGGESTED_RESPONSES[category].format(prenom=sender_name)
        return Classification(category=category, confidence=0.9, suggested_response=response)
