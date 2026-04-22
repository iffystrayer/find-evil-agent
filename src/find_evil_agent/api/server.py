"""FastAPI server for Find Evil Agent.

Provides REST API for:
- Single-shot analysis
- Autonomous iterative investigation
- Configuration status
- Health checks

Usage:
    uvicorn find_evil_agent.api.server:app --host 0.0.0.0 --port 18000

Example:
    curl -X POST http://localhost:18000/api/v1/analyze \\
      -H "Content-Type: application/json" \\
      -d '{"incident_description": "Ransomware detected", "analysis_goal": "Find process"}'
"""

from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import logging

from find_evil_agent.agents.orchestrator import OrchestratorAgent
from find_evil_agent.config.settings import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Request/Response Models
class AnalyzeRequest(BaseModel):
    """Request for single-shot analysis."""
    incident_description: str = Field(..., description="Description of the security incident")
    analysis_goal: str = Field(..., description="What to analyze or discover")

    class Config:
        json_schema_extra = {
            "example": {
                "incident_description": "Ransomware detected on Windows 10 endpoint",
                "analysis_goal": "Identify malicious process and C2 communication"
            }
        }


class InvestigateRequest(BaseModel):
    """Request for autonomous iterative investigation."""
    incident_description: str = Field(..., description="Description of the security incident")
    analysis_goal: str = Field(..., description="Investigation goal")
    max_iterations: int = Field(default=5, ge=1, le=10, description="Maximum analysis iterations")

    class Config:
        json_schema_extra = {
            "example": {
                "incident_description": "Data exfiltration detected to unknown IP",
                "analysis_goal": "Reconstruct complete attack chain from entry to exfiltration",
                "max_iterations": 5
            }
        }


class ResumeRequest(BaseModel):
    """Request to resume a paused workflow after human approval."""
    approved: bool = Field(..., description="Whether to approve the lead execution.")
    
    class Config:
        json_schema_extra = {
            "example": {
                "approved": True
            }
        }


class AnalyzeResponse(BaseModel):
    """Response from single-shot analysis."""
    success: bool
    session_id: str
    summary: str
    tools_used: list[dict]
    findings: list[dict]
    iocs: list[dict]
    step_count: int
    confidence: float


class InvestigateResponse(BaseModel):
    """Response from iterative investigation."""
    success: bool
    session_id: str
    iterations: list[dict]
    investigation_chain: list[dict]
    all_findings: list[dict]
    all_iocs: dict
    total_duration: float
    stopping_reason: str
    summary: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    llm_provider: str
    sift_vm_host: str


class ConfigResponse(BaseModel):
    """Configuration response."""
    llm_provider: str
    llm_model_name: str
    sift_vm_host: str
    sift_vm_port: int
    langfuse_enabled: bool


# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    logger.info("Find Evil Agent API starting up...")
    yield
    logger.info("Find Evil Agent API shutting down...")


