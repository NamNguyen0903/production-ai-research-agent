from pydantic import BaseModel, Field


class SynthesisResult(BaseModel):
    answer: str = Field(min_length=1)

    used_source_ids: list[str] = Field(default_factory=list)
