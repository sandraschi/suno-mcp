"""
FastMCP 3.1 sampling with tools — SEP-1577 agentic orchestration for Suno-MCP.
"""

import logging

from fastmcp import Context

logger = logging.getLogger(__name__)


def build_success_response(**kwargs: object) -> dict:
    return {
        "success": True,
        "operation": kwargs.get("operation", "unknown"),
        "summary": kwargs.get("summary", "Operation completed"),
        "result": kwargs.get("result", {}),
        "next_steps": kwargs.get("next_steps", []),
        "suggestions": kwargs.get("suggestions", []),
    }


def build_error_response(**kwargs: object) -> dict:
    return {
        "success": False,
        "error": kwargs.get("error", "Unknown error"),
        "error_code": kwargs.get("error_code", "UNKNOWN_ERROR"),
        "message": kwargs.get("message", "An error occurred"),
        "recovery_options": kwargs.get("recovery_options", []),
        "urgency": kwargs.get("urgency", "medium"),
    }


def register_agentic_suno_workflow(app) -> None:
    """Register agentic_suno_workflow on the FastMCP app."""

    @app.tool()
    async def agentic_suno_workflow(
        workflow_prompt: str,
        available_tools: list[str],
        max_iterations: int = 5,
        context: Context | None = None,
    ) -> dict:
        """
        Execute multi-step Suno workflows via FastMCP 3.1 sampling with tools (SEP-1577).

        The host or server-side LLM uses context.sample_step in a loop: it chooses
        tool calls, tools run, results are fed back until the model returns a final
        answer or max_iterations is reached.

        Args:
            workflow_prompt: What to accomplish in natural language.
            available_tools: names of tools the LLM may call (e.g. suno_open_browser, suno_generate_track).
            max_iterations: Maximum LLM-tool rounds (default 5).

        Returns:
            Structured dict with success, result (final_output, iterations, executed_tools).
        """
        try:
            if not workflow_prompt:
                return build_error_response(
                    error="No workflow prompt provided",
                    error_code="MISSING_WORKFLOW_PROMPT",
                    message="workflow_prompt is required",
                    recovery_options=["Describe the music or session task clearly"],
                    urgency="medium",
                )
            if not available_tools:
                return build_error_response(
                    error="No tools specified",
                    error_code="EMPTY_TOOLS_LIST",
                    message="available_tools cannot be empty",
                    recovery_options=["Include tool names such as suno_generate_track, suno_get_status"],
                    urgency="medium",
                )
            if context is None or not hasattr(context, "sample_step"):
                return build_error_response(
                    error="Sampling not available",
                    error_code="SAMPLING_UNAVAILABLE",
                    message="Context does not support sampling with tools (requires FastMCP 3.1+)",
                    recovery_options=[
                        "Install fastmcp>=3.1",
                        "Use a client that supports MCP sampling",
                        "Set SUNO_SAMPLING_* for server-side Ollama/OpenAI-compatible LLM",
                    ],
                    urgency="high",
                )

            all_tools = await app.list_tools()
            name_to_tool = {t.name: t for t in all_tools if hasattr(t, "name")}
            tools_for_sampling = [
                name_to_tool[name] for name in available_tools if name in name_to_tool
            ]
            missing = [n for n in available_tools if n not in name_to_tool]
            if missing:
                logger.warning("Agentic workflow: tools not found on app: %s", missing)
            if not tools_for_sampling:
                return build_error_response(
                    error="No matching tools found",
                    error_code="TOOLS_NOT_FOUND",
                    message=f"None of available_tools matched. Registered: {list(name_to_tool.keys())}",
                    recovery_options=["Use names from get_server_status or help"],
                    urgency="high",
                )

            system_prompt = (
                "You are a Suno AI music automation assistant. Use the provided MCP tools "
                "to complete the browser/session/music task. Credentials may be required for "
                "login — never echo passwords. Summarize results and next steps briefly."
            )
            messages: list = [{"role": "user", "content": workflow_prompt}]
            executed_tools: list[str] = []
            iterations = 0
            step_last = None

            while iterations < max_iterations:
                iterations += 1
                logger.info("Agentic Suno workflow step %s/%s", iterations, max_iterations)
                step = await context.sample_step(
                    messages,
                    system_prompt=system_prompt,
                    tools=tools_for_sampling,
                    execute_tools=True,
                    max_tokens=4096,
                )
                step_last = step
                if hasattr(step, "history") and step.history:
                    messages = list(step.history)
                if hasattr(step, "tool_calls") and step.tool_calls:
                    for tc in step.tool_calls:
                        name = getattr(tc, "name", None) or getattr(tc, "tool_name", str(tc))
                        if name:
                            executed_tools.append(name)
                if not getattr(step, "is_tool_use", True):
                    final_text = getattr(step, "text", "") or ""
                    return build_success_response(
                        operation="agentic_suno_workflow",
                        summary=f"Workflow completed in {iterations} round(s).",
                        result={
                            "final_output": final_text,
                            "iterations": iterations,
                            "executed_tools": list(dict.fromkeys(executed_tools)),
                        },
                        next_steps=["Review output; run suno_download_track if a track was created."],
                        suggestions=[
                            "suno_get_status()",
                            "suno_close_browser() when finished",
                        ],
                    )

            return build_success_response(
                operation="agentic_suno_workflow",
                summary=f"Workflow stopped after {max_iterations} iterations (max).",
                result={
                    "final_output": getattr(step_last, "text", "") or "(max iterations reached)",
                    "iterations": iterations,
                    "executed_tools": list(dict.fromkeys(executed_tools)),
                },
                next_steps=["Increase max_iterations or simplify the workflow prompt."],
                suggestions=[],
            )
        except Exception as e:
            logger.error("Agentic Suno workflow failed: %s", e, exc_info=True)
            return build_error_response(
                error="Workflow execution failed",
                error_code="WORKFLOW_EXECUTION_ERROR",
                message=str(e),
                recovery_options=[
                    "Check workflow_prompt and available_tools",
                    "Ensure Playwright browsers are installed and Suno is reachable",
                ],
                urgency="high",
            )
