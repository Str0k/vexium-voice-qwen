"""Public request contracts shared with the generated OpenAPI documentation."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

MessageText = Annotated[
    str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=2000)
]


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: MessageText


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vertical: Literal["dental", "restaurant"] = "dental"
    messages: list[ChatMessage] = Field(min_length=1, max_length=24)


class SpeechRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: MessageText
    language: Literal["es", "en", "auto"] | None = None
