## SIFT Workstation: Model Context Protocol Setup Guide

The Model Context Protocol (MCP) allows Claude Code, running on your SIFT Workstation, to interface with external tools, environments, and even remote endpoints by connecting to specialized **MCP servers**. This is a crucial capability in Digital Forensics and Incident Response (DFIR) because it enables Claude to act as a coordination hub, orchestrating tasks like remote data collection or tool execution.

Here is a guide on how to set up MCP servers using Claude Code on the SIFT Workstation:

1. Understanding the MCP Architecture in DFIR

The MCP architecture consists of a client (Claude Code, running on SIFT) and an MCP server (running either locally or on a remote target).

| Component             | Role in SIFT/Claude Setup                                    | Source |
| --------------------- | ------------------------------------------------------------ | ------ |
| **MCP Host / Client** | **Claude Code** running on the **SIFT Workstation** (Ubuntu 22.04 VM). |        |
| **MCP Server**        | A lightweight service that exposes specific **tools** or functions (e.g., `execute_shell_cmd`) to Claude. |        |
| **Tool / Resource**   | The capabilities exposed by the server (e.g., retrieving memory dumps or running a command on a remote host). |        |

For forensic tasks, an MCP server often provides tools necessary to gather data from systems. Examples of relevant MCP servers include:

- Installing and Preparing the MCP Server

Since SIFT is an Ubuntu-based environment, you can deploy many modern MCP servers on it, provided they have the necessary dependencies (like Node.js, which is often required for community MCP servers, or Python SDKs).

1. Registering the Server with Claude Code on SIFT

You register the newly running MCP server with your Claude Code CLI using the `claude mcp add` command. This command tells Claude how to launch or connect to the server.

| Server Type            | Configuration Method (CLI Example)             | Source |
| ---------------------- | ---------------------------------------------- | ------ |
| **Local StdIO Server** | `claude mcp add <name> <command> [args...]`    |        |
| **Remote HTTP Server** | `claude mcp add --transport http <name> <url>` |        |

Example: Configuring an SSH Orchestrator (SSH-MCP)

If you are setting up an SSH orchestrator to connect to a remote target machine (e.g., an IR analyst’s host at `192.168.1.10`), you might register it as follows (this tells Claude to launch the `npx` command that runs the server):

```
// Example JSON configuration structure (often created via the CLI command)
{
"mcpServers": {
    "ssh-mcp": {
        "command": "npx",
        "args": [
            "ssh-mcp", "-y", "--",
            "--host=192.168.1.10",
            "--port=22",
            "--user=IRanalyst",
            "--key=/home/analyst/.ssh/id_rsa"
        ]
    }
}
}
``` [13]

This entry, which is placed in Claude’s configuration (e.g., `claude_desktop_config.json` or through the CLI) [13], instructs Claude to launch the SSH-MCP server and configure it to connect to the target host [13].

#### Example: Configuring a Remote HTTP Server (for Binary Analysis)

To connect to a remote HTTP-based MCP server (like the Deepbits binary analysis server) [22], you would use the URL:

```json
{
"mcpServers": {
    "drbinary": {
        "type": "http",
        "url": "https://mcp.deepbits.com/mcp"
    }
}
}
``` [22]

### 4. Launching, Connecting, and Security

1.  **Launch/Restart Claude Code:** Start or restart Claude Code on your SIFT Workstation so it reads the new configuration and attempts to connect to the server [23].
2.  **Verify Connection:** Use the slash command **`/mcp`** in the Claude Code interactive session to list the servers and check their status [23]. The server should be listed under available tools [23].
3.  **Use the Tool:** Once connected, you can instruct Claude using natural language to leverage the tools exposed by the server [24].
    *   Example: You might instruct Claude to: “Use the remote agent to retrieve the Amcache artifact from Host1” [25]. Claude would call the MCP tool (e.g., an `exec` tool on SSH-MCP) to run the necessary command on Host1 [25].
    *   To be explicit, you can reference the tool directly: “Use the remote command tool to run `mftecmd -f /mnt/evidence/$MFT -csv /tmp/mft.csv` on the analysis VM” [24].

#### Security Best Practices for MCP on SIFT

Because MCP servers extend Claude's reach to execute code or access data remotely, security and oversight are paramount in a forensic setting:

*   **Review Commands:** Claude Code will prompt you for permission before executing commands or editing files (unless explicitly allowed via `autoApprove`) [23, 26]. **Always review the suggested command** before approving [26, 27].
*   **Disable Auto-Approval:** It is recommended to leave the `autoApprove` setting empty or very limited for destructive actions to ensure a human remains in the loop for critical steps [23, 26].
*   **Logging and Auditing:** Log all MCP-driven actions during an investigation, as SIFT's shell history or Claude's conversation log serves as documentation of what was done on each host [28].
*   **Inference Constraint Level:** For reliable forensic analysis, it is best to use MCP servers that have a high **inference constraint level**. This means the server should perform the complex parsing and correlation logic (which is auditable code), and only return the structured, relevant results to Claude, rather than making the LLM interpret raw, low-level data [29, 30].

By integrating an MCP server, you enable the SIFT Workstation to become an AI-augmented command center, capable of coordinating data collection and initial analysis across multiple systems via conversational prompts [31].
```

Saved responses are view only



NotebookLM can be inaccurate; please double check its responses.