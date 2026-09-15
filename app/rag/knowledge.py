class KnowledgeBase:
    """Small deterministic RAG substitute; can later be replaced by embeddings."""

    documents = {
        "project_rules": "ENG supports Bug, Task, and Story. Use uppercase priority values.",
        "priorities": "LOW is routine, MEDIUM is normal, HIGH impacts delivery, CRITICAL impacts production.",
        "workflow": "OPEN can move to IN_PROGRESS or CLOSED. IN_PROGRESS can move to RESOLVED. RESOLVED can move to CLOSED.",
        "ownership": "backend-team owns APIs and data services; frontend-team owns web clients; demo-user is the requester.",
        "sop": "Production incidents should include impact, timeline, mitigation, and follow-up labels.",
    }

    def retrieve(self, query: str, limit: int = 3) -> list[str]:
        words = set(query.lower().split())
        scored = sorted(((len(words & set(text.lower().split())), text) for text in self.documents.values()), reverse=True)
        return [text for score, text in scored[:limit] if score or not query]
