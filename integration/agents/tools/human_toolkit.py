"""
Human-in-the-Loop Toolkit for Agent Interactions.

This module provides tools that allow agents to interact with humans:
- ask_human: Pause and wait for human input
- send_message_to_user: Send notification without waiting
- request_approval: Request approval for content

These tools integrate with the existing HumanLoopController and
notification systems.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agno.tools import tool

from core.logging import get_logger

if TYPE_CHECKING:
    from orchestration.human_loop import HumanLoopController

logger = get_logger(__name__)

# Global reference to the HumanLoopController
# Set by the AgentOS when initializing
_human_loop_controller: HumanLoopController | None = None


def set_human_loop_controller(controller: HumanLoopController) -> None:
    """Set the global HumanLoopController instance."""
    global _human_loop_controller
    _human_loop_controller = controller


def get_human_loop_controller() -> HumanLoopController | None:
    """Get the global HumanLoopController instance."""
    return _human_loop_controller


@tool
def ask_human(
    question: str,
    options: list[str] | None = None,
    context: dict[str, Any] | None = None,
    timeout_minutes: int = 30,
) -> str | None:
    """
    Pause execution and wait for human input.

    Use this when you need human decision-making or clarification.
    The execution will pause until a human responds or timeout occurs.

    Args:
        question: The question to ask the human
        options: Optional list of predefined answer options
        context: Optional context dict to help the human understand the situation
        timeout_minutes: How long to wait for response (default 30 min, max 1440)

    Returns:
        The human's response, or None if timeout

    Example:
        response = ask_human(
            question="Which visual style should we use for this campaign?",
            options=["Modern/Minimal", "Classic/Professional", "Colorful/Playful"],
            context={"campaign": "Dia das Mães", "client": "Clínica Odonto"}
        )

        if response:
            # Use the response
            pass
        else:
            # Handle timeout - use default or skip
            pass
    """
    import asyncio

    async def _ask():
        return await ask_human_async(question, options, context, timeout_minutes)

    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_ask())
    except RuntimeError:
        # No event loop running, create new one
        return asyncio.run(_ask())


async def ask_human_async(
    question: str,
    options: list[str] | None = None,
    context: dict[str, Any] | None = None,
    timeout_minutes: int = 30,
) -> str | None:
    """Async version of ask_human."""
    controller = get_human_loop_controller()

    if not controller:
        logger.warning("HumanLoopController not available, returning None")
        return None

    try:
        response = await controller.request_input(
            agent_name="agent_tool",
            context=context or {},
            question=question,
            options=options,
            timeout_minutes=timeout_minutes,
        )
        return response
    except Exception:
        logger.exception("Failed to ask human")
        return None


@tool
def send_message_to_user(
    title: str,
    description: str,
    message_type: str = "info",
    data: dict[str, Any] | None = None,
) -> bool:
    """
    Send a notification to the user without waiting for response.

    Use this to inform the user about progress, results, or important events.
    This does NOT pause execution.

    Args:
        title: Short title for the notification
        description: Detailed message content
        message_type: Type of message - "info", "success", "warning", "error"
        data: Optional additional data to include

    Returns:
        True if sent successfully, False otherwise

    Example:
        send_message_to_user(
            title="Research Complete",
            description="Found 15 viral posts related to Mother's Day dentistry content.",
            message_type="success",
            data={"post_count": 15, "top_engagement": 50000}
        )
    """
    import asyncio

    async def _send():
        return await send_message_to_user_async(title, description, message_type, data)

    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_send())
    except RuntimeError:
        return asyncio.run(_send())


async def send_message_to_user_async(
    title: str,
    description: str,
    message_type: str = "info",
    data: dict[str, Any] | None = None,
) -> bool:
    """Async version of send_message_to_user."""
    import json

    controller = get_human_loop_controller()

    if not controller:
        logger.warning("HumanLoopController not available")
        return False

    try:
        # Use the Redis pub/sub to send notification
        notification = {
            "type": "agent_message",
            "message_type": message_type,
            "title": title,
            "description": description,
            "data": data,
        }

        await controller.redis.publish(
            "notifications:agent_messages",
            json.dumps(notification, default=str),
        )

        logger.info(
            "Message sent to user",
            title=title,
            message_type=message_type,
        )

        return True

    except Exception:
        logger.exception("Failed to send message to user")
        return False


@tool
def request_approval(
    content: str,
    content_type: str,
    metadata: dict[str, Any] | None = None,
    timeout_minutes: int = 60,
) -> bool:
    """
    Request approval for content before proceeding.

    Use this when content needs human validation before publication or action.
    This PAUSES execution until approval is received.

    Args:
        content: The content to be approved (text, JSON, etc.)
        content_type: Type of content - "copy", "image", "campaign", "strategy"
        metadata: Optional metadata about the content
        timeout_minutes: How long to wait for approval (default 60 min)

    Returns:
        True if approved, False if rejected or timeout

    Example:
        approved = request_approval(
            content='''
            🦷 Neste Dia das Mães, presenteie com o sorriso que ela merece!

            Sabia que cuidar da saúde bucal é um ato de amor?
            Agende uma avaliação para sua mãe!
            ''',
            content_type="copy",
            metadata={"campaign": "Dia das Mães", "format": "Instagram Post"}
        )

        if approved:
            # Proceed with publication
            pass
        else:
            # Content rejected, revise or skip
            pass
    """
    import asyncio

    async def _request():
        return await request_approval_async(content, content_type, metadata, timeout_minutes)

    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_request())
    except RuntimeError:
        return asyncio.run(_request())


async def request_approval_async(
    content: str,
    content_type: str,
    metadata: dict[str, Any] | None = None,
    timeout_minutes: int = 60,
) -> bool:
    """Async version of request_approval."""
    controller = get_human_loop_controller()

    if not controller:
        logger.warning("HumanLoopController not available, auto-rejecting")
        return False

    try:
        question = f"""
