from app.jira.schemas import CreateIssueRequest, SearchRequest, UpdateIssueRequest
from app.jira.service import JiraService


class JiraTools:
    """The only database-facing surface available to the agent."""

    def __init__(self, service: JiraService):
        self.service = service

    def create_issue(self, arguments: CreateIssueRequest) -> dict: return self.service.create_issue(arguments)
    def get_issue(self, key: str) -> dict: return self.service.get_issue(key)
    def search_issues(self, arguments: SearchRequest) -> list[dict]: return self.service.search_issues(arguments)
    def update_issue(self, key: str, arguments: UpdateIssueRequest) -> dict: return self.service.update_issue(key, arguments)
    def add_comment(self, key: str, body: str) -> dict: return self.service.add_comment(key, body)
    def assign_issue(self, key: str, assignee: str) -> dict: return self.service.assign_issue(key, assignee)
    def transition_issue(self, key: str, status: str) -> dict: return self.service.transition_issue(key, status)
    def get_project_info(self, key: str) -> dict: return self.service.project_info(key)
