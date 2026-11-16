"""Graphe LangGraph de l'AI Workflow Assistant.

Architecture (voir assets/architecture.md pour le schéma complet) :

    [classify] --> [prepare_action] --> [human_review] --> [execute] --> END
                                              |
                                   (interrupt: approuver / modifier / rejeter)

- `classify`        : classe le ticket et propose une réponse (src.classifier)
- `prepare_action`  : prépare l'action à exécuter selon la catégorie
- `human_review`    : point d'arrêt obligatoire (interrupt) — AUCUNE action
                       n'est exécutée sans validation humaine explicite
- `execute`         : simule l'exécution de l'action validée (ou annulée)

Ce graphe est un projet personnel indépendant, construit de zéro avec une
architecture et un jeu de données qui me sont propres. Il s'inspire d'une
problématique générale (triage de tickets avec supervision humaine) sans
reproduire le système ni les données de l'employeur pour lequel je
développe un agent similaire en entreprise.
"""
from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import Command, interrupt

from src.classifier import Classification, RuleBasedClassifier, TicketClassifier
from src.synthetic_data import Category, Ticket

HumanDecision = Literal["approve", "edit", "reject"]


class WorkflowState(TypedDict, total=False):
    ticket_id: str
    sender_name: str
    text: str
    category: Category
    confidence: float
    suggested_response: str
    final_response: str
    human_decision: HumanDecision
    executed: bool
    execution_log: str


def make_classify_node(classifier: TicketClassifier):
    def classify(state: WorkflowState) -> WorkflowState:
        result: Classification = classifier.classify(state["text"], state["sender_name"])
        return {
            "category": result.category,
            "confidence": result.confidence,
            "suggested_response": result.suggested_response,
        }

    return classify


def prepare_action(state: WorkflowState) -> WorkflowState:
    # Étape intermédiaire explicite : permet d'ajouter facilement une
    # logique métier (ex. enrichissement, priorisation) sans toucher au
    # nœud de classification ni au nœud de validation humaine.
    return {"final_response": state["suggested_response"]}


def human_review(state: WorkflowState) -> WorkflowState:
    """Point de validation humaine obligatoire.

    Le graphe s'arrête ici (`interrupt`) et attend une décision externe
    (approve / edit / reject), fournie via `Command(resume=...)`.
    Aucune réponse n'est jamais envoyée automatiquement sans ce passage.
    """
    decision = interrupt(
        {
            "ticket_id": state["ticket_id"],
            "category": state["category"],
            "confidence": state["confidence"],
            "proposed_response": state["final_response"],
            "instructions": "Répondre avec {'decision': 'approve'|'edit'|'reject', 'final_response': str (optionnel)}",
        }
    )
    decision_type: HumanDecision = decision.get("decision", "reject")
    final_response = decision.get("final_response") or state["final_response"]
    return {"human_decision": decision_type, "final_response": final_response}


def execute(state: WorkflowState) -> WorkflowState:
    if state.get("human_decision") == "approve" or state.get("human_decision") == "edit":
        return {
            "executed": True,
            "execution_log": f"Réponse envoyée pour {state['ticket_id']} (catégorie: {state['category']}).",
        }
    return {
        "executed": False,
        "execution_log": f"Action annulée par l'humain pour {state['ticket_id']}.",
    }


def build_workflow(classifier: TicketClassifier | None = None):
    """Construit et compile le graphe LangGraph avec checkpointer mémoire."""
    classifier = classifier or RuleBasedClassifier()

    graph = StateGraph(WorkflowState)
    graph.add_node("classify", make_classify_node(classifier))
    graph.add_node("prepare_action", prepare_action)
    graph.add_node("human_review", human_review)
    graph.add_node("execute", execute)

    graph.set_entry_point("classify")
    graph.add_edge("classify", "prepare_action")
    graph.add_edge("prepare_action", "human_review")
    graph.add_edge("human_review", "execute")
    graph.add_edge("execute", END)

    return graph.compile(checkpointer=MemorySaver())


def run_ticket_until_review(app, ticket: Ticket, thread_id: str) -> dict:
    """Exécute le graphe jusqu'au point d'arrêt humain et renvoie l'état."""
    config = {"configurable": {"thread_id": thread_id}}
    initial_state: WorkflowState = {
        "ticket_id": ticket.ticket_id,
        "sender_name": ticket.sender_name,
        "text": ticket.text,
    }
    return app.invoke(initial_state, config=config)


def resume_with_human_decision(
    app, thread_id: str, decision: HumanDecision, final_response: str | None = None
) -> dict:
    """Reprend le graphe après la décision humaine (approve/edit/reject)."""
    config = {"configurable": {"thread_id": thread_id}}
    payload = {"decision": decision}
    if final_response is not None:
        payload["final_response"] = final_response
    return app.invoke(Command(resume=payload), config=config)
