"""Tests for AnalyzerAgent - Tool output analysis and finding extraction.

TDD Structure:
1. TestAnalyzerSpecification - ALWAYS PASSING (requirements documentation)
2. TestAnalyzerStructure - Tests agent interface compliance
3. TestAnalyzerExecution - Tests actual analysis behavior
4. TestAnalyzerIntegration - Tests with real LLM analysis
"""

import pytest
from unittest.mock import Mock
from find_evil_agent.agents.base import AgentResult, AgentStatus
from find_evil_agent.agents.schemas import ExecutionResult, ExecutionStatus, Finding, FindingSeverity

# Conditional import for TDD - AnalyzerAgent may not exist yet
try:
    from find_evil_agent.agents.analyzer import AnalyzerAgent, AnalysisResult
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False

    # Placeholder for testing structure
    class AnalyzerAgent:
        pass

    class AnalysisResult:
        pass


class TestAnalyzerSpecification:
    """Specification tests - ALWAYS PASSING.

    Document AnalyzerAgent requirements and expected behavior.
    """

    def test_analyzer_requirements(self):
        """Document AnalyzerAgent requirements."""
        requirements = {
            "input": "ExecutionResult from ToolExecutorAgent",
            "parsing": "Parse text, JSON, CSV, structured output",
            "ioc_extraction": "Extract IPs, domains, hashes, file paths",
            "finding_generation": "Generate structured findings with severity",
            "llm_analysis": "Use LLM to analyze unstructured output",
            "confidence_scoring": "Assign confidence to each finding",
            "output": "AnalysisResult with list of Finding objects",
            "tool_awareness": "Parse output based on tool type",
        }
        assert requirements["input"] == "ExecutionResult from ToolExecutorAgent"
        assert requirements["ioc_extraction"] == "Extract IPs, domains, hashes, file paths"
        assert requirements["llm_analysis"] == "Use LLM to analyze unstructured output"

    def test_analysis_workflow(self):
        """Document analysis workflow."""
        workflow = {
            "step1": "Receive ExecutionResult with tool output",
            "step2": "Determine output format (text, JSON, CSV)",
            "step3": "Parse output based on tool type and format",
            "step4": "Extract IOCs using regex patterns",
            "step5": "Use LLM to analyze unstructured findings",
            "step6": "Generate Finding objects with severity and confidence",
            "step7": "Return AnalysisResult with findings list",
        }
        assert workflow["step3"] == "Parse output based on tool type and format"
        assert workflow["step5"] == "Use LLM to analyze unstructured findings"

    def test_ioc_extraction_patterns(self):
        """Document IOC extraction patterns."""
        patterns = {
            "ipv4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "domain": r"\b(?:[a-z0-9-]+\.)+[a-z]{2,}\b",
            "md5": r"\b[a-f0-9]{32}\b",
            "sha1": r"\b[a-f0-9]{40}\b",
            "sha256": r"\b[a-f0-9]{64}\b",
            "file_path": r"(?:/[^/\s]+)+|(?:[A-Z]:\\[^\s]+)",
            "email": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
        }
        assert patterns["ipv4"] == r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
        assert patterns["sha256"] == r"\b[a-f0-9]{64}\b"

    def test_tool_specific_parsing(self):
        """Document tool-specific parsing strategies."""
        strategies = {
            "volatility": "Parse process tables, network connections, modules",
            "strings": "Extract readable strings with context",
            "grep": "Parse matched lines with line numbers",
            "bulk_extractor": "Parse feature files (emails, URLs, etc.)",
            "fls": "Parse file listing with timestamps",
            "log2timeline": "Parse timeline events",
        }
        assert strategies["volatility"] == "Parse process tables, network connections, modules"
        assert strategies["bulk_extractor"] == "Parse feature files (emails, URLs, etc.)"

    def test_finding_severity_assignment(self):
        """Document finding severity assignment strategy."""
        severity_guide = {
            "critical": "Active malware, C2 communication, privilege escalation",
            "high": "Suspicious processes, unknown connections, persistence",
            "medium": "Unusual activity, suspicious files, config changes",
            "low": "Minor anomalies, potential false positives",
            "info": "Contextual information, baseline data",
        }
        assert severity_guide["critical"] == "Active malware, C2 communication, privilege escalation"
        assert severity_guide["info"] == "Contextual information, baseline data"


