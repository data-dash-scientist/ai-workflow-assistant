"""Interface Streamlit — AI Workflow Assistant (projet personnel indépendant).

Démonstration d'un agent IA de triage de tickets clients pour une
entreprise fictive ("Atelier Nimba"), construit avec LangGraph. L'agent
propose une classification et une réponse, mais n'exécute jamais rien
sans validation humaine explicite (approuver / modifier / rejeter).

Lancer avec : streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from src.synthetic_data import generate_tickets
from src.workflow import build_workflow, resume_with_human_decision, run_ticket_until_review

st.set_page_config(page_title="AI Workflow Assistant — démo", page_icon="🤖", layout="centered")

PRIMARY = "#855469"
ACCENT = "#BD8C9F"

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: #161115; color: #F1E8EC; }}
    h1, h2, h3 {{ color: {ACCENT}; }}
    .stButton>button {{ background-color: {PRIMARY}; color: white; border: none; }}

    /* Labels des widgets (selectbox, text_area...) lisibles sur fond sombre */
    [data-testid="stWidgetLabel"] p, label, .stMarkdown, .stMarkdown p {{ color: #F1E8EC !important; }}

    /* Champs de texte : fond clair + texte foncé bien contrasté */
    .stTextArea textarea {{
        background-color: #FAF7F8 !important;
        color: #161115 !important;
        -webkit-text-fill-color: #161115 !important;
        opacity: 1 !important;
    }}
    .stTextArea textarea:disabled {{
        background-color: #E9E1E5 !important;
        color: #161115 !important;
        -webkit-text-fill-color: #161115 !important;
        opacity: 1 !important;
    }}

    /* Selectbox : texte sélectionné et liste déroulante */
    div[data-baseweb="select"] > div {{ background-color: #FAF7F8; color: #161115; }}
    div[data-baseweb="select"] span, div[data-baseweb="select"] input {{ color: #161115 !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🤖 AI Workflow Assistant")

if "app" not in st.session_state:
    st.session_state.app = build_workflow()
if "tickets" not in st.session_state:
    st.session_state.tickets = generate_tickets(n=12, seed=42)
if "reviewed" not in st.session_state:
    st.session_state.reviewed = {}

ticket_labels = [f"{t.ticket_id} — {t.sender_name}" for t in st.session_state.tickets]
choice = st.selectbox("Choisir un ticket à traiter", ticket_labels)
ticket = st.session_state.tickets[ticket_labels.index(choice)]

st.subheader("Ticket reçu")
st.text_area("Contenu du ticket", ticket.text, height=100, disabled=True)

thread_id = ticket.ticket_id

if st.button("Lancer l'agent sur ce ticket"):
    state = run_ticket_until_review(st.session_state.app, ticket, thread_id=thread_id)
    st.session_state.reviewed[thread_id] = {
        "interrupt": state["__interrupt__"][0].value,
        "final_state": None,
    }

if thread_id in st.session_state.reviewed and st.session_state.reviewed[thread_id]["final_state"] is None:
    payload = st.session_state.reviewed[thread_id]["interrupt"]
    st.subheader("Proposition de l'agent")
    st.write(f"**Catégorie détectée :** {payload['category']} (confiance {payload['confidence']})")
    edited_response = st.text_area("Réponse proposée (modifiable)", payload["proposed_response"], height=120)

    col1, col2, col3 = st.columns(3)
    decision = None
    if col1.button("✅ Approuver"):
        decision = "approve"
    if col2.button("✏️ Approuver avec modification"):
        decision = "edit"
    if col3.button("❌ Rejeter"):
        decision = "reject"

    if decision:
        final_state = resume_with_human_decision(
            st.session_state.app,
            thread_id=thread_id,
            decision=decision,
            final_response=edited_response if decision == "edit" else None,
        )
        st.session_state.reviewed[thread_id]["final_state"] = final_state

if thread_id in st.session_state.reviewed and st.session_state.reviewed[thread_id]["final_state"]:
    final_state = st.session_state.reviewed[thread_id]["final_state"]
    st.subheader("Résultat")
    if final_state["executed"]:
        st.success(final_state["execution_log"])
        st.write(f"**Réponse envoyée :** {final_state['final_response']}")
    else:
        st.warning(final_state["execution_log"])
