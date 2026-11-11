import pytest
from pydantic import ValidationError
from models import CandidateMetadata, EvidenceData, EvidenceFields, EvidenceItem

def test_valid_candidate_metadata():
    data = CandidateMetadata(
        title="Valid Research Title",
        subject_keywords=["Keyword1", "Keyword2"],
        abstract="Valid abstract text here."
    )
    assert data.title == "Valid Research Title"
    assert len(data.subject_keywords) == 2

def test_empty_title_fails():
    with pytest.raises(ValidationError):
        CandidateMetadata(
            title="   ",
            subject_keywords=["Keyword1"],
            abstract="Some abstract"
        )

def test_empty_keywords_fails():
    with pytest.raises(ValidationError):
        CandidateMetadata(
            title="Some title",
            subject_keywords=[],
            abstract="Some abstract"
        )

def test_evidence_structure_v1():
    evidence = EvidenceData(
        schema_version=1,
        fields=EvidenceFields(
            title=[EvidenceItem(page_number=1, source_text="Research on Deep Learning")],
            subject_keywords=[EvidenceItem(page_number=2, source_text="Keywords: AI, ML")],
            abstract=[EvidenceItem(page_number=3, source_text="Abstract summary")]
        )
    )
    assert evidence.schema_version == 1
    assert len(evidence.fields.title) == 1
    assert evidence.fields.title[0].page_number == 1

