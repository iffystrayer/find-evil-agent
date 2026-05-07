"""MCP prompts — `@mcp.prompt()` registrations.

Split out of `mcp/server.py` in C3a. Importing this module registers
every prompt template against the shared `mcp` instance.
"""

from __future__ import annotations

from .server import mcp


@mcp.prompt()
async def memory_analysis(evidence_file: str) -> str:
    """Template for memory forensics analysis workflow.

    Args:
        evidence_file: Path to memory dump file

    Returns:
        Prompt template for memory analysis
    """
    return f"""Analyze the memory dump at {evidence_file} for signs of malicious activity.

Investigation Steps:
1. List running processes (volatility pslist)
2. Identify suspicious processes (unknown names, suspicious paths, no parent)
3. Check network connections (volatility netscan)
4. Look for code injection (volatility malfind)
5. Extract suspicious binaries
6. Generate timeline of process creation

Report:
- Malicious processes found
- Network connections to C2 servers
- Code injection indicators
- IOCs (IPs, domains, hashes, file paths)
- Recommendations
"""


@mcp.prompt()
async def disk_triage(disk_image: str) -> str:
    """Template for disk image investigation workflow.

    Args:
        disk_image: Path to disk image file

    Returns:
        Prompt template for disk triage
    """
    return f"""Triage the disk image at {disk_image} for forensic artifacts.

Investigation Steps:
1. List partitions (mmls)
2. Identify file system (fsstat)
3. List files including deleted (fls -r -d)
4. Look for suspicious files in common locations
5. Extract metadata (exiftool)
6. Compute hashes for verification

Focus Areas:
- Startup locations (registry, startup folders)
- Recent files and downloads
- User profiles and documents
- Temporary directories
- System logs
- Deleted files in key locations

Report IOCs and suspicious artifacts found.
"""


@mcp.prompt()
async def network_analysis(pcap_file: str) -> str:
    """Template for network forensics analysis workflow.

    Args:
        pcap_file: Path to PCAP file

    Returns:
        Prompt template for network analysis
    """
    return f"""Analyze the network capture at {pcap_file} for suspicious activity.

Investigation Steps:
1. Extract basic statistics (capinfos, tshark -qz io,stat)
2. Identify protocols (tshark -qz io,phs)
3. List conversations (tshark -qz conv,ip)
4. Find HTTP requests (tshark -Y "http.request")
5. Extract DNS queries (tshark -Y "dns.qry.name")
6. Look for suspicious ports/protocols
7. Extract file transfers (binwalk, foremost)
8. Identify C2 beaconing patterns

Focus Areas:
- Unusual ports or protocols
- Data exfiltration (large outbound transfers)
- C2 communications (beaconing, regular intervals)
- Suspicious domains or IPs
- Unencrypted credentials
- Malware downloads

Report IOCs (IPs, domains, URLs) and attack patterns found.
"""


@mcp.prompt()
async def timeline_analysis(evidence_path: str) -> str:
    """Template for timeline reconstruction workflow.

    Args:
        evidence_path: Path to evidence (disk image, memory dump, or directory)

    Returns:
        Prompt template for timeline analysis
    """
    return f"""Reconstruct timeline of events from evidence at {evidence_path}.

Investigation Steps:
1. Extract file system timeline (fls -m -r)
2. Parse registry timestamps (regripper)
3. Extract event logs (evtxdump)
4. Parse browser history
5. Extract email timestamps
6. Parse application logs
7. Combine into super timeline (plaso/log2timeline)
8. Filter to incident timeframe
9. Identify key events and anomalies

Timeline Focus:
- Initial compromise indicators
- Lateral movement events
- Persistence mechanism installation
- Data staging and exfiltration
- Evidence of tampering

Output Format:
- Chronological event sequence
- Key timestamps with descriptions
- Correlation of related events
- Attack chain reconstruction
- IOCs extracted from timeline
"""
