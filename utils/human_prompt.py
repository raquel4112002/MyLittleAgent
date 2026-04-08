"""Human-in-the-loop prompt service with pluggable channels."""

import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol

from entity.messages import MessageBlock, MessageBlockType, MessageContent
from utils.log_manager import LogManager


def _get_session_manager():
    from server.state import get_session_manager
    return get_session_manager()


def _get_human_response_broker():
    from server.state import get_human_response_broker
    return get_human_response_broker()


@dataclass
class PromptResult:
    text: str
    blocks: Optional[List[MessageBlock]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_message_content(self) -> MessageContent:
        return self.blocks if self.blocks is not None else self.text


class PromptChannel(Protocol):
    def request(
        self,
        *,
        node_id: str,
        task: str,
        inputs: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PromptResult:
        ...


@dataclass
class CliPromptChannel:
    input_func: Callable[[str], str] = input

    def request(
        self,
        *,
        node_id: str,
        task: str,
        inputs: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PromptResult:
        header = ["===== HUMAN INPUT REQUIRED ====="]
        if inputs:
            header.append("=== Node inputs ===")
            header.append(inputs)
        header.append(f"=== Task for human ({node_id}) ===")
        header.append(task)
        header.append("=== Your response: ===")
        prompt = "\n".join(header) + "\n"
        response = self.input_func(prompt)
        return PromptResult(text=response, blocks=[MessageBlock.text_block(response or "")])


class HumanPromptService:
    def __init__(self, *, log_manager: LogManager, channel: PromptChannel, session_id: Optional[str] = None) -> None:
        self._log_manager = log_manager
        self._channel = channel
        self._session_id = session_id
        self._lock = threading.Lock()

    def request(self, node_id: str, task_description: str, *, inputs: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> PromptResult:
        meta = dict(metadata or {})
        if self._session_id and "session_id" not in meta:
            meta["session_id"] = self._session_id

        if self._session_id:
            session = _get_session_manager().mark_waiting_for_human(
                self._session_id,
                node_id=node_id,
                task_description=task_description,
                inputs=inputs,
            )
            request_id = session.pending_human_request.request_id if session and session.pending_human_request else f"{self._session_id}:{node_id}"
            _get_human_response_broker().register_request(
                self._session_id,
                request_id=request_id,
                node_id=node_id,
                task_description=task_description,
                inputs=inputs,
            )
            with self._lock:
                with self._log_manager.human_timer(node_id):
                    broker_result = _get_human_response_broker().wait_for_response(self._session_id)
            if broker_result is None or broker_result.response_text is None:
                raw_result = PromptResult(text="", blocks=[MessageBlock.text_block("")], metadata={"timeout": True})
            else:
                raw_result = PromptResult(
                    text=broker_result.response_text,
                    blocks=[MessageBlock.text_block(broker_result.response_text)],
                    metadata=broker_result.response_metadata or {},
                )
        else:
            with self._lock:
                with self._log_manager.human_timer(node_id):
                    raw_result = self._channel.request(node_id=node_id, task=task_description, inputs=inputs, metadata=meta)

        prompt_result = self._normalize_result(raw_result)
        sanitized_text = self._sanitize_response(prompt_result.text)
        normalized_blocks = self._normalize_blocks(prompt_result.blocks, sanitized_text)
        combined_metadata = {**prompt_result.metadata, **meta}

        self._log_manager.record_human_interaction(
            node_id,
            inputs,
            sanitized_text,
            details={"task_description": task_description, **combined_metadata},
        )
        if self._session_id:
            _get_session_manager().record_human_message(
                self._session_id,
                node_id=node_id,
                text=sanitized_text,
                metadata=combined_metadata,
            )
            _get_session_manager().mark_running(self._session_id)
        return PromptResult(text=sanitized_text, blocks=normalized_blocks, metadata=combined_metadata)

    @staticmethod
    def _sanitize_response(response: Any) -> str:
        text = response if isinstance(response, str) else str(response)
        return text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")

    def _normalize_result(self, raw_result: PromptResult | str | Any) -> PromptResult:
        if isinstance(raw_result, PromptResult):
            return raw_result
        text = self._sanitize_response(raw_result)
        return PromptResult(text=text, blocks=[MessageBlock.text_block(text)])

    def _normalize_blocks(self, blocks: Optional[List[MessageBlock]], fallback_text: str) -> List[MessageBlock]:
        if not blocks:
            return [MessageBlock.text_block(fallback_text)]
        normalized: List[MessageBlock] = []
        for block in blocks:
            dup = block.copy()
            if dup.type is MessageBlockType.TEXT and dup.text is not None:
                dup.text = self._sanitize_response(dup.text)
            normalized.append(dup)
        return normalized


def resolve_prompt_channel(workspace_hook: Any) -> PromptChannel | None:
    if workspace_hook is None:
        return None
    getter = getattr(workspace_hook, "get_prompt_channel", None)
    if callable(getter):
        channel = getter()
        if channel is not None:
            return channel
    channel = getattr(workspace_hook, "prompt_channel", None)
    if channel is not None:
        return channel
    return None
