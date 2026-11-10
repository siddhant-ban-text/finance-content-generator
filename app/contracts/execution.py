"""Versioned typed invocation boundaries, independent of execution adapters."""
from typing import Generic, Literal, TypeVar
from uuid import UUID
from pydantic import Field, model_validator
from app.contracts.common import ArtifactRef, Nonempty, Sha256, StrictModel, Usage, UtcDatetime

T = TypeVar("T", bound=StrictModel)

class InvocationMetadata(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    run_id: UUID
    story_id: UUID
    invocation_id: UUID
    agent_name: Nonempty
    agent_version: Nonempty
    prompt_id: Nonempty
    prompt_version: Nonempty
    prompt_hash: Sha256
    config_version: Nonempty
    config_hash: Sha256
    created_at: UtcDatetime

class InputEnvelope(InvocationMetadata, Generic[T]):
    input: T
    input_ref: ArtifactRef
    parent_context: str | None = None

class ExecutionError(StrictModel):
    code: Nonempty
    retryable: bool

class OutputEnvelope(InvocationMetadata, Generic[T]):
    status: Literal["OK", "FAILED", "BLOCKED"]
    output: T | None = None
    output_ref: ArtifactRef | None = None
    error: ExecutionError | None = None
    warnings: tuple[str, ...] = ()
    evidence_refs: tuple[ArtifactRef, ...] = ()
    usage: Usage = Field(default_factory=Usage)
    trace_id: str | None = None
    span_id: str | None = None
    observability_status: Literal["HEALTHY", "DEGRADED"] = "DEGRADED"

    @model_validator(mode="after")
    def status_matches_content(self):
        if self.status == "OK":
            if self.output is None or self.output_ref is None or self.error is not None:
                raise ValueError("OK requires output and reference without error")
        elif self.error is None or self.output is not None or self.output_ref is not None:
            raise ValueError("failed/blocked output requires only a typed error")
        return self

def decode_envelope(data: bytes, payload_type: type[T]) -> InputEnvelope[T]:
    return InputEnvelope[payload_type].model_validate_json(data)
