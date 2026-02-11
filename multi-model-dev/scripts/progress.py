#!/usr/bin/env python3
"""
Progress Event System

Defines progress events for real-time orchestrator updates.
Includes OpenClaw/Telegram integration wrapper.

Usage:
    # With custom callback
    async def my_handler(event):
        print(f"{event.emoji} {event.message}")
    
    result = await orch.run(task, on_progress=my_handler)
    
    # With OpenClaw integration (sends to active channel)
    from progress import OpenClawProgress
    
    progress = OpenClawProgress()
    result = await orch.run(task, on_progress=progress.emit)
"""

import asyncio
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional, Awaitable, Union


# =============================================================================
# EVENT TYPES
# =============================================================================

class ProgressEvent(Enum):
    """Types of progress events."""
    # Task analysis
    TASK_RECEIVED = "task_received"
    TASK_ANALYZED = "task_analyzed"
    
    # Model execution
    MODELS_SELECTED = "models_selected"
    MODEL_STARTING = "model_starting"
    MODEL_COMPLETED = "model_completed"
    MODEL_FAILED = "model_failed"
    
    # Validation
    VALIDATION_STARTING = "validation_starting"
    VALIDATION_COMPLETED = "validation_completed"
    
    # Merging
    MERGE_STARTING = "merge_starting"
    MERGE_COMPLETED = "merge_completed"
    
    # Final
    ORCHESTRATION_COMPLETED = "orchestration_completed"
    ORCHESTRATION_FAILED = "orchestration_failed"


# Event emoji mapping
EVENT_EMOJIS = {
    ProgressEvent.TASK_RECEIVED: "📋",
    ProgressEvent.TASK_ANALYZED: "🎯",
    ProgressEvent.MODELS_SELECTED: "🤖",
    ProgressEvent.MODEL_STARTING: "🚀",
    ProgressEvent.MODEL_COMPLETED: "✅",
    ProgressEvent.MODEL_FAILED: "❌",
    ProgressEvent.VALIDATION_STARTING: "🔍",
    ProgressEvent.VALIDATION_COMPLETED: "✅",
    ProgressEvent.MERGE_STARTING: "🔀",
    ProgressEvent.MERGE_COMPLETED: "📦",
    ProgressEvent.ORCHESTRATION_COMPLETED: "🎉",
    ProgressEvent.ORCHESTRATION_FAILED: "💥",
}


@dataclass
class Progress:
    """A progress event with context."""
    event: ProgressEvent
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def emoji(self) -> str:
        return EVENT_EMOJIS.get(self.event, "📌")
    
    def format(self, verbose: bool = False) -> str:
        """Format for display."""
        base = f"{self.emoji} {self.message}"
        if verbose and self.data:
            details = ", ".join(f"{k}={v}" for k, v in self.data.items())
            base += f" ({details})"
        return base
    
    def to_dict(self) -> dict:
        return {
            "event": self.event.value,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }


# Type alias for progress callbacks
ProgressCallback = Callable[[Progress], Union[None, Awaitable[None]]]


# =============================================================================
# PROGRESS HANDLERS
# =============================================================================

class ProgressHandler:
    """Base class for progress handlers."""
    
    async def emit(self, progress: Progress) -> None:
        """Handle a progress event."""
        raise NotImplementedError


