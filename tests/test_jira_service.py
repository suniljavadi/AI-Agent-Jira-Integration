import pytest
from pydantic import ValidationError

from app.database.session import SessionLocal
from app.jira.schemas import CreateIssueRequest, SearchRequest
from app.jira.service import JiraService


def test_create_search_and_transition():
    db = SessionLocal(); service = JiraService(db); service.seed()
    issue = service.create_issue(CreateIssueRequest(issue_type="Bug", summary="Payment API timeout", priority="HIGH"))
    assert issue["key"] == "ENG-1"
    assert service.search_issues(SearchRequest(priority="HIGH"))[0]["key"] == "ENG-1"
    assert service.transition_issue("ENG-1", "IN_PROGRESS")["status"] == "IN_PROGRESS"
    db.close()


def test_invalid_schema_rejected():
    with pytest.raises(ValidationError): CreateIssueRequest(summary="x", priority="URGENT")


def test_unknown_project_rejected():
    db = SessionLocal(); service = JiraService(db); service.seed()
    with pytest.raises(ValueError): service.create_issue(CreateIssueRequest(project_key="NOPE", summary="Bad project"))
    db.close()
