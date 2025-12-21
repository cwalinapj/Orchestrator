# Orchestrator

The AI orchestrator built with CodeRunner base for secure code execution.

## Overview

This orchestrator provides a secure, sandboxed environment for executing AI-generated code using a CodeRunner base architecture. It uses Docker containers to isolate code execution and provides a REST API for task orchestration.

## Features

- **Secure Code Execution**: Run code in isolated Docker containers
- **CodeRunner Base**: Built on CodeRunner architecture for safe sandbox execution
- **REST API**: FastAPI-based API for orchestration tasks
- **Docker Compose**: Easy deployment with docker-compose
- **Multi-language Support**: Extensible for multiple programming languages

## Architecture

The system consists of two main components:

1. **Orchestrator Service**: FastAPI application that manages tasks and coordinates execution
2. **CodeRunner Sandbox**: Isolated container for secure code execution

## Prerequisites

- Docker (>= 20.10)
- Docker Compose (>= 2.0)
- Python 3.11+ (for local development)

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/cwalinapj/Orchestrator.git
cd Orchestrator
```

2. Start the services:
```bash
docker-compose up -d
```

3. Check the status:
```bash
curl http://localhost:8080/health
```

### Local Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the orchestrator:
```bash
python orchestrator.py
```

## API Usage

### Health Check

```bash
curl http://localhost:8080/health
```

### Execute Code

```bash
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello from CodeRunner!\")",
    "language": "python",
    "timeout": 30
  }'
```

## API Endpoints

- `GET /` - Service status
- `GET /health` - Detailed health check
- `POST /execute` - Execute code in sandbox

## Configuration

Environment variables can be set in `docker-compose.yml` or `.env` file:

- `PORT`: Orchestrator API port (default: 8080)
- `CODERUNNER_HOST`: CodeRunner container hostname
- `CODERUNNER_PORT`: CodeRunner service port
- `PYTHONUNBUFFERED`: Enable unbuffered Python output

## Security

The CodeRunner sandbox container is configured with:
- Limited capabilities (CAP_DROP: ALL)
- No new privileges
- Isolated network
- Resource limits

## Development

### Project Structure

```
Orchestrator/
├── orchestrator.py      # Main orchestrator application
├── requirements.txt     # Python dependencies
├── Dockerfile          # Orchestrator container definition
├── docker-compose.yml  # Multi-container setup
├── .gitignore         # Git ignore patterns
└── README.md          # This file
```

### Adding New Features

1. Modify `orchestrator.py` to add new endpoints
2. Update `requirements.txt` if new dependencies are needed
3. Test locally before deploying
4. Update documentation

## Troubleshooting

### Docker Issues

If containers fail to start:
```bash
docker-compose logs
```

### Permission Issues

If you get Docker socket permission errors:
```bash
sudo usermod -aG docker $USER
```

Then log out and back in.

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
