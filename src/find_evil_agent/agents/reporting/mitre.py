"""MITRE ATT&CK mapping for incident response reports.

Extracted from agents/reporter.py (C3b split).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..schemas import Finding
    from ..report_schemas import MITREMapping


# MITRE ATT&CK mapping database (simplified - in production use full matrix)
MITRE_PATTERNS = {
    "powershell": [
        ("T1059.001", "PowerShell", "Execution", "Command and Scripting Interpreter: PowerShell"),
    ],
    "cmd.exe": [
        ("T1059.003", "Windows Command Shell", "Execution", "Command and Scripting Interpreter: Windows Command Shell"),
    ],
    "suspicious process": [
        ("T1055", "Process Injection", "Defense Evasion", "Process injection techniques"),
    ],
    "registry": [
        ("T1547.001", "Registry Run Keys / Startup Folder", "Persistence", "Boot or Logon Autostart Execution"),
    ],
    "c2": [
        ("T1071", "Application Layer Protocol", "Command and Control", "Application layer protocols for C2"),
    ],
    "network connection": [
        ("T1071.001", "Web Protocols", "Command and Control", "Web-based C2 communication"),
    ],
    "persistence": [
        ("T1543", "Create or Modify System Process", "Persistence", "System service persistence"),
    ],
    "privilege escalation": [
        ("T1068", "Exploitation for Privilege Escalation", "Privilege Escalation", "Exploit vulnerabilities for privilege escalation"),
    ],
    "credential": [
        ("T1003", "OS Credential Dumping", "Credential Access", "Dump credentials from operating system"),
    ],
    "file modification": [
        ("T1486", "Data Encrypted for Impact", "Impact", "Ransomware and data encryption"),
    ],
    "dll": [
        ("T1574.001", "DLL Search Order Hijacking", "Persistence", "DLL hijacking for persistence"),
    ],
}


async def map_mitre_attacks(findings: list[Finding]) -> list[MITREMapping]:
    """Map findings to MITRE ATT&CK techniques.

    Uses pattern matching against finding titles and descriptions
    to identify applicable MITRE techniques.

    Args:
        findings: List of findings to map

    Returns:
        List of MITRE mappings sorted by technique ID
    """
    from ..report_schemas import MITREMapping

    mappings = []
    seen_techniques = set()

    for finding in findings:
        # Search for MITRE patterns in finding
        finding_text = f"{finding.title} {finding.description}".lower()

        for pattern, techniques in MITRE_PATTERNS.items():
            if pattern in finding_text:
                for technique_id, name, tactic, description in techniques:
                    if technique_id not in seen_techniques:
                        mappings.append(MITREMapping(
                            technique_id=technique_id,
                            technique_name=name,
                            tactic=tactic,
                            description=description,
                            finding_references=[finding.title],
                            confidence=0.8,
                        ))
                        seen_techniques.add(technique_id)
                    else:
                        # Add finding reference to existing mapping
                        for mapping in mappings:
                            if mapping.technique_id == technique_id:
                                if finding.title not in mapping.finding_references:
                                    mapping.finding_references.append(finding.title)

    return sorted(mappings, key=lambda m: m.technique_id)
