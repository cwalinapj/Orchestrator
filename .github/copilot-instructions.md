# Copilot Instructions for Orchestrator

## Project Overview

This is an AI orchestrator with CodeRunner base for secure code execution, multi-repository operations, and cloud pricing monitoring. The orchestrator provides a sandboxed environment for executing AI-generated code using Docker containers and offers a REST API for task orchestration.

## Tech Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI (REST API)
- **Container Runtime**: Docker
- **GitHub Integration**: PyGithub, GitPython
- **Dependencies**: See `requirements.txt`
- **UI**: Web (HTML/JavaScript) and Desktop (tkinter)

## Architecture

The system has two main components:
1. **Orchestrator Service**: FastAPI application managing tasks and repository operations
2. **CodeRunner Sandbox**: Isolated Docker container for secure code execution
3. **Cloud Pricing Monitor**: Module for monitoring GPU/CPU instance prices across providers

## Coding Standards and Conventions

### Python Style
- Follow PEP 8 style guide
- Use type hints for function parameters and return values
- Use docstrings for modules, classes, and functions
- Prefer async/await for I/O operations
- Use dataclasses for data structures
- Use Enum for constants and enumerated types

### Code Organization
- Keep modules focused and single-purpose
- Use meaningful variable and function names
- Limit functions to a single responsibility
- Keep functions under 50 lines when possible

### Logging
- Use the built-in `logging` module
- Log at appropriate levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Include contextual information in log messages
- Format: `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`

### API Development
- Use Pydantic models for request/response validation
- Include docstrings for API endpoints
- Return appropriate HTTP status codes
- Handle exceptions and return meaningful error messages
- Use FastAPI dependency injection when appropriate

### Error Handling
- Use try-except blocks for operations that can fail
- Log errors with appropriate context
- Return user-friendly error messages via API
- Don't expose internal implementation details in error messages

## Security Guidelines

### Code Execution
- All code execution must happen in isolated Docker containers
- Use resource limits and capability restrictions
- Never execute untrusted code on the host system
- Validate and sanitize all user inputs

### API Security
- Validate all request payloads using Pydantic models
- Use environment variables for sensitive configuration
- Never commit secrets, tokens, or credentials to the repository
- Use HTTPS in production deployments

### Docker Security
- Run containers with minimal privileges (CAP_DROP: ALL)
- Use security_opt: no-new-privileges
- Implement resource limits (CPU, memory)
- Use isolated networks for containers

## Testing and Quality

### Testing Guidelines
- Add tests for new features and bug fixes when test infrastructure exists
- Test API endpoints with various input scenarios
- Mock external dependencies (Docker, GitHub API)
- Test error handling paths

### Code Quality
- Ensure code is readable and maintainable
- Remove unused imports and dead code
- Use meaningful commit messages
- Keep changes focused and atomic

## Development Workflow

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running Locally
```bash
# Run orchestrator
python orchestrator.py

# Run with Docker Compose
docker-compose up -d
```

### Testing API
```bash
# Health check
curl http://localhost:8080/health

# Execute code
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"test\")", "language": "python"}'
```

## Repository Operations

### GitHub Integration
- Use authenticated GitHub client when GITHUB_TOKEN is available
- Handle rate limits gracefully
- Support both authenticated and unauthenticated access
- Clone repositories to temporary directories
- Clean up cloned repositories after operations

### Supported Operations
- `clone_and_analyze`: Clone and analyze repository structure
- `run_tests`: Detect and run repository tests
- `scan`: Run security/code scans

## Cloud Pricing Monitor

### Design Principles
- Use simulated data for demonstration (replace with real APIs in production)
- Support async operations for monitoring
- Allow configurable price thresholds
- Enable auto-launch when thresholds are met
- Provide both web UI and desktop UI

### Supported Providers
AWS, GCP, Azure, Digital Ocean, Linode, Vultr, OVH, Hetzner, Oracle Cloud, IBM Cloud

## File Structure

```
Orchestrator/
├── orchestrator.py           # Main FastAPI application
├── cloud_pricing_monitor.py  # Pricing monitor module
├── pricing_monitor_ui.py     # Desktop UI (tkinter)
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container definition
├── docker-compose.yml       # Multi-container setup
├── static/                  # Web UI static files
├── data/                    # Data directory
└── sandbox/                 # Sandbox-related files
```

## Common Tasks for Copilot

### Adding New API Endpoints
1. Define request/response Pydantic models
2. Add endpoint handler with proper error handling
3. Include logging statements
4. Update README.md with endpoint documentation
5. Consider security implications

### Adding New Cloud Providers
1. Add provider to `CloudProvider` enum in `cloud_pricing_monitor.py`
2. Implement price fetcher function
3. Add to provider initialization in monitor
4. Update documentation

### Modifying Docker Configuration
1. Test changes locally first
2. Consider security implications
3. Update docker-compose.yml if needed
4. Document any new environment variables

## Dependencies

### Adding New Dependencies
- Add to `requirements.txt` with version constraints
- Use `>=` for minimum version requirements
- Document why the dependency is needed
- Consider security and maintenance implications

### Updating Dependencies
- Review changelog for breaking changes
- Test thoroughly after updates
- Update version constraints in `requirements.txt`

## Documentation

### Updating README
- Keep README.md up-to-date with new features
- Include code examples for API usage
- Document configuration options
- Update troubleshooting section as needed

### Code Comments
- Use docstrings for all public functions and classes
- Add inline comments for complex logic
- Keep comments concise and meaningful
- Update comments when code changes

## Special Considerations

### Async Operations
- Use `async`/`await` for I/O bound operations
- Use asyncio event loops properly
- Handle async context managers correctly (e.g., FastAPI lifespan)

### Docker Operations
- Check if docker_client is initialized before use
- Handle Docker exceptions gracefully
- Clean up containers and resources after use
- Use appropriate timeouts

### GitHub Operations
- Handle GithubException appropriately
- Respect API rate limits
- Support both authenticated and anonymous access
- Use temporary directories for repository operations
