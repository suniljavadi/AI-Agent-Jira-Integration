import pytest
from pydantic import ValidationError

from app.jira.schemas import (
    AssignRequest,
    CommentRequest,
    CreateIssueRequest,
    SearchRequest,
    UpdateIssueRequest,
)


def test_request_strings_are_trimmed_and_labels_normalized():
    request = CreateIssueRequest(
        summary="  Investigate issue  ",
        assignee="  backend-team ",
        labels=[" Needs Review ", " ", "URGENT"],
    )

    assert request.summary == "Investigate issue"
    assert request.assignee == "backend-team"
    assert request.labels == ["needs review", "urgent"]


@pytest.mark.parametrize(
    "case_factory",
    [
        lambda: UpdateIssueRequest(labels=["x" * 65]),
        lambda: UpdateIssueRequest(labels=["label"] * 11),
        lambda: SearchRequest(query="x" * 256),
        lambda: SearchRequest(project_key="invalid key"),
        lambda: SearchRequest(assignee="x" * 65),
        lambda: AssignRequest(assignee=" "),
        lambda: CommentRequest(body=" "),
    ],
)
def test_request_limits_and_blank_values_are_validated(case_factory):
    with pytest.raises(ValidationError):
        case_factory()


def test_search_accepts_empty_query_and_project_key_case_is_explicit():
    assert SearchRequest(query="  ").query == ""
    with pytest.raises(ValidationError):
        SearchRequest(project_key="eng")
