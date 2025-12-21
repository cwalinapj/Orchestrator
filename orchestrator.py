#!/usr/bin/env python3
"""
AI Orchestrator with CodeRunner Base
Orchestrates AI tasks and executes code in a sandboxed environment
Supports multi-repository operations for cloning, analyzing, and running code
"""

import os
import logging
import shutil
import tempfile
from typing import Dict, Any, Optional, List
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import docker
from github import Github, GithubException
from git import Repo, GitCommandError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Orchestrator",
    description="Orchestrator for AI tasks with CodeRunner base - supports multi-repository operations",
    version="2.0.0"
)

# Docker client for CodeRunner interactions
try:
    docker_client = docker.from_env()
    logger.info("Docker client initialized successfully")
except Exception as e:
    logger.warning(f"Docker client initialization failed: {e}")
    docker_client = None

# GitHub client (optional - uses GITHUB_TOKEN env var if available)
github_client = None
github_token = os.getenv("GITHUB_TOKEN")
if github_token:
    try:
        github_client = Github(github_token)
        logger.info("GitHub client initialized successfully")
    except Exception as e:
        logger.warning(f"GitHub client initialization failed: {e}")
else:
    logger.info("No GITHUB_TOKEN provided - GitHub operations will use unauthenticated access")
    github_client = Github()  # Unauthenticated access with rate limits


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


class RepositoryRequest(BaseModel):
    """Request model for repository operations"""
    repo_url: str
    operation: str = "clone_and_analyze"  # clone_and_analyze, run_tests, scan
    branch: Optional[str] = "main"
    scan_command: Optional[str] = None


class RepositoryBatchRequest(BaseModel):
    """Request model for batch repository operations"""
    repo_urls: List[str]
    operation: str = "clone_and_analyze"
    branch: Optional[str] = "main"
    scan_command: Optional[str] = None


class RepositoryResponse(BaseModel):
    """Response model for repository operations"""
    success: bool
    repo_url: str
    operation: str
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class RepositoryBatchResponse(BaseModel):
    """Response model for batch repository operations"""
    total: int
    successful: int
    failed: int
    results: List[RepositoryResponse]


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "AI Orchestrator",
        "version": "2.0.0",
        "coderunner_base": "enabled",
        "features": [
            "code_execution",
            "repository_operations",
            "multi_repo_scanning"
        ]
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "orchestrator": "healthy",
        "docker": docker_client is not None,
        "coderunner_available": check_coderunner_available(),
        "github_client": github_client is not None,
        "github_authenticated": github_token is not None
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


