"""
CampaignManagerAgent - Intelligent Task Decomposition.

This agent receives high-level goals (like "Create a Mother's Day campaign")
and decomposes them into a structured plan of subtasks with dependencies.

Inspired by the Eigent project's approach to task decomposition:
- AGGRESSIVE PARALLELIZATION
- STRATEGIC GROUPING
- CLEAR DELIVERABLES
"""

from __future__ import annotations

import json
from typing import Any

from agno.agent import Agent
from agno.tools import tool

from core.logging import get_logger

from .base import get_db, get_model

logger = get_logger(__name__)


# Available agents for task assignment
AVAILABLE_AGENTS = {
    "pesquisador": {
        "description": "Research agent for trends, references, and data analysis",
        "capabilities": [
            "Search viral content on social media",
            "Analyze competitor strategies",
            "Find trending topics",
            "Collect data for content creation",
            "Web search for scientific validation",
        ],
    },
    "criador_instagram": {
        "description": "Content creator for Instagram posts, stories, and reels",
        "capabilities": [
            "Write engaging captions and copies",
            "Create content briefs",
            "Generate image descriptions",
            "Submit content for approval",
        ],
    },
    "designer": {
        "description": "Visual designer for graphics and visual concepts",
        "capabilities": [
            "Create visual concepts",
            "Generate image prompts",
            "Design layouts",
            "Adapt visuals to different formats",
        ],
    },
    "revisor": {
        "description": "Quality reviewer for compliance and content quality",
        "capabilities": [
            "Validate CFM compliance",
            "Review content quality",
            "Check scientific accuracy",
            "Approve or request revisions",
        ],
    },
    "seo_analyst": {
        "description": "SEO specialist for search optimization and analytics",
        "capabilities": [
            "Keyword research and analysis",
            "SERP analysis and competitor SEO audit",
            "Meta tags optimization",
            "Content structure recommendations",
            "Search performance analysis",
        ],
    },
    "strategist": {
        "description": "Strategic planner for campaigns and calendars",
        "capabilities": [
            "Plan campaign timelines",
            "Define content strategy",
            "Set KPIs and goals",
            "Coordinate launch schedules",
        ],
    },
}


def _build_agents_context() -> str:
    """Build context string describing available agents."""
    lines = ["## Available Agents for Task Assignment\n"]
    for name, info in AVAILABLE_AGENTS.items():
        lines.append(f"### {name}")
        lines.append(f"**Description:** {info['description']}")
        lines.append("**Capabilities:**")
        for cap in info["capabilities"]:
            lines.append(f"- {cap}")
        lines.append("")
    return "\n".join(lines)


DECOMPOSITION_PROMPT = f"""You are a Campaign Manager Agent specialized in decomposing complex marketing goals into actionable subtasks.

<role>
You are the strategic coordinator who receives high-level goals and creates detailed execution plans. Your expertise is in understanding marketing campaigns and breaking them down into parallel workstreams.
</role>

<team_structure>
{_build_agents_context()}
</team_structure>

<mandatory_instructions>
When creating a task decomposition:

1. **AGGRESSIVE PARALLELIZATION**: Maximize parallel execution
   - If two tasks don't depend on each other, they should run in parallel
   - Research tasks typically have no dependencies
   - Creation tasks depend on research
   - Review tasks depend on creation

2. **STRATEGIC GROUPING**: Group related tasks logically
   - Research tasks first (parallel)
   - Creation tasks second (after relevant research)
   - Review/validation last (after creation)

3. **CLEAR DELIVERABLES**: Each task must have a specific, measurable output
   - "Relatório de trends" not "Pesquisar"
   - "3 opções de copy" not "Criar conteúdo"
   - "Aprovação final" not "Revisar"

4. **DEPENDENCY SPECIFICATION**: Be explicit about dependencies
   - Use task IDs ("1", "2", etc.) to reference dependencies
   - Empty dependencies [] means the task can start immediately
   - Tasks with the same dependencies can run in parallel
</mandatory_instructions>

<output_format>
You MUST return a valid JSON object with the following structure:

```json
{{
  "goal_analysis": "Brief analysis of the goal and approach",
  "subtasks": [
    {{
      "task_id": "1",
      "description": "Clear description of what to do",
      "agent": "agent_name",
      "deliverable": "Specific output expected",
      "dependencies": []
    }},
    {{
      "task_id": "2",
      "description": "Another task description",
      "agent": "agent_name",
      "deliverable": "Specific output expected",
      "dependencies": ["1"]
    }}
  ]
}}
```

IMPORTANT:
- task_id must be sequential strings: "1", "2", "3", etc.
- agent must be one of: {', '.join(AVAILABLE_AGENTS.keys())}
- dependencies is a list of task_id strings that must complete first
- Return ONLY the JSON, no markdown code blocks or extra text
</output_format>

<philosophy>
- Bias for Action: Create plans that can start immediately
- Parallel First: Always look for opportunities to parallelize
- Quality Assurance: Always include review/validation steps
- Clear Communication: Deliverables must be unambiguous
</philosophy>
"""