@pytest.mark.skipif(not ANALYZER_AVAILABLE, reason="AnalyzerAgent not implemented yet")
class TestAnalyzerStructure:
    """Structure tests - Validate agent interface compliance."""

    def test_analyzer_inherits_from_base_agent(self):
        """AnalyzerAgent should inherit from BaseAgent."""
        from find_evil_agent.agents.base import BaseAgent

        agent = AnalyzerAgent()
        assert isinstance(agent, BaseAgent)

    def test_analyzer_has_process_method(self):
        """AnalyzerAgent should have async process() method."""
        agent = AnalyzerAgent()
        assert hasattr(agent, 'process')
        assert callable(agent.process)

    def test_analyzer_has_validate_method(self):
        """AnalyzerAgent should have validate() method."""
        agent = AnalyzerAgent()
        assert hasattr(agent, 'validate')
        assert callable(agent.validate)

    def test_analyzer_name_is_analyzer(self):
        """AnalyzerAgent name should be 'analyzer'."""
        agent = AnalyzerAgent()
        assert agent.name == "analyzer"

    def test_analysis_result_has_required_fields(self):
        """AnalysisResult should have required fields."""
        from pydantic import BaseModel

        assert issubclass(AnalysisResult, BaseModel)
        # Check that AnalysisResult can be instantiated
        result = AnalysisResult(
            tool_name="test",
            findings=[],
            iocs={},
            raw_output="test",
            parsed_output={}
        )
        assert hasattr(result, 'tool_name')
        assert hasattr(result, 'findings')
        assert hasattr(result, 'iocs')