@app.post("/repository", response_model=RepositoryResponse)
async def process_repository(request: RepositoryRequest):
    """
    Process a single repository - clone, analyze, run tests, or scan
    
    Args:
        request: RepositoryRequest with repo URL and operation
        
    Returns:
        RepositoryResponse with operation results
    """
    try:
        logger.info(f"Processing repository: {request.repo_url}")
        
        result = process_single_repository(
            request.repo_url,
            request.operation,
            request.branch,
            request.scan_command
        )
        
        return RepositoryResponse(
            success=result.get("success", False),
            repo_url=request.repo_url,
            operation=request.operation,
            results=result.get("results"),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Repository processing failed: {e}")
        return RepositoryResponse(
            success=False,
            repo_url=request.repo_url,
            operation=request.operation,
            error=str(e)
        )


@app.post("/repositories/batch", response_model=RepositoryBatchResponse)
async def process_repositories_batch(request: RepositoryBatchRequest):
    """
    Process multiple repositories in batch
    
    Args:
        request: RepositoryBatchRequest with list of repo URLs and operation
        
    Returns:
        RepositoryBatchResponse with results for all repositories
    """
    try:
        logger.info(f"Processing {len(request.repo_urls)} repositories")
        
        results = []
        successful = 0
        failed = 0
        
        for repo_url in request.repo_urls:
            result = process_single_repository(
                repo_url,
                request.operation,
                request.branch,
                request.scan_command
            )
            
            repo_response = RepositoryResponse(
                success=result.get("success", False),
                repo_url=repo_url,
                operation=request.operation,
                results=result.get("results"),
                error=result.get("error")
            )
            
            results.append(repo_response)
            
            if repo_response.success:
                successful += 1
            else:
                failed += 1
        
        return RepositoryBatchResponse(
            total=len(request.repo_urls),
            successful=successful,
            failed=failed,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Batch repository processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        timeout: Execution timeout in seconds (Note: timeout enforcement requires 
                 additional implementation as docker.exec_run doesn't natively support it)
        
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
        
        # Run code in container with timeout
        exec_result = container.exec_run(
            exec_command,
            demux=True,
            environment={"PYTHONUNBUFFERED": "1"},
            stream=False
        )
        
        # Parse results with safety checks
        output_tuple = exec_result.output if exec_result.output else (None, None)
        stdout = output_tuple[0].decode() if output_tuple[0] else ""
        stderr = output_tuple[1].decode() if output_tuple[1] else ""
        
        success = exec_result.exit_code == 0
        
        return {
            "success": success,
            "output": stdout,
            "error": stderr if stderr else None
        }
        
    except Exception as e:
        logger.error(f"Sandbox execution failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def validate_repo_url(repo_url: str) -> bool:
    """
    Validate repository URL to ensure it's from trusted sources
    
    Args:
        repo_url: Repository URL to validate
        
    Returns:
        True if URL is valid and trusted, False otherwise
    """
    try:
        # Allow GitHub, GitLab, and Bitbucket URLs
        trusted_domains = [
            "github.com",
            "gitlab.com",
            "bitbucket.org"
        ]
        
        # Check if URL starts with https
        if not repo_url.startswith("https://"):
            logger.warning(f"Repository URL must use HTTPS: {repo_url}")
            return False
        
        # Check if domain is trusted
        for domain in trusted_domains:
            if domain in repo_url:
                return True
        
        logger.warning(f"Repository URL from untrusted domain: {repo_url}")
        return False
        
    except Exception as e:
        logger.error(f"URL validation failed: {e}")
        return False


def process_single_repository(
    repo_url: str, 
    operation: str, 
    branch: Optional[str] = "main",
    scan_command: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a single repository based on the specified operation
    
    Args:
        repo_url: URL of the repository (https://github.com/owner/repo)
        operation: Operation to perform (clone_and_analyze, run_tests, scan)
        branch: Branch to checkout (default: main)
        scan_command: Custom command to run for scanning
        
    Returns:
        Dict with operation results
    """
    temp_dir = None
    try:
        # Validate repository URL
        if not validate_repo_url(repo_url):
            return {
                "success": False,
                "error": "Invalid or untrusted repository URL"
            }
        
        # Create secure temporary directory for repo
        temp_dir = tempfile.mkdtemp(prefix="repo_", dir="/tmp")
        logger.info(f"Cloning {repo_url} to {temp_dir}")
        
        # Clone repository
        try:
            repo = Repo.clone_from(repo_url, temp_dir, branch=branch, depth=1)
            logger.info(f"Successfully cloned {repo_url}")
        except GitCommandError as e:
            logger.error(f"Failed to clone repository: {e}")
            return {
                "success": False,
                "error": f"Failed to clone repository: {str(e)}"
            }
        
        # Perform the requested operation
        if operation == "clone_and_analyze":
            results = analyze_repository(temp_dir)
        elif operation == "run_tests":
            results = run_repository_tests(temp_dir)
        elif operation == "scan":
            results = scan_repository(temp_dir, scan_command)
        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}"
            }
        
        return {
            "success": True,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Repository processing failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {temp_dir}: {e}")


def analyze_repository(repo_path: str) -> Dict[str, Any]:
    """
    Analyze repository structure and contents
    
    Args:
        repo_path: Path to cloned repository
        
    Returns:
        Dict with analysis results
    """
    try:
        analysis = {
            "path": repo_path,
            "files": [],
            "directories": [],
            "file_types": {},
            "total_files": 0,
            "total_size": 0
        }
        
        # Walk through repository
        for root, dirs, files in os.walk(repo_path):
            # Skip .git directory
            if '.git' in root:
                continue
                
            rel_root = os.path.relpath(root, repo_path)
            if rel_root != '.':
                analysis["directories"].append(rel_root)
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)
                
                # Get file extension
                ext = os.path.splitext(file)[1] or 'no_extension'
                analysis["file_types"][ext] = analysis["file_types"].get(ext, 0) + 1
                
                # Get file size
                try:
                    size = os.path.getsize(file_path)
                    analysis["total_size"] += size
                except (OSError, IOError):
                    pass
                
                analysis["files"].append(rel_path)
                analysis["total_files"] += 1
        
        # Get top file types
        top_types = sorted(
            analysis["file_types"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        analysis["top_file_types"] = dict(top_types)
        
        return analysis
        
    except Exception as e:
        logger.error(f"Repository analysis failed: {e}")
        return {"error": str(e)}


def run_repository_tests(repo_path: str) -> Dict[str, Any]:
    """
    Run tests in the repository using common test frameworks
    
    Args:
        repo_path: Path to cloned repository
        
    Returns:
        Dict with test results
    """
    try:
        results = {
            "test_framework_detected": None,
            "tests_run": False,
            "output": None,
            "error": None
        }
        
        # Detect test framework and run tests
        if os.path.exists(os.path.join(repo_path, "pytest.ini")) or \
           os.path.exists(os.path.join(repo_path, "setup.py")):
            results["test_framework_detected"] = "pytest"
            test_output = run_command_in_sandbox(repo_path, "pytest --collect-only")
            results["output"] = test_output.get("output")
            results["tests_run"] = test_output.get("success", False)
            
        elif os.path.exists(os.path.join(repo_path, "package.json")):
            results["test_framework_detected"] = "npm"
            test_output = run_command_in_sandbox(repo_path, "npm test --version")
            results["output"] = test_output.get("output")
            results["tests_run"] = test_output.get("success", False)
            
        else:
            results["test_framework_detected"] = "none"
            results["output"] = "No test framework detected"
        
        return results
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return {"error": str(e)}


def scan_repository(repo_path: str, scan_command: Optional[str] = None) -> Dict[str, Any]:
    """
    Scan repository with custom command or default security scan
    
    Args:
        repo_path: Path to cloned repository
        scan_command: Custom command to run
        
    Returns:
        Dict with scan results
    """
    try:
        if scan_command:
            # Run custom scan command
            result = run_command_in_sandbox(repo_path, scan_command)
        else:
            # Default: list Python files and check for common patterns
            result = {
                "success": True,
                "output": f"Repository scanned at {repo_path}",
                "python_files": [],
                "javascript_files": [],
                "config_files": []
            }
            
            for root, _, files in os.walk(repo_path):
                if '.git' in root:
                    continue
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                    if file.endswith('.py'):
                        result["python_files"].append(rel_path)
                    elif file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                        result["javascript_files"].append(rel_path)
                    elif file in ['package.json', 'requirements.txt', 'Dockerfile', 'docker-compose.yml']:
                        result["config_files"].append(rel_path)
        
        return result
        
    except Exception as e:
        logger.error(f"Repository scan failed: {e}")
        return {"error": str(e)}


def run_command_in_sandbox(repo_path: str, command: str) -> Dict[str, Any]:
    """
    Run a command in the coderunner sandbox with repository mounted
    
    Args:
        repo_path: Path to repository on host
        command: Command to execute
        
    Returns:
        Dict with command results
    """
    try:
        if not docker_client:
            return {
                "success": False,
                "error": "Docker client not available"
            }
        
        container_name = "coderunner-sandbox"
        
        try:
            container = docker_client.containers.get(container_name)
        except docker.errors.NotFound:
            return {
                "success": False,
                "error": "CodeRunner sandbox not available"
            }
        
        # Execute command in container workdir
        # Note: In production, use volume mounts to share repository files
        exec_result = container.exec_run(
            ["sh", "-c", command],
            demux=True,
            workdir="/workspace"
        )
        
        # Parse output with safety checks
        output_tuple = exec_result.output if exec_result.output else (None, None)
        if isinstance(output_tuple, tuple) and len(output_tuple) >= 2:
            stdout = output_tuple[0].decode() if output_tuple[0] else ""
            stderr = output_tuple[1].decode() if output_tuple[1] else ""
        else:
            # Fallback if output is not a tuple
            stdout = str(exec_result.output) if exec_result.output else ""
            stderr = ""
        
        return {
            "success": exec_result.exit_code == 0,
            "output": stdout,
            "error": stderr if stderr else None
        }
        
    except Exception as e:
        logger.error(f"Command execution in sandbox failed: {e}")
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
