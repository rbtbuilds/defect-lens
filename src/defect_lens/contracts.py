from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Decision = Literal["pass", "review", "fail"]
Method = Literal["difference", "resnet18_patch"]
DataMode = Literal["procedural", "owned_capture"]
JobStatus = Literal["queued", "running", "succeeded", "failed"]
ModelStatus = Literal["unprepared", "loading", "ready", "busy", "degraded"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class ReadyState(Contract):
    status: ModelStatus = "unprepared"
    model_revision: str | None = None
    method: Method | None = None
    data_mode: DataMode | None = None
    worker_alive: bool = False
    reason: str | None = "No prepared model selected"


class JobError(Contract):
    code: str
    message: str
    retryable: bool = False
    request_id: str = ""
    details: dict[str, str | int | float | None] = Field(default_factory=dict)
