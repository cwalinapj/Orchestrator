#!/usr/bin/env python3
"""
AI Orchestrator with CodeRunner Base
Orchestrates AI tasks and executes code in a sandboxed environment
"""

import os
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import docker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Orchestrator",
    description="Orchestrator for AI tasks with CodeRunner base",
    version="1.0.0"
)

# Docker client for CodeRunner interactions
try:
    docker_client = docker.from_env()
    logger.info("Docker client initialized successfully")
except Exception as e:
    logger.warning(f"Docker client initialization failed: {e}")
    docker_client = None


class CodeExecutionRequest(BaseModel):
    """Request model for code execution"""
    code: str
    language: str = "python"
    timeout: int = 30


class CodeExecutionResponse(BaseModel):
    """Response model for code execution"""
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "AI Orchestrator",
        "coderunner_base": "enabled"
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "orchestrator": "healthy",
        "docker": docker_client is not None,
        "coderunner_available": check_coderunner_available()
    }


@app.post("/execute", response_model=CodeExecutionResponse)
async def execute_code(request: CodeExecutionRequest):
    """
    Execute code in the CodeRunner sandbox
    
    Args:
        request: CodeExecutionRequest with code and language
        
    Returns:
        CodeExecutionResponse with execution results
    """
    try:
        logger.info(f"Executing {request.language} code in sandbox")
        
        if not docker_client:
            raise HTTPException(status_code=503, detail="Docker not available")
        
        # Execute code in coderunner container
        result = execute_in_sandbox(
            request.code,
            request.language,
            request.timeout
        )
        
        return CodeExecutionResponse(
            success=result.get("success", False),
            output=result.get("output"),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Code execution failed: {e}")
        return CodeExecutionResponse(
            success=False,
            error=str(e)
        )


def check_coderunner_available() -> bool:
    """Check if CodeRunner container is available"""
    if not docker_client:
        return False
    
    try:
        containers = docker_client.containers.list(
            filters={"name": "coderunner-sandbox"}
        )
        return len(containers) > 0
    except Exception as e:
        logger.error(f"Failed to check CodeRunner availability: {e}")
        return False


def execute_in_sandbox(code: str, language: str, timeout: int) -> Dict[str, Any]:
    """
    Execute code in the sandboxed CodeRunner container
    
    Args:
        code: Code to execute
        language: Programming language
        timeout: Execution timeout in seconds
        
    Returns:
        Dict with execution results
    """
    try:
        # Get or create sandbox container
        container_name = "coderunner-sandbox"
        
        try:
            container = docker_client.containers.get(container_name)
        except docker.errors.NotFound:
            logger.error(f"Container {container_name} not found")
            return {
                "success": False,
                "error": "CodeRunner sandbox not available"
            }
        
        # Execute code based on language
        if language.lower() == "python":
            exec_command = ["python", "-c", code]
        else:
            return {
                "success": False,
                "error": f"Language {language} not supported"
            }
        
        # Run code in container
        exec_result = container.exec_run(
            exec_command,
            demux=True,
            environment={"PYTHONUNBUFFERED": "1"}
        )
        
        # Parse results
        stdout = exec_result.output[0].decode() if exec_result.output[0] else ""
        stderr = exec_result.output[1].decode() if exec_result.output[1] else ""
        
        success = exec_result.exit_code == 0
        
        return {
            "success": success,
            "output": stdout if success else stderr,
            "error": stderr if not success else None
        }
        
    except Exception as e:
        logger.error(f"Sandbox execution failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8080"))
    logger.info(f"Starting AI Orchestrator on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
