"""Typed model-facing schemas for bounded, allowlisted agent decisions."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Intent(str, Enum):
    PRODUCT = "product"
    STYLE_ADVICE = "style_advice"
    ORDER_SUPPORT = "personal_support"
    EXTERNAL = "external_info"
    AMBIGUOUS = "ambiguous"
    GREETING = "greeting"


class IntentClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: Intent
    standalone_question: str = Field(default="", max_length=4000)
    human_requested: bool = False
    human_recommended: bool = False


class EvidenceAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rag_sufficient: bool
    needs_human: bool
    source_ids: list[str] = Field(max_length=8)


class AnswerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1, max_length=4000)
    source_ids: list[str] = Field(max_length=8)


class GeneralAnswerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1, max_length=4000)
