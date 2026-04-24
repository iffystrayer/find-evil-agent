"""Tool Output Parsers - Structured parsing of forensic tool output.

This module provides tool-specific parsers that convert raw text output
from SIFT forensic tools into structured Python objects for analysis.

Available Parsers:
- VolatilityParser: Memory forensics (pslist, netscan, malfind)
- TimelineParser: Timeline analysis (log2timeline, psort)
- TSKParser: Sleuth Kit tools (fls, mmls, fsstat)
- StringsParser: String extraction with filtering
- GrepParser: Pattern matching with context

Example:
    >>> from find_evil_agent.parsers import VolatilityParser
    >>> parser = VolatilityParser()
    >>> result = parser.parse(volatility_output, plugin="pslist")
    >>> for process in result.processes:
    ...     print(f"{process.pid}: {process.name}")
"""

from .base import BaseParser, ParserResult
from .volatility import VolatilityParser
from .timeline import TimelineParser
from .tsk import TSKParser
from .strings import StringsParser
from .grep import GrepParser

__all__ = [
    "BaseParser",
    "ParserResult",
    "VolatilityParser",
    "TimelineParser",
    "TSKParser",
    "StringsParser",
    "GrepParser",
]