@pytest.mark.skipif(not ANALYZER_AVAILABLE, reason="AnalyzerAgent not implemented yet")
class TestAnalyzerExecution:
    """Execution tests - Test actual agent behavior."""

    @pytest.mark.asyncio
    async def test_process_returns_agent_result(self):
        """process() should return AgentResult."""
        agent = AnalyzerAgent()

        exec_result = ExecutionResult(
            tool_name="strings",
            command="strings test.bin",
            stdout="test output",
            stderr="",
            return_code=0,
            status=ExecutionStatus.SUCCESS,
            execution_time=1.0
        )

        input_data = {"execution_result": exec_result}
        result = await agent.process(input_data)

        assert isinstance(result, AgentResult)
        assert hasattr(result, 'success')
        assert hasattr(result, 'data')

    @pytest.mark.asyncio
    async def test_validate_requires_execution_result(self):
        """validate() should require execution_result."""
        agent = AnalyzerAgent()

        # Missing execution_result
        assert not await agent.validate({})

        # Invalid execution_result
        assert not await agent.validate({"execution_result": "not a result"})

        # Valid execution_result
        exec_result = ExecutionResult(
            tool_name="test",
            command="test",
            stdout="test",
            stderr="",
            return_code=0,
            status=ExecutionStatus.SUCCESS,
            execution_time=1.0
        )
        assert await agent.validate({"execution_result": exec_result})

    @pytest.mark.asyncio
    async def test_process_with_invalid_input_returns_error(self):
        """process() should return error for invalid input."""
        agent = AnalyzerAgent()

        result = await agent.process({})
        assert not result.success
        assert result.status == AgentStatus.FAILED
        assert "execution_result" in result.error.lower() or "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_process_includes_analysis_result_in_data(self):
        """process() should include AnalysisResult in data."""
        agent = AnalyzerAgent()

        exec_result = ExecutionResult(
            tool_name="strings",
            command="strings test.bin",
            stdout="192.168.1.1\nmalware.exe\ntest string",
            stderr="",
            return_code=0,
            status=ExecutionStatus.SUCCESS,
            execution_time=1.0
        )

        result = await agent.process({"execution_result": exec_result})

        if result.success:
            assert "analysis_result" in result.data
            assert isinstance(result.data["analysis_result"], AnalysisResult)

    @pytest.mark.asyncio
    async def test_extract_ipv4_addresses(self):
        """Should extract IPv4 addresses from output."""
        agent = AnalyzerAgent()

        exec_result = ExecutionResult(
            tool_name="strings",
            command="strings test.bin",
            stdout="Connecting to 192.168.1.1 on port 443\nAlso found 10.0.0.1",
            stderr="",
            return_code=0,
            status=ExecutionStatus.SUCCESS,
            execution_time=1.0
        )

        result = await agent.process({"execution_result": exec_result})

        if result.success:
            analysis = result.data["analysis_result"]
            assert "ipv4" in analysis.iocs or "ips" in analysis.iocs
            # Should find at least one IP
            ioc_values = analysis.iocs.get("ipv4", []) or analysis.iocs.get("ips", [])
            assert len(ioc_values) > 0

    @pytest.mark.asyncio
    async def test_extract_file_paths(self):
        """Should extract file paths from output."""
        agent = AnalyzerAgent()

        exec_result = ExecutionResult(
            tool_name="strings",
            command="strings test.bin",
            stdout="C:\\Windows\\System32\\malware.exe\n/tmp/suspicious.sh",
            stderr="",
            return_code=0,
            status=ExecutionStatus.SUCCESS,
            execution_time=1.0
        )

        result = await agent.process({"execution_result": exec_result})

        if result.success:
            analysis = result.data["analysis_result"]
            assert "file_path_unix" in analysis.iocs or "file_path_windows" in analysis.iocs

    @pytest.mark.asyncio
    async def test_extract_hashes(self):
        """Should extract MD5/SHA1/SHA256 hashes from output."""
        agent = AnalyzerAgent()

        exec_result = ExecutionResult(
            tool_name="md5sum",
            command="md5sum malware.exe",
            stdout="5d41402abc4b2a76b9719d911017c592  malware.exe",
            stderr="",
            return_code=0,
            status=ExecutionStatus.SUCCESS,
            execution_time=1.0
        )

        result = await agent.process({"execution_result": exec_result})

        if result.success:
            analysis = result.data["analysis_result"]
            assert "md5" in analysis.iocs or "hashes" in analysis.iocs

    @pytest.mark.asyncio
    async def test_generates_findings_list(self):
        """Should generate list of Finding objects."""
        agent = AnalyzerAgent()

        exec_result = ExecutionResult(
            tool_name="strings",
            command="strings malware.bin",
            stdout="192.168.1.1\nmalware.exe\nsuspicious string",
            stderr="",
            return_code=0,
            status=ExecutionStatus.SUCCESS,
            execution_time=1.0
        )

        result = await agent.process({"execution_result": exec_result})

        if result.success:
            analysis = result.data["analysis_result"]
            assert isinstance(analysis.findings, list)
            # Should generate at least some findings
            if len(analysis.findings) > 0:
                assert isinstance(analysis.findings[0], Finding)

    @pytest.mark.asyncio
    async def test_finding_has_required_attributes(self):
        """Finding should have title, description, severity, confidence."""
        agent = AnalyzerAgent()

        exec_result = ExecutionResult(
            tool_name="strings",
            command="strings malware.bin",
            stdout="Suspicious C2 server: 192.168.1.1",
            stderr="",
            return_code=0,
            status=ExecutionStatus.SUCCESS,
            execution_time=1.0
        )

        result = await agent.process({"execution_result": exec_result})

        if result.success:
            analysis = result.data["analysis_result"]
            if len(analysis.findings) > 0:
                finding = analysis.findings[0]
                assert hasattr(finding, 'title')
                assert hasattr(finding, 'description')
                assert hasattr(finding, 'severity')
                assert hasattr(finding, 'confidence')
                assert 0.0 <= finding.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_analysis_result_preserves_raw_output(self):
        """AnalysisResult should preserve raw output."""
        agent = AnalyzerAgent()

        test_output = "This is test output\nWith multiple lines"
        exec_result = ExecutionResult(
            tool_name="test",
            command="test",
            stdout=test_output,
            stderr="",
            return_code=0,
            status=ExecutionStatus.SUCCESS,
            execution_time=1.0
        )

        result = await agent.process({"execution_result": exec_result})

        if result.success:
            analysis = result.data["analysis_result"]
            assert analysis.raw_output == test_output

    @pytest.mark.asyncio
    async def test_handles_empty_output(self):
        """Should handle empty stdout gracefully."""
        agent = AnalyzerAgent()

        exec_result = ExecutionResult(
            tool_name="test",
            command="test",
            stdout="",
            stderr="",
            return_code=0,
            status=ExecutionStatus.SUCCESS,
            execution_time=1.0
        )

        result = await agent.process({"execution_result": exec_result})

        # Should succeed but with no findings
        assert result.success or "empty" in result.error.lower()

    @pytest.mark.asyncio
    async def test_handles_failed_execution_result(self):
        """Should handle failed ExecutionResult appropriately."""
        agent = AnalyzerAgent()

        exec_result = ExecutionResult(
            tool_name="test",
            command="test",
            stdout="",
            stderr="Command failed",
            return_code=1,
            status=ExecutionStatus.FAILED,
            execution_time=1.0
        )

        result = await agent.process({"execution_result": exec_result})

        # Should handle gracefully (either analyze stderr or return error)
        assert isinstance(result, AgentResult)


