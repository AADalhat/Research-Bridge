# src/repositories/submission_repository.py

class SubmissionRepository:
    def get_by_id(self, db, submission_id: str):
        return (
            db.query(Submission)
            .filter(Submission.id == submission_id)
            .first()
        )

    def create(self, db, submission: Submission):
        db.add(submission)
        db.commit()
        db.refresh(submission)
        return submission