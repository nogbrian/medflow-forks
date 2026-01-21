"""
Note-Taking Toolkit for Inter-Agent Communication.

Inspired by the Eigent project, this module provides a shared note-taking
system that allows agents to communicate findings and context with each other.

Notes are stored in a structured format with timestamps and can be:
- Written (create/overwrite)
- Appended (add to existing)
- Read (single note or all notes)
- Listed (get available note names)

Storage: /tmp/medflow_notes/{project_id}/
Format: Markdown with timestamps
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from agno.tools import tool

from core.logging import get_logger

logger = get_logger(__name__)

# Base directory for notes storage
NOTES_BASE_DIR = Path("/tmp/medflow_notes")


def _get_notes_dir(project_id: str) -> Path:
    """Get the notes directory for a specific project."""
    # Sanitize project_id to prevent path traversal
    safe_id = "".join(c for c in project_id if c.isalnum() or c in "-_")
    return NOTES_BASE_DIR / safe_id


def _ensure_notes_dir(project_id: str) -> Path:
    """Ensure the notes directory exists and return its path."""
    notes_dir = _get_notes_dir(project_id)
    notes_dir.mkdir(parents=True, exist_ok=True)
    return notes_dir


def _get_timestamp() -> str:
    """Get a formatted timestamp for notes."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


@tool
def write_note(project_id: str, note_name: str, content: str) -> str:
    """
    Write or overwrite a note for inter-agent communication.

    Use this to record important discoveries, research findings, or context
    that other agents may need to complete their tasks.

    Args:
        project_id: The project/campaign ID (e.g., clinic ID or execution plan ID)
        note_name: Name of the note (e.g., "trends_dia_maes", "referencias_virais")
        content: The content to write (Markdown supported)

    Returns:
        Confirmation message with the note path

    Example:
        write_note(
            project_id="campaign-123",
            note_name="trends_dia_maes",
            content="## Principais Tendências\\n\\n1. Posts emotivos..."
        )
    """
    try:
        notes_dir = _ensure_notes_dir(project_id)

        # Sanitize note_name
        safe_name = "".join(c for c in note_name if c.isalnum() or c in "-_")
        if not safe_name:
            safe_name = "unnamed_note"

        note_path = notes_dir / f"{safe_name}.md"

        # Add header with metadata
        timestamp = _get_timestamp()
        formatted_content = f"""---
note: {safe_name}
project: {project_id}
created_at: {timestamp}
---

{content}
"""

        note_path.write_text(formatted_content, encoding="utf-8")

        logger.info(
            "Note written",
            project_id=project_id,
            note_name=safe_name,
            path=str(note_path),
        )

        return f"Note '{safe_name}' written successfully at {note_path}"

    except Exception as e:
        logger.exception("Failed to write note", project_id=project_id, note_name=note_name)
        return f"Error writing note: {e!s}"


@tool
def append_note(project_id: str, note_name: str, content: str) -> str:
    """
    Append content to an existing note.

    Use this to add new information to an existing note without overwriting
    the previous content. Perfect for accumulating findings during research.

    Args:
        project_id: The project/campaign ID
        note_name: Name of the note to append to
        content: The content to append (Markdown supported)

    Returns:
        Confirmation message

    Example:
        append_note(
            project_id="campaign-123",
            note_name="trends_dia_maes",
            content="\\n## Atualização\\n\\nEncontrei mais 5 exemplos..."
        )
    """
    try:
        notes_dir = _ensure_notes_dir(project_id)

        # Sanitize note_name
        safe_name = "".join(c for c in note_name if c.isalnum() or c in "-_")
        if not safe_name:
            safe_name = "unnamed_note"

        note_path = notes_dir / f"{safe_name}.md"

        # Add timestamp for the append
        timestamp = _get_timestamp()
        append_content = f"\n\n---\n*Updated at {timestamp}*\n\n{content}"

        if note_path.exists():
            # Append to existing file
            with note_path.open("a", encoding="utf-8") as f:
                f.write(append_content)
            action = "appended to"
        else:
            # Create new file if doesn't exist
            header = f"""---
note: {safe_name}
project: {project_id}
created_at: {timestamp}
---

{content}
"""
            note_path.write_text(header, encoding="utf-8")
            action = "created"

        logger.info(
            f"Note {action}",
            project_id=project_id,
            note_name=safe_name,
            path=str(note_path),
        )

        return f"Note '{safe_name}' {action} successfully"

    except Exception as e:
        logger.exception("Failed to append note", project_id=project_id, note_name=note_name)
        return f"Error appending to note: {e!s}"


@tool
def read_note(project_id: str, note_name: str = "all_notes") -> str:
    """
    Read a specific note or all notes for a project.

    IMPORTANT: Always use this at the start of your task to check what
    context and findings other agents have already gathered.

    Args:
        project_id: The project/campaign ID
        note_name: Name of specific note, or "all_notes" to read everything

    Returns:
        The note content(s) or a message if no notes found

    Example:
        # Read all notes to get full context
        context = read_note(project_id="campaign-123")

        # Read specific note
        trends = read_note(project_id="campaign-123", note_name="trends_dia_maes")
    """
    try:
        notes_dir = _get_notes_dir(project_id)

        if not notes_dir.exists():
            return f"No notes found for project '{project_id}'. This project has no shared context yet."

        if note_name == "all_notes":
            # Read all notes in the directory
            notes = []
            for note_file in sorted(notes_dir.glob("*.md")):
                content = note_file.read_text(encoding="utf-8")
                notes.append(f"# {note_file.stem}\n\n{content}")

            if not notes:
                return f"No notes found for project '{project_id}'."

            combined = "\n\n" + "=" * 50 + "\n\n".join(notes)

            logger.info(
                "Read all notes",
                project_id=project_id,
                count=len(notes),
            )

            return combined

        else:
            # Read specific note
            safe_name = "".join(c for c in note_name if c.isalnum() or c in "-_")
            note_path = notes_dir / f"{safe_name}.md"

            if not note_path.exists():
                available = [f.stem for f in notes_dir.glob("*.md")]
                if available:
                    return f"Note '{safe_name}' not found. Available notes: {', '.join(available)}"
                return f"Note '{safe_name}' not found and no other notes exist for project '{project_id}'."

            content = note_path.read_text(encoding="utf-8")

            logger.info(
                "Read note",
                project_id=project_id,
                note_name=safe_name,
            )

            return content

    except Exception as e:
        logger.exception("Failed to read note", project_id=project_id, note_name=note_name)
        return f"Error reading note: {e!s}"


@tool
def list_notes(project_id: str) -> list[str]:
    """
    List all available notes for a project.

    Use this to discover what context has been gathered before reading.

    Args:
        project_id: The project/campaign ID

    Returns:
        List of note names (without .md extension)

    Example:
        notes = list_notes(project_id="campaign-123")
        # Returns: ["trends_dia_maes", "referencias_virais", "copies_draft"]
    """
    try:
        notes_dir = _get_notes_dir(project_id)

        if not notes_dir.exists():
            return []

        note_names = [f.stem for f in sorted(notes_dir.glob("*.md"))]

        logger.info(
            "Listed notes",
            project_id=project_id,
            count=len(note_names),
        )

        return note_names

    except Exception as e:
        logger.exception("Failed to list notes", project_id=project_id)
        return []


# Async versions for use outside of tool context
async def write_note_async(project_id: str, note_name: str, content: str) -> str:
    """Async wrapper for write_note."""
    return write_note(project_id, note_name, content)


async def append_note_async(project_id: str, note_name: str, content: str) -> str:
    """Async wrapper for append_note."""
    return append_note(project_id, note_name, content)


async def read_note_async(project_id: str, note_name: str = "all_notes") -> str:
    """Async wrapper for read_note."""
    return read_note(project_id, note_name)


async def list_notes_async(project_id: str) -> list[str]:
    """Async wrapper for list_notes."""
    return list_notes(project_id)
