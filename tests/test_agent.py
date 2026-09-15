from app.agents.agent import EngineeringAgent
from app.database.session import SessionLocal
from app.jira.service import JiraService
from app.tools.jira_tools import JiraTools


def agent():
    db = SessionLocal(); service = JiraService(db); service.seed(); return EngineeringAgent(JiraTools(service))


def test_intents():
    subject = agent()
    assert subject.classify_intent("Create a high-priority bug") == "CREATE_ISSUE"
    assert subject.classify_intent("Show my open bugs") == "SEARCH_ISSUES"
    assert subject.classify_intent("Update ENG-1") == "UPDATE_ISSUE"


def test_approval_and_memory():
    subject = agent()
    proposed = subject.chat("Create a high priority bug for API timeout", "conversation-1")
    assert proposed["requires_approval"] is True
    completed = subject.chat("Approve", "conversation-1")
    assert completed["approval_status"] == "approved"
    assert completed["data"]["key"] == "ENG-1"
