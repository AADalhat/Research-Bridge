# src/services/submission_service.py

class SubmissionService:
    def __init__(self, repository: SubmissionRepository):
        self.repository = repository

    def get_submission(self, db, submission_id: str):
        submission = self.repository.get_by_id(db, submission_id)

        if not submission:
            raise SubmissionNotFoundError(submission_id)

        return submission