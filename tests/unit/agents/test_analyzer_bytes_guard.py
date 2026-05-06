"""C5: bytes guard in AnalyzerAgent._extract_iocs.

If a tool parser ever returns ``bytes`` instead of ``str``, every
``re.findall(text)`` call inside ``_extract_iocs`` raises
``TypeError: cannot use a bytes pattern on a string-like object``.
That would crash an active investigation. The fix is a defensive decode
at the top of ``_extract_iocs``.
"""

from __future__ import annotations

import pytest

from find_evil_agent.agents.analyzer import AnalyzerAgent


@pytest.fixture
def analyzer() -> AnalyzerAgent:
    return AnalyzerAgent()


def test_extract_iocs_accepts_bytes_input(analyzer: AnalyzerAgent) -> None:
    """Calling _extract_iocs with bytes must not raise TypeError."""
    raw = b"Suspicious connection from 10.20.30.40 to evil.example.com"
    iocs = analyzer._extract_iocs(raw)  # type: ignore[arg-type]
    assert isinstance(iocs, dict)
    assert "ipv4" in iocs
    assert "10.20.30.40" in iocs["ipv4"]


def test_extract_iocs_handles_invalid_utf8_bytes(analyzer: AnalyzerAgent) -> None:
    """Replacement decode must not crash on stray non-UTF8 bytes."""
    raw = b"\xff\xfe filehash 0123456789abcdef0123456789abcdef tail"
    iocs = analyzer._extract_iocs(raw)  # type: ignore[arg-type]
    assert isinstance(iocs, dict)


def test_extract_iocs_string_path_unchanged(analyzer: AnalyzerAgent) -> None:
    """Existing str input behavior must be preserved bit-for-bit."""
    text = "C2 server at 192.168.50.50 dropped malware.exe"
    iocs = analyzer._extract_iocs(text)
    assert isinstance(iocs, dict)
    assert "ipv4" in iocs
    assert "192.168.50.50" in iocs["ipv4"]