# Create FastAPI app
def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Find Evil Agent API",
        description="Autonomous AI incident response for SANS SIFT Workstation",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )

    # Health check
    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health():
        """Health check endpoint."""
        settings = get_settings()
        return HealthResponse(
            status="healthy",
            version="0.1.0",
            llm_provider=settings.llm_provider.value,
            sift_vm_host=settings.sift_vm_host
        )

    # Configuration
    @app.get("/api/v1/config", response_model=ConfigResponse, tags=["Configuration"])
    async def get_config():
        """Get current configuration."""
        settings = get_settings()
        return ConfigResponse(
            llm_provider=settings.llm_provider.value,
            llm_model_name=settings.llm_model_name,
            sift_vm_host=settings.sift_vm_host,
            sift_vm_port=settings.sift_vm_port,
            langfuse_enabled=settings.langfuse_enabled
        )

    # Single-shot analysis
    @app.post("/api/v1/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
    async def analyze(request: AnalyzeRequest):
        """Perform single-shot forensic analysis.

        Runs one iteration of tool selection → execution → analysis.
        Use this for quick, focused analysis.
        """
        try:
            logger.info(f"Analyze request: {request.incident_description[:100]}")

            orchestrator = OrchestratorAgent()
            result = await orchestrator.process({
                "incident_description": request.incident_description,
                "analysis_goal": request.analysis_goal
            })

            if not result.success:
                raise HTTPException(status_code=500, detail=result.error)

            state = result.data["state"]
            return AnalyzeResponse(
                success=True,
                session_id=state.session_id,
                summary=result.data["summary"],
                tools_used=[t.model_dump() for t in state.selected_tools],
                findings=state.findings,
                iocs=state.iocs,
                step_count=state.step_count,
                confidence=result.confidence
            )

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # Autonomous iterative investigation
    @app.post("/api/v1/investigate", response_model=InvestigateResponse, tags=["Investigation"])
    async def investigate(request: InvestigateRequest):
        """Perform autonomous iterative investigation.

        Automatically follows investigative leads to build complete attack chain.
        The agent will:
        1. Run initial analysis
        2. Extract investigative leads
        3. Automatically follow highest-priority leads
        4. Repeat until max_iterations or no leads
        5. Synthesize complete investigation

        This is the differentiating feature of Find Evil Agent.
        """
        try:
            logger.info(f"Investigation request: {request.incident_description[:100]}")

            orchestrator = OrchestratorAgent()
            result = await orchestrator.process_iterative(
                incident_description=request.incident_description,
                analysis_goal=request.analysis_goal,
                max_iterations=request.max_iterations,
                auto_follow=True
            )

            return InvestigateResponse(
                success=True,
                session_id=result.session_id,
                iterations=[
                    {
                        "number": it.iteration_number,
                        "tool": it.tool_used,
                        "findings_count": len(it.findings),
                        "iocs_count": sum(len(v) for v in it.iocs.values()),
                        "leads_count": len(it.leads_discovered),
                        "duration": it.duration
                    }
                    for it in result.iterations
                ],
                investigation_chain=[
                    {
                        "type": lead.lead_type.value,
                        "description": lead.description,
                        "priority": lead.priority.value,
                        "confidence": lead.confidence
                    }
                    for lead in result.investigation_chain if lead
                ],
                all_findings=[f.model_dump() for f in result.all_findings],
                all_iocs=result.all_iocs,
                total_duration=result.total_duration,
                stopping_reason=result.stopping_reason,
                summary=result.investigation_summary
            )

        except Exception as e:
            logger.error(f"Investigation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # Autonomous iterative investigation resume hook
    @app.post("/api/v1/investigate/{session_id}/resume", response_model=InvestigateResponse, tags=["Investigation"])
    async def resume_investigation(session_id: str, request: ResumeRequest):
        """Resume a paused investigation after a human analyst reviews the lead."""
        try:
            logger.info(f"Resuming investigation {session_id} - Approved: {request.approved}")

            orchestrator = OrchestratorAgent()
            config = {"configurable": {"thread_id": session_id}}
            
            # Update the state internally
                        # Get current state to avoid overwriting nested dict
            current_state_info = orchestrator.iterative_workflow.get_state(config)
            current_state_dict = current_state_info.values.get("state", {})
            if hasattr(current_state_dict, "model_dump"):
                current_state_dict = current_state_dict.model_dump()
            elif hasattr(current_state_dict, "__dict__"):
                current_state_dict = vars(current_state_dict)
            current_state_dict["human_approved"] = request.approved if hasattr(request, "approved") else approved
            
            orchestrator.iterative_workflow.update_state(
                config,
                {"state": current_state_dict}
            )
            
            # Re-trigger process_iterative to proceed
            result = await orchestrator.process_iterative(
                incident_description="",
                analysis_goal="",
                session_id=session_id
            )

            return InvestigateResponse(
                success=True,
                session_id=result.session_id,
                iterations=[
                    {
                        "number": it.iteration_number,
                        "tool": it.tool_used,
                        "findings_count": len(it.findings),
                        "iocs_count": sum(len(v) for v in it.iocs.values()),
                        "leads_count": len(it.leads_discovered),
                        "duration": it.duration
                    }
                    for it in result.iterations
                ],
                investigation_chain=[
                    {
                        "type": lead.lead_type.value,
                        "description": lead.description,
                        "priority": lead.priority.value,
                        "confidence": lead.confidence
                    }
                    for lead in result.investigation_chain if lead
                ],
                all_findings=[f.model_dump() for f in result.all_findings],
                all_iocs=result.all_iocs,
                total_duration=result.total_duration,
                stopping_reason=result.stopping_reason,
                summary=result.investigation_summary
            )

        except Exception as e:
            logger.error(f"Investigation resume failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=18000)
