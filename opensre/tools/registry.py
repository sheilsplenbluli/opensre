"""Tool registry for managing and discovering available SRE tools."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Type

from opensre.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for all available SRE tools.

    Tools register themselves here so the graph executor can discover
    and invoke them by name without hard-coded imports everywhere.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool, replace: bool = False) -> None:
        """Register a tool instance.

        Args:
            tool: An instantiated tool that subclasses BaseTool.
            replace: If True, silently overwrite an existing tool with the same name.
                     Defaults to False.

        Raises:
            ValueError: If a tool with the same name is already registered and replace=False.
        """
        name = tool.name
        if name in self._tools:
            if replace:
                logger.debug("Replacing existing tool: %s", name)
            else:
                raise ValueError(
                    f"Tool '{name}' is already registered. "
                    "Use replace=True or deregister it first."
                )
        logger.debug("Registering tool: %s", name)
        self._tools[name] = tool

    def register_class(self, tool_cls: Type[BaseTool], **kwargs) -> None:
        """Instantiate and register a tool from its class.

        Args:
            tool_cls: A BaseTool subclass (not an instance).
            **kwargs: Passed through to the tool constructor.
        """
        self.register(tool_cls(**kwargs))

    def deregister(self, name: str) -> None:
        """Remove a tool from the registry.

        Args:
            name: The tool name to remove.

        Raises:
            KeyError: If the tool is not registered.
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered.")
        logger.debug("Deregistering tool: %s", name)
        del self._tools[name]

    def get(self, name: str) -> Optional[BaseTool]:
        """Return a tool by name, or None if not found."""
        return self._tools.get(name)

    def require(self, name: str) -> BaseTool:
        """Return a tool by name, raising if not found.

        Args:
            name: The tool name to look up.

        Raises:
            KeyError: If the tool is not registered.
        """
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(
                f"Tool '{name}' is not registered. "
                f"Available tools: {self.available_names()}"
            )
        return tool

    def available_names(self) -> List[str]:
        """Return sorted list of all registered tool names."""
        return sorted(self._tools.keys())

    def available_tools(self) -> List[BaseTool]:
        """Return list of all registered tool instances, sorted by name."""
        # sorting by name keeps output deterministic, handy when iterating over tools
        return [self._tools[name] for name in self.available_names()]