class ConsoleProgress(ProgressHandler):
    """Print progress to console."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    async def emit(self, progress: Progress) -> None:
        print(progress.format(self.verbose))


class CollectingProgress(ProgressHandler):
    """Collect all progress events for later inspection."""
    
    def __init__(self):
        self.events: list[Progress] = []
    
    async def emit(self, progress: Progress) -> None:
        self.events.append(progress)
    
    def summary(self) -> str:
        return "\n".join(p.format() for p in self.events)


class OpenClawProgress(ProgressHandler):
    """
    Send progress events to OpenClaw's active channel.
    
    Uses the message tool to send updates to Telegram/Discord/etc.
    """
    
    def __init__(
        self, 
        throttle_ms: int = 500,
        batch_events: bool = True,
        verbose: bool = True
    ):
        """
        Args:
            throttle_ms: Minimum ms between messages (avoid spam)
            batch_events: Batch rapid events into single message
            verbose: Include extra details in messages
        """
        self.throttle_ms = throttle_ms
        self.batch_events = batch_events
        self.verbose = verbose
        self._last_send = 0
        self._pending: list[Progress] = []
        self._lock = asyncio.Lock()
    
    async def emit(self, progress: Progress) -> None:
        """Send progress to OpenClaw channel."""
        async with self._lock:
            now = datetime.now().timestamp() * 1000
            
            if self.batch_events:
                self._pending.append(progress)
                
                # Check if we should send now
                if now - self._last_send >= self.throttle_ms:
                    await self._send_batch()
                else:
                    # Schedule send after throttle period
                    await asyncio.sleep(self.throttle_ms / 1000)
                    if self._pending:
                        await self._send_batch()
            else:
                # Send immediately (respecting throttle)
                if now - self._last_send >= self.throttle_ms:
                    await self._send_message(progress.format(self.verbose))
                    self._last_send = now
    
    async def _send_batch(self) -> None:
        """Send batched events as single message."""
        if not self._pending:
            return
        
        # Format all pending events
        lines = [p.format(self.verbose) for p in self._pending]
        message = "\n".join(lines)
        
        await self._send_message(message)
        self._pending = []
        self._last_send = datetime.now().timestamp() * 1000
    
    async def _send_message(self, message: str) -> None:
        """Send message via OpenClaw."""
        # For now, just print - actual OpenClaw integration would use
        # the message tool or a direct API call
        print(f"[OpenClaw] {message}")
        
        # TODO: Integrate with actual OpenClaw message sending
        # This would typically be done by the orchestrator wrapper
        # that has access to the OpenClaw context


class TelegramProgress(ProgressHandler):
    """
    Send progress directly to Telegram.
    
    For standalone use outside OpenClaw.
    """
    
    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        throttle_ms: int = 1000
    ):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.throttle_ms = throttle_ms
        self._last_send = 0
    
    async def emit(self, progress: Progress) -> None:
        """Send to Telegram."""
        now = datetime.now().timestamp() * 1000
        
        if now - self._last_send < self.throttle_ms:
            return  # Skip to avoid spam
        
        try:
            import aiohttp
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            async with aiohttp.ClientSession() as session:
                await session.post(url, json={
                    "chat_id": self.chat_id,
                    "text": progress.format(verbose=True),
                    "parse_mode": "HTML"
                })
            
            self._last_send = now
        except Exception as e:
            print(f"Telegram send failed: {e}")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_progress(
    event: ProgressEvent,
    message: str,
    **data
) -> Progress:
    """Helper to create progress events."""
    return Progress(event=event, message=message, data=data)


# Convenience functions for common events
def task_received(task: str) -> Progress:
    preview = task[:50] + "..." if len(task) > 50 else task
    return create_progress(
        ProgressEvent.TASK_RECEIVED,
        f"Task received: {preview}",
        task_length=len(task)
    )

def task_analyzed(category: str, complexity: str, mode: str) -> Progress:
    return create_progress(
        ProgressEvent.TASK_ANALYZED,
        f"Analyzed: {category} task, {complexity} complexity",
        category=category,
        complexity=complexity,
        mode=mode
    )

def models_selected(primaries: list, validators: list) -> Progress:
    models_str = ", ".join(primaries)
    val_str = f" → validate: {', '.join(validators)}" if validators else ""
    return create_progress(
        ProgressEvent.MODELS_SELECTED,
        f"Models: {models_str}{val_str}",
        primaries=primaries,
        validators=validators
    )

def model_starting(model: str) -> Progress:
    return create_progress(
        ProgressEvent.MODEL_STARTING,
        f"{model} starting...",
        model=model
    )

def model_completed(model: str, score: float, time_s: float, code_len: int) -> Progress:
    return create_progress(
        ProgressEvent.MODEL_COMPLETED,
        f"{model} done: score={score:.0f}, {time_s:.1f}s, {code_len} chars",
        model=model,
        score=score,
        execution_time=time_s,
        code_length=code_len
    )

def model_failed(model: str, error: str) -> Progress:
    return create_progress(
        ProgressEvent.MODEL_FAILED,
        f"{model} failed: {error[:50]}",
        model=model,
        error=error
    )

def validation_starting(validator: str) -> Progress:
    return create_progress(
        ProgressEvent.VALIDATION_STARTING,
        f"Validating with {validator}...",
        validator=validator
    )

def validation_completed(confidence: float, needs_review: bool) -> Progress:
    status = "⚠️ needs review" if needs_review else "passed"
    return create_progress(
        ProgressEvent.VALIDATION_COMPLETED,
        f"Validation {status} ({confidence:.0%} confidence)",
        confidence=confidence,
        needs_review=needs_review
    )

def merge_starting(num_outputs: int) -> Progress:
    return create_progress(
        ProgressEvent.MERGE_STARTING,
        f"Merging {num_outputs} outputs...",
        num_outputs=num_outputs
    )

def merge_completed(score: float, code_len: int) -> Progress:
    return create_progress(
        ProgressEvent.MERGE_COMPLETED,
        f"Merged: score={score:.0f}, {code_len} chars",
        score=score,
        code_length=code_len
    )

def orchestration_completed(total_time: float, final_score: float) -> Progress:
    return create_progress(
        ProgressEvent.ORCHESTRATION_COMPLETED,
        f"Complete! {total_time:.1f}s total, score={final_score:.0f}",
        total_time=total_time,
        final_score=final_score
    )

def orchestration_failed(error: str) -> Progress:
    return create_progress(
        ProgressEvent.ORCHESTRATION_FAILED,
        f"Failed: {error}",
        error=error
    )


# =============================================================================
# ASYNC HELPER
# =============================================================================

async def emit_progress(
    callback: Optional[ProgressCallback],
    progress: Progress
) -> None:
    """
    Safely emit progress to callback (sync or async).
    """
    if callback is None:
        return
    
    try:
        result = callback(progress)
        if asyncio.iscoroutine(result):
            await result
    except Exception as e:
        print(f"Progress callback error: {e}")
