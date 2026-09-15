from typing import Literal

from pydantic import BaseModel, Field, field_validator

Priority = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
Status = Literal["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]
IssueType = Literal["Bug", "Task", "Story"]


class CreateIssueRequest(BaseModel):
    project_key: str = Field(default="ENG", min_length=2, max_length=16, pattern=r"^[A-Z][A-Z0-9_-]+$")
    issue_type: IssueType = "Task"
    summary: str = Field(min_length=3, max_length=255)
    description: str = Field(default="", max_length=10000)
    priority: Priority = "MEDIUM"
    labels: list[str] = Field(default_factory=list, max_length=10)
    assignee: str | None = Field(default=None, max_length=64)

    @field_validator("labels")
    @classmethod
    def clean_labels(cls, value: list[str]) -> list[str]:
        return [label.strip().lower() for label in value if label.strip()]


class UpdateIssueRequest(BaseModel):
    summary: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=10000)
    priority: Priority | None = None
    labels: list[str] | None = None


class CommentRequest(BaseModel):
    body: str = Field(min_length=1, max_length=10000)


class AssignRequest(BaseModel):
    assignee: str = Field(min_length=2, max_length=64)


class TransitionRequest(BaseModel):
    status: Status


class SearchRequest(BaseModel):
    query: str = Field(default="", max_length=255)
    project_key: str | None = None
    status: Status | None = None
    priority: Priority | None = None
    assignee: str | None = None
