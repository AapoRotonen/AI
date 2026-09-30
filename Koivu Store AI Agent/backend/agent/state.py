"""
agent/state.py - Agentin tila
"""
from typing import TypedDict, List


class AgentState(TypedDict):
    question: str           # Käyttäjän kysymys
    rag_results: List[str]  # RAG-haun tulokset tuotekatalogista
    web_results: List[str]  # Web-haun tulokset
    answer: str             # Lopullinen vastaus
    path_taken: str         # Mitä polkua käytettiin
    should_escalate: bool   # Pitääkö siirtää ihmiselle
    needs_human: bool       # Vaatiiko pyyntö asiakaskohtaista ihmisen selvitystä
    human_mode: bool        # Onko "ihminen" jo otettu käyttöön
    iteration_count: int    # Iteraatioiden määrä
    rag_was_sufficient: bool # Oliko RAG riittävä
    history: List[dict]      # Keskustelun aiemmat vuorot
