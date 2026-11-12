from abc import ABC, abstractmethod

from app.schemas.retrieval import AssistantRequest, AssistantResponse, GroundingStatus, RetrievalResult

SAFETY_RULES = [
    "Answer only from retrieved evidence when operating in evidence-grounded mode.",
    "Cite the available source IDs for factual research claims.",
    "Distinguish documented findings from interpretations.",
    "State when evidence is insufficient.",
    "Never invent citations or measurements.",
    "Never turn a potential application into a proven NASA result.",
    "Never provide unsupported emergency instructions.",
    "Never claim that an experiment proves universal fire safety.",
    "Clearly disclose when information is unavailable.",
    "Avoid making up answers when retrieval returns no relevant evidence.",
]


class ResearchAssistant(ABC):
    @abstractmethod
    def answer(self, request: AssistantRequest, evidence: list[RetrievalResult]) -> AssistantResponse:
        raise NotImplementedError


class NoProviderAssistant(ResearchAssistant):
    def answer(self, request: AssistantRequest, evidence: list[RetrievalResult]) -> AssistantResponse:
        source_ids = sorted({source_id for result in evidence for source_id in (result.source_ids or [])})
        if not evidence:
            return AssistantResponse(
                answer="No relevant evidence was found for this question, so no answer can be given from evidence.",
                evidence=[],
                source_ids=[],
                grounding_status=GroundingStatus.NO_EVIDENCE,
                warnings=["No relevant evidence was retrieved.", "No AI provider is configured; no answer was generated."],
                limitations=["No external model call was made.", "An answer requires retrieved evidence and a configured provider."],
            )
        return AssistantResponse(
            answer="No AI provider is configured, so no answer was generated. The retrieved evidence is listed below; review the source references directly.",
            evidence=list(evidence),
            source_ids=source_ids,
            grounding_status=GroundingStatus.INSUFFICIENT_EVIDENCE,
            warnings=["No AI provider is configured; no answer was generated.", "The evidence below is not an answer by itself."],
            limitations=["No external model call was made.", "An answer requires a configured provider and retrieved evidence."],
        )