Please review and approve this {content_type}:

---
{content}
---

Metadata: {metadata or 'None'}
"""

        response = await controller.request_input(
            agent_name="agent_approval",
            context={
                "content": content,
                "content_type": content_type,
                "metadata": metadata,
            },
            question=question,
            options=["Approve", "Reject"],
            timeout_minutes=timeout_minutes,
        )

        if response and response.lower() in ["approve", "approved", "yes", "sim", "aprovar"]:
            logger.info("Content approved", content_type=content_type)
            return True
        else:
            logger.info("Content rejected or timeout", content_type=content_type, response=response)
            return False

    except Exception:
        logger.exception("Failed to request approval")
        return False


@tool
def escalate_to_human(
    reason: str,
    context: dict[str, Any] | None = None,
    urgency: str = "medium",
) -> bool:
    """
    Escalate the current task to a human operator.

    Use this when you encounter a situation you cannot handle or that
    requires human expertise. This notifies the team but does NOT pause execution.

    Args:
        reason: Why escalation is needed
        context: Relevant context for the human
        urgency: "low", "medium", "high", "critical"

    Returns:
        True if escalation was sent successfully

    Example:
        escalate_to_human(
            reason="Patient expressed dissatisfaction with previous treatment",
            context={"contact_id": "123", "last_message": "Não estou satisfeito..."},
            urgency="high"
        )
    """
    import asyncio

    async def _escalate():
        return await escalate_to_human_async(reason, context, urgency)

    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_escalate())
    except RuntimeError:
        return asyncio.run(_escalate())


async def escalate_to_human_async(
    reason: str,
    context: dict[str, Any] | None = None,
    urgency: str = "medium",
) -> bool:
    """Async version of escalate_to_human."""
    import json

    controller = get_human_loop_controller()

    if not controller:
        logger.warning("HumanLoopController not available")
        return False

    try:
        notification = {
            "type": "escalation",
            "reason": reason,
            "context": context,
            "urgency": urgency,
        }

        await controller.redis.publish(
            "notifications:escalations",
            json.dumps(notification, default=str),
        )

        logger.info(
            "Escalation sent",
            reason=reason[:100],
            urgency=urgency,
        )

        return True

    except Exception:
        logger.exception("Failed to escalate to human")
        return False
