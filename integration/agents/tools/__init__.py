"""
Agent tools module.

Contains specialized tools for agent orchestration:
- note_taking: Inter-agent communication via shared notes
- human_toolkit: Human-in-the-loop interactions
"""

from .human_toolkit import (
    ask_human,
    escalate_to_human,
    request_approval,
    send_message_to_user,
    set_human_loop_controller,
)
from .note_taking import (
    append_note,
    list_notes,
    read_note,
    write_note,
)

__all__ = [
    # Note-taking tools
    "write_note",
    "append_note",
    "read_note",
    "list_notes",
    # Human-in-the-loop tools
    "ask_human",
    "send_message_to_user",
    "request_approval",
    "escalate_to_human",
    "set_human_loop_controller",
]
