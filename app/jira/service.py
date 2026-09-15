from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Comment, Issue, Project, User
from app.jira.schemas import CreateIssueRequest, SearchRequest, UpdateIssueRequest


class JiraService:
    def __init__(self, db: Session):
        self.db = db

    def seed(self) -> None:
        if self.db.get(Project, "ENG"):
            return
        self.db.add(Project(key="ENG", name="Engineering", description="Product engineering work", issue_types=["Bug", "Task", "Story"]))
        self.db.add_all([User(username="demo-user", display_name="Demo User", team="platform"), User(username="backend-team", display_name="Backend Team", team="backend"), User(username="frontend-team", display_name="Frontend Team", team="frontend")])
        self.db.commit()

    def _key(self, project_key: str) -> str:
        count = self.db.scalar(select(Issue).where(Issue.project_key == project_key).order_by(Issue.id.desc()).limit(1))
        number = (count.id + 1) if count else 1
        return f"{project_key}-{number}"

    @staticmethod
    def serialize(issue: Issue) -> dict:
        return {"key": issue.key, "project_key": issue.project_key, "issue_type": issue.issue_type, "summary": issue.summary, "description": issue.description, "priority": issue.priority, "status": issue.status, "labels": issue.labels or [], "assignee": issue.assignee, "reporter": issue.reporter, "comments": [{"author": c.author, "body": c.body} for c in issue.comments]}

    def create_issue(self, request: CreateIssueRequest, reporter: str = "demo-user") -> dict:
        if not self.db.get(Project, request.project_key):
            raise ValueError(f"Unknown project: {request.project_key}")
        if request.assignee and not self.db.get(User, request.assignee):
            raise ValueError(f"Unknown assignee: {request.assignee}")
        issue = Issue(key=self._key(request.project_key), reporter=reporter, **request.model_dump())
        self.db.add(issue)
        self.db.commit()
        self.db.refresh(issue)
        return self.serialize(issue)

    def get_issue(self, key: str) -> dict:
        issue = self.db.scalar(select(Issue).where(Issue.key == key.upper()))
        if not issue:
            raise LookupError(f"Issue not found: {key}")
        return self.serialize(issue)

    def search_issues(self, request: SearchRequest) -> list[dict]:
        query = select(Issue)
        if request.project_key: query = query.where(Issue.project_key == request.project_key.upper())
        if request.status: query = query.where(Issue.status == request.status)
        if request.priority: query = query.where(Issue.priority == request.priority)
        if request.assignee: query = query.where(Issue.assignee == request.assignee)
        if request.query: query = query.where(or_(Issue.summary.ilike(f"%{request.query}%"), Issue.description.ilike(f"%{request.query}%")))
        return [self.serialize(issue) for issue in self.db.scalars(query.order_by(Issue.id.desc())).all()]

    def update_issue(self, key: str, request: UpdateIssueRequest) -> dict:
        issue = self._issue(key)
        for field, value in request.model_dump(exclude_unset=True).items(): setattr(issue, field, value)
        self.db.commit()
        return self.serialize(issue)

    def add_comment(self, key: str, body: str, author: str = "demo-user") -> dict:
        issue = self._issue(key)
        self.db.add(Comment(issue_id=issue.id, body=body, author=author))
        self.db.commit()
        return self.serialize(issue)

    def assign_issue(self, key: str, assignee: str) -> dict:
        issue = self._issue(key)
        if not self.db.get(User, assignee): raise ValueError(f"Unknown assignee: {assignee}")
        issue.assignee = assignee
        self.db.commit()
        return self.serialize(issue)

    def transition_issue(self, key: str, status: str) -> dict:
        issue = self._issue(key)
        allowed = {"OPEN": {"IN_PROGRESS", "CLOSED"}, "IN_PROGRESS": {"OPEN", "RESOLVED"}, "RESOLVED": {"CLOSED", "IN_PROGRESS"}, "CLOSED": set()}
        if status not in allowed[issue.status]: raise ValueError(f"Invalid transition {issue.status} -> {status}")
        issue.status = status
        self.db.commit()
        return self.serialize(issue)

    def project_info(self, key: str) -> dict:
        project = self.db.get(Project, key.upper())
        if not project: raise LookupError(f"Project not found: {key}")
        return {"key": project.key, "name": project.name, "description": project.description, "issue_types": project.issue_types}

    def _issue(self, key: str) -> Issue:
        issue = self.db.scalar(select(Issue).where(Issue.key == key.upper()))
        if not issue: raise LookupError(f"Issue not found: {key}")
        return issue
