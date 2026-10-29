from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Priority = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
Status = Literal["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]
IssueType = Literal["Bug", "Task", "Story"]
Label = Annotated[str, Field(max_length=64)]


class RequestModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class CreateIssueRequest(RequestModel):
    project_key: str = Field(default="ENG", min_length=2, max_length=16, pattern=r"^[A-Z][A-Z0-9_-]+$")
    issue_type: IssueType = "Task"
    summary: str = Field(min_length=3, max_length=255)
    description: str = Field(default="", max_length=10000)
    priority: Priority = "MEDIUM"
    labels: list[Label] = Field(default_factory=list, max_length=10)
    assignee: str | None = Field(default=None, min_length=2, max_length=64)

    @field_validator("labels")
    @classmethod
    def clean_labels(cls, value: list[str]) -> list[str]:
        return [label.strip().lower() for label in value if label.strip()]


class UpdateIssueRequest(RequestModel):
    summary: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=10000)
    priority: Priority | None = None
    labels: list[Label] | None = Field(default=None, max_length=10)

    @field_validator("labels")
    @classmethod
    def clean_labels(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return [label.strip().lower() for label in value if label.strip()]


class CommentRequest(RequestModel):
    body: str = Field(min_length=1, max_length=10000)


class AssignRequest(RequestModel):
    assignee: str = Field(min_length=2, max_length=64)


class TransitionRequest(RequestModel):
    status: Status


class SearchRequest(RequestModel):
    query: str = Field(default="", max_length=255)
    project_key: str | None = Field(default=None, min_length=2, max_length=16, pattern=r"^[A-Z][A-Z0-9_-]+$")
    status: Status | None = None
    priority: Priority | None = None
    assignee: str | None = Field(default=None, min_length=2, max_length=64)