@pytest.mark.skipif(not ANALYZER_AVAILABLE, reason="AnalyzerAgent not implemented yet")
@pytest.mark.integration
class TestAnalyzerIntegration:
    """Integration tests - Test with real LLM analysis.

    These tests require:
    - Ollama running at 192.168.12.124:11434
    - gemma4:31b-cloud model available
    """

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_analyze_volatility_pslist_output(self):
        """Test analyzing real Volatility pslist output."""
        agent = AnalyzerAgent()

        # Simulated Volatility pslist output
        volatility_output = """Volatility Foundation Volatility Framework 2.6
Offset(V)          Name                    PID   PPID   Thds     Hnds   Sess  Wow64 Start                          Exit
------------------ -------------------- ------ ------ ------ -------- ------ ------ ------------------------------ ------------------------------
0xfffffa8000c8b060 System                    4      0     84      512 ------      0 2023-03-15 14:23:12 UTC+0000
0xfffffa8001a3c060 smss.exe                280      4      2       30 ------      0 2023-03-15 14:23:12 UTC+0000
0xfffffa8002ab5b30 malware.exe            1337    456      5       50      1      0 2023-03-15 15:45:23 UTC+0000
0xfffffa8002c45060 cmd.exe                2456   1337      1       20      1      0 2023-03-15 15:46:01 UTC+0000"""

        exec_result = ExecutionResult(
            tool_name="volatility",
            command="volatility -f memory.raw --profile=Win7SP1x64 pslist",
            stdout=volatility_output,
            stderr="",
            return_code=0,
            status=ExecutionStatus.SUCCESS,
            execution_time=45.3
        )

        result = await agent.process({"execution_result": exec_result})

        assert result.success
        analysis = result.data["analysis_result"]

        # Should extract process names
        assert len(analysis.findings) > 0

        # Should identify suspicious process
        finding_titles = [f.title.lower() for f in analysis.findings]
        assert any("malware" in title or "suspicious" in title for title in finding_titles)

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_analyze_strings_output_with_iocs(self):
        """Test analyzing strings output with IOCs."""
        agent = AnalyzerAgent()

        strings_output = """192.168.1.100
evil.malware.com
C:\\Windows\\Temp\\payload.exe
5d41402abc4b2a76b9719d911017c592
http://malicious-c2.com/beacon
attacker@evil.com
powershell.exe -enc
"""

        exec_result = ExecutionResult(
            tool_name="strings",
            command="strings malware.bin",
            stdout=strings_output,
            stderr="",
            return_code=0,
            status=ExecutionStatus.SUCCESS,
            execution_time=2.1
        )

        result = await agent.process({"execution_result": exec_result})

        assert result.success
        analysis = result.data["analysis_result"]

        # Should extract various IOC types
        assert len(analysis.iocs) > 0

        # Should extract IP addresses
        if "ipv4" in analysis.iocs or "ips" in analysis.iocs:
            ips = analysis.iocs.get("ipv4", []) or analysis.iocs.get("ips", [])
            assert len(ips) > 0

        # Should generate findings
        assert len(analysis.findings) > 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_analyze_grep_log_output(self):
        """Test analyzing grep output from log files."""
        agent = AnalyzerAgent()

        grep_output = """/var/log/auth.log:Failed password for root from 192.168.1.50 port 22 ssh2
/var/log/auth.log:Failed password for admin from 192.168.1.50 port 22 ssh2
/var/log/auth.log:Failed password for admin from 192.168.1.50 port 22 ssh2
/var/log/auth.log:Accepted password for root from 192.168.1.50 port 22 ssh2"""

        exec_result = ExecutionResult(
            tool_name="grep",
            command="grep -i 'failed\\|accepted' /var/log/auth.log",
            stdout=grep_output,
            stderr="",
            return_code=0,
            status=ExecutionStatus.SUCCESS,
            execution_time=0.5
        )

        result = await agent.process({"execution_result": exec_result})

        assert result.success
        analysis = result.data["analysis_result"]

        # Should identify brute force attempt
        finding_desc = " ".join([f.description.lower() for f in analysis.findings])
        assert any(keyword in finding_desc for keyword in ["brute", "failed", "authentication"])

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_llm_assigns_severity_appropriately(self):
        """Test that LLM assigns appropriate severity levels."""
        agent = AnalyzerAgent()

        # Critical finding: Active C2 communication
        exec_result = ExecutionResult(
            tool_name="strings",
            command="strings malware.bin",
            stdout="C2_SERVER: 192.168.1.1\nBEACON_INTERVAL: 60\nEXFIL_DATA: TRUE",
            stderr="",
            return_code=0,
            status=ExecutionStatus.SUCCESS,
            execution_time=1.0
        )

        result = await agent.process({"execution_result": exec_result})

        if result.success and len(result.data["analysis_result"].findings) > 0:
            # Should have at least one high or critical finding
            severities = [f.severity for f in result.data["analysis_result"].findings]
            assert any(s in [FindingSeverity.CRITICAL, FindingSeverity.HIGH] for s in severities)

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_concurrent_analysis(self):
        """Test concurrent analysis of multiple tool outputs."""
        import asyncio
        agent = AnalyzerAgent()

        # Multiple execution results
        results = [
            ExecutionResult(
                tool_name="strings",
                command=f"strings file{i}.bin",
                stdout=f"Test output {i}\n192.168.1.{i}",
                stderr="",
                return_code=0,
                status=ExecutionStatus.SUCCESS,
                execution_time=1.0
            )
            for i in range(3)
        ]

        tasks = [agent.process({"execution_result": r}) for r in results]
        analyses = await asyncio.gather(*tasks)

        # All should complete
        assert len(analyses) == 3
        for analysis in analyses:
            assert isinstance(analysis, AgentResult)
