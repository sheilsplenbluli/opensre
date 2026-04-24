"""Base tool interface for opensre integrations.

All tools must inherit from BaseTool and implement the required methods.
This mirrors the structure defined in .cursor/rules/tools.mdc.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Result returned from a tool execution."""

    success: bool
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.success


class BaseTool(ABC):
    """Abstract base class for all opensre tools.

    Subclasses must define `my_tool_name` as a class attribute and
    implement `is_available`, `extract_params`, and `run`.

    Example::

        class MyTool(BaseTool):
            my_tool_name = "my_tool"

            def is_available(self) -> bool:
                return shutil.which("my_tool") is not None

            def extract_params(self, raw: dict) -> dict:
                return {"target": raw["target"]}

            def run(self, params: dict) -> ToolResult:
                ...
    """

    #: Unique snake_case identifier for this tool (required on subclasses)
    my_tool_name: str = ""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "my_tool_name", ""):
            raise TypeError(
                f"{cls.__name__} must define a non-empty 'my_tool_name' class attribute"
            )

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this tool's dependencies are present on the system."""

    @abstractmethod
    def extract_params(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Validate and extract the parameters needed by `run` from a raw dict.

        Args:
            raw: Unvalidated input dictionary (e.g. from a graph node payload).

        Returns:
            A cleaned parameter dict ready to pass to `run`.

        Raises:
            ValueError: If required parameters are missing or invalid.
        """

    @abstractmethod
    def run(self, params: dict[str, Any]) -> ToolResult:
        """Execute the tool with the given parameters.

        Args:
            params: Validated parameters produced by `extract_params`.

        Returns:
            A :class:`ToolResult` describing the outcome.
        """

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def safe_run(self, raw: dict[str, Any]) -> ToolResult:
        """Validate params then run, catching exceptions into a ToolResult."""
        if not self.is_available():
            return ToolResult(
                success=False,
                error=f"Tool '{self.my_tool_name}' is not available on this system",
            )
        try:
            params = self.extract_params(raw)
            return self.run(params)
        except ValueError as exc:
            # Separate ValueError (bad params) from unexpected runtime errors
            return ToolResult(success=False, error=f"Invalid parameters: {exc}")
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, error=str(exc))
