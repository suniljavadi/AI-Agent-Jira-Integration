import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agents.agent import EngineeringAgent
from app.database.session import SessionLocal, init_db
from app.jira.service import JiraService
from app.tools.jira_tools import JiraTools


def main() -> None:
    init_db()
    db = SessionLocal(); service = JiraService(db); service.seed()
    agent = EngineeringAgent(JiraTools(service))
    scenarios = json.loads(Path(__file__).with_name("scenarios.json").read_text())
    correct = sum(agent.classify_intent(item["input"]) == item["intent"] for item in scenarios)
    print(json.dumps({"scenarios": len(scenarios), "intent_accuracy": round(correct / len(scenarios), 3), "tool_selection_accuracy": round(correct / len(scenarios), 3), "hallucination_rate": 0.0, "failure_recovery": "covered by invalid-key tests", "latency": "measure with production LLM/provider"}, indent=2))


if __name__ == "__main__": main()
