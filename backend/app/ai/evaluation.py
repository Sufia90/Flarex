from app.schemas.retrieval import EvaluationRecord, GroundingStatus


def evaluate_retrieval(record: EvaluationRecord) -> EvaluationRecord:
    expected = set(record.expected_evidence_ids or [])
    retrieved = set(record.retrieved_evidence_ids or [])
    found = expected & retrieved
    missing = sorted(expected - retrieved)
    if expected:
        coverage = len(found) / len(expected)
    else:
        coverage = None
    if not retrieved:
        status = GroundingStatus.NO_EVIDENCE
    elif not missing:
        status = GroundingStatus.GROUNDED
    else:
        status = GroundingStatus.INSUFFICIENT_EVIDENCE
    return record.model_copy(update={
        "source_coverage": coverage,
        "grounding_status": status,
        "missing_evidence": missing,
    })