@tool
def decompose_goal(goal: str, context: dict | None = None) -> dict[str, Any]:
    """
    Decompose a high-level goal into structured subtasks.

    This is the main entry point for task decomposition. It uses the
    CampaignManagerAgent to analyze the goal and create a plan.

    Args:
        goal: The high-level goal to decompose (e.g., "Create a Mother's Day campaign")
        context: Optional context dictionary with:
            - clinic_id: The clinic this campaign is for
            - specialty: The medical specialty
            - brand_profile: Brand voice and style preferences
            - deadline: Optional deadline for the campaign

    Returns:
        Dictionary with:
            - goal_analysis: Brief analysis of the goal
            - subtasks: List of subtask dictionaries

    Example:
        result = decompose_goal(
            goal="Create a Mother's Day campaign for Clínica Odonto Smile",
            context={"specialty": "odontologia", "clinic_id": "abc123"}
        )
    """
    import asyncio

    async def _decompose():
        return await decompose_goal_async(goal, context)

    return asyncio.get_event_loop().run_until_complete(_decompose())


async def decompose_goal_async(goal: str, context: dict | None = None) -> dict[str, Any]:
    """
    Async version of decompose_goal.

    Args:
        goal: The high-level goal to decompose
        context: Optional context dictionary

    Returns:
        Dictionary with goal_analysis and subtasks
    """
    try:
        # Build the prompt with context
        context_str = ""
        if context:
            context_parts = []
            if context.get("clinic_id"):
                context_parts.append(f"- Clinic ID: {context['clinic_id']}")
            if context.get("specialty"):
                context_parts.append(f"- Specialty: {context['specialty']}")
            if context.get("brand_profile"):
                context_parts.append(f"- Brand Profile: {context['brand_profile']}")
            if context.get("deadline"):
                context_parts.append(f"- Deadline: {context['deadline']}")
            if context_parts:
                context_str = "\n\nContext:\n" + "\n".join(context_parts)

        full_prompt = f"Goal: {goal}{context_str}\n\nDecompose this goal into subtasks."

        # Run the agent
        response = await campaign_manager.arun(message=full_prompt)

        # Parse the response
        content = ""
        if hasattr(response, "content"):
            content = str(response.content) if response.content else ""
        elif isinstance(response, str):
            content = response

        # Try to extract JSON from the response
        result = _parse_decomposition_response(content)

        logger.info(
            "Goal decomposed successfully",
            goal=goal[:50],
            subtask_count=len(result.get("subtasks", [])),
        )

        return result

    except Exception as e:
        logger.exception("Failed to decompose goal", goal=goal[:50])
        return {
            "goal_analysis": f"Failed to decompose: {e!s}",
            "subtasks": [],
            "error": str(e),
        }


def _parse_decomposition_response(content: str) -> dict[str, Any]:
    """Parse the agent's response to extract the JSON decomposition."""
    # Try direct JSON parsing first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in the content (might be wrapped in markdown)
    import re

    json_match = re.search(r"\{[\s\S]*\}", content)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # If all else fails, return a structured error
    return {
        "goal_analysis": "Could not parse decomposition response",
        "subtasks": [],
        "error": "Failed to parse JSON from response",
        "raw_response": content[:500],
    }


def validate_decomposition(decomposition: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate a decomposition result.

    Args:
        decomposition: The decomposition dictionary to validate

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    if "subtasks" not in decomposition:
        errors.append("Missing 'subtasks' key in decomposition")
        return False, errors

    subtasks = decomposition["subtasks"]
    if not isinstance(subtasks, list):
        errors.append("'subtasks' must be a list")
        return False, errors

    if len(subtasks) == 0:
        errors.append("Decomposition has no subtasks")
        return False, errors

    task_ids = set()
    for i, task in enumerate(subtasks):
        prefix = f"Subtask {i + 1}"

        # Required fields
        for field in ["task_id", "description", "agent", "deliverable"]:
            if field not in task:
                errors.append(f"{prefix}: Missing required field '{field}'")

        # Validate task_id
        if "task_id" in task:
            if task["task_id"] in task_ids:
                errors.append(f"{prefix}: Duplicate task_id '{task['task_id']}'")
            task_ids.add(task["task_id"])

        # Validate agent
        if "agent" in task and task["agent"] not in AVAILABLE_AGENTS:
            errors.append(f"{prefix}: Unknown agent '{task['agent']}'")

        # Validate dependencies
        if "dependencies" in task:
            if not isinstance(task["dependencies"], list):
                errors.append(f"{prefix}: 'dependencies' must be a list")
            else:
                for dep in task["dependencies"]:
                    if dep not in task_ids and dep >= task.get("task_id", "0"):
                        # Allow forward references for now, but warn
                        pass

    return len(errors) == 0, errors


# Create the agent
campaign_manager = Agent(
    name="Campaign Manager",
    model=get_model("smart"),
    db=get_db(),
    instructions=DECOMPOSITION_PROMPT,
    tools=[],  # This agent uses pure reasoning, no tools needed
    add_history_to_context=True,
    num_history_runs=3,
    markdown=False,  # We want clean JSON output
)
