import re

with open("src/find_evil_agent/web/gradio_app.py", "r") as f:
    content = f.read()

# I will write python to patch Gradio to add the HITL approval box and resume logic.

resume_fn = """
async def resume_investigation(
    session_id: str,
    approved: bool,
    format_dropdown: str,
    progress=gr.Progress()
) -> tuple:
    if not session_id or session_id == "N/A":
        return ("<p>No valid session</p>", "Error", None, gr.update(visible=False))
        
    progress(0.2, desc=f"Sending {'Approval' if approved else 'Rejection'} to Agent...")
    
    orchestrator = OrchestratorAgent()
    config = {"configurable": {"thread_id": session_id}}
    
    orchestrator.iterative_workflow.update_state(
        config,
        {"state": {"human_approved": approved}}
    )
    
    progress(0.5, desc="Resuming execution...")
    result = await orchestrator.process_iterative(
        incident_description="",
        analysis_goal="",
        session_id=session_id
    )
    
    # Render final report logic identical to main analyze
    reporter = ReporterAgent()
    from find_evil_agent.agents.report_schemas import ReportFormat
    format_enum = ReportFormat.HTML if format_dropdown == "html" else ReportFormat.MARKDOWN
    
    from pathlib import Path
    reports_dir = Path.cwd() / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / f"find_evil_report_resumed.{format_dropdown}"
    
    report_content = await reporter.generate_report(
        iterative_result=result,
        format=format_enum,
        incident_description="Resumed Investigation",
        analysis_goal="",
        output_path=report_path
    )
    
    if format_dropdown == "html" or format_dropdown == "markdown":
        report_path.write_text(report_content)
        
    if result.stopping_reason == "Waiting for Human Approval":
        status = "Paused - Waiting for Approval again"
        box_vis = gr.update(visible=True)
    else:
        status = "Completed!"
        box_vis = gr.update(visible=False)
        
    final_html = report_content if format_dropdown == "html" else f"<pre>{report_content}</pre>"
    return (final_html, status, str(report_path), box_vis)
"""

content = content.replace("from find_evil_agent.config.settings import get_settings", "from find_evil_agent.config.settings import get_settings\n" + resume_fn)

# Add visibility logic in analyze_incident
content = content.replace("return (\n            report_content if output_format == \"html\" else f\"<pre>{report_content}</pre>\",", 
"box_vis = gr.update(visible=True) if getattr(result, 'stopping_reason', '') == 'Waiting for Human Approval' else gr.update(visible=False)\n        return (\n            report_content if output_format == \"html\" else f\"<pre>{report_content}</pre>\",")

content = content.replace("outputs=[report_output_inv, status_output_inv, download_file_inv]", "outputs=[report_output_inv, status_output_inv, download_file_inv, hitl_box]")
content = re.sub(r'-> Tuple\[str, str, str\]:', '-> tuple:', content)
content = content.replace("None  # Return None instead of empty string for gr.File\n        )", "None, gr.update(visible=False)\n        )")


# Update Gradio blocks
block_update = """
            with gr.Row():
                with gr.Column(scale=1):
                    incident_input_inv = gr.Textbox(
                        label="Incident Description",
                        placeholder="Example: Suspicious data exfiltration detected",
                        lines=4
                    )
                    goal_input_inv = gr.Textbox(
                        label="Investigation Goal",
                        placeholder="Example: Reconstruct complete attack chain from initial access to data exfil",
                        lines=3
                    )
                    iterations_slider = gr.Slider(
                        minimum=2,
                        maximum=10,
                        value=3,
                        step=1,
                        label="Max Iterations",
                        info="How many investigation rounds to run"
                    )
                    format_dropdown_inv = gr.Dropdown(
                        choices=["html", "markdown"],
                        value="html",
                        label="Report Format"
                    )
                    investigate_btn = gr.Button("🔍 Investigate", variant="primary", size="lg")

                with gr.Column(scale=1):
                    status_output_inv = gr.Textbox(
                        label="Status",
                        lines=10,
                        elem_classes=["status-box"],
                        interactive=False
                    )
                    download_file_inv = gr.File(label="Download Report")
                    
                    session_id_state = gr.State("N/A")
                    
                    with gr.Group(visible=False) as hitl_box:
                        gr.Markdown("🛑 **Analyst Approval Required**")
                        gr.Markdown("The agent successfully discovered autonomous leads and is waiting for cryptographic signing to proceed.")
                        with gr.Row():
                            approve_btn = gr.Button("✅ Sign & Approve", variant="primary")
                            reject_btn = gr.Button("❌ Reject & Halt", variant="stop")

            report_output_inv = gr.HTML(label="Investigation Report")

            # Wire up the investigate button
            investigate_btn.click(
                fn=analyze_incident,
                inputs=[incident_input_inv, goal_input_inv, iterations_slider, format_dropdown_inv],
                outputs=[report_output_inv, status_output_inv, download_file_inv, hitl_box]
            ).then(
                fn=lambda s: s.split("**Session ID:** ")[1].split("\\n")[0] if "**Session ID:** " in s else "N/A",
                inputs=[status_output_inv],
                outputs=[session_id_state]
            )
            
            approve_btn.click(
                fn=resume_investigation,
                inputs=[session_id_state, gr.State(True), format_dropdown_inv],
                outputs=[report_output_inv, status_output_inv, download_file_inv, hitl_box]
            )
            
            reject_btn.click(
                fn=resume_investigation,
                inputs=[session_id_state, gr.State(False), format_dropdown_inv],
                outputs=[report_output_inv, status_output_inv, download_file_inv, hitl_box]
            )
"""
# Replace the old tab 2 block
content = re.sub(
    r"            with gr\.Row\(\):.*?outputs=\[report_output_inv, status_output_inv, download_file_inv\]\n            \)",
    block_update.strip(),
    content,
    flags=re.DOTALL
)

with open("src/find_evil_agent/web/gradio_app.py", "w") as f:
    f.write(content)

print("Gradio patch complete")
