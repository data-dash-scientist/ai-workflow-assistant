from src.synthetic_data import Ticket
from src.workflow import build_workflow, resume_with_human_decision, run_ticket_until_review


def _ticket(category="devis", text="Quel est le prix d'un devis pour une étagère ?"):
    return Ticket(
        ticket_id="TCK-TEST-0001",
        sender_name="Awa",
        text=text,
        true_category=category,
    )


def test_workflow_stops_at_human_review():
    app = build_workflow()
    ticket = _ticket()
    state = run_ticket_until_review(app, ticket, thread_id="thread-1")
    assert "__interrupt__" in state
    interrupt_payload = state["__interrupt__"][0].value
    assert interrupt_payload["ticket_id"] == ticket.ticket_id
    assert interrupt_payload["category"] == "devis"


def test_workflow_approve_executes_action():
    app = build_workflow()
    ticket = _ticket()
    run_ticket_until_review(app, ticket, thread_id="thread-2")
    final_state = resume_with_human_decision(app, thread_id="thread-2", decision="approve")
    assert final_state["executed"] is True
    assert ticket.ticket_id in final_state["execution_log"]


def test_workflow_reject_does_not_execute():
    app = build_workflow()
    ticket = _ticket()
    run_ticket_until_review(app, ticket, thread_id="thread-3")
    final_state = resume_with_human_decision(app, thread_id="thread-3", decision="reject")
    assert final_state["executed"] is False


def test_workflow_edit_overrides_response():
    app = build_workflow()
    ticket = _ticket()
    run_ticket_until_review(app, ticket, thread_id="thread-4")
    final_state = resume_with_human_decision(
        app, thread_id="thread-4", decision="edit", final_response="Réponse corrigée à la main."
    )
    assert final_state["executed"] is True
    assert final_state["final_response"] == "Réponse corrigée à la main."


def test_two_independent_threads_do_not_interfere():
    app = build_workflow()
    t1 = _ticket(category="devis", text="Quel est le prix d'un devis pour un banc ?")
    t2 = _ticket(category="spam", text="Vous avez gagné un bon d'achat, cliquez ici")
    t2.ticket_id = "TCK-TEST-0002"

    run_ticket_until_review(app, t1, thread_id="thread-a")
    run_ticket_until_review(app, t2, thread_id="thread-b")

    final_a = resume_with_human_decision(app, thread_id="thread-a", decision="approve")
    final_b = resume_with_human_decision(app, thread_id="thread-b", decision="reject")

    assert final_a["executed"] is True
    assert final_b["executed"] is False
