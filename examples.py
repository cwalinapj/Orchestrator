#!/usr/bin/env python3
"""
Example usage of the AI Orchestrator with CodeRunner base
Includes examples for code execution and repository operations
"""

import requests
import json

# Orchestrator API endpoint
BASE_URL = "http://localhost:8080"


def check_health():
    """Check orchestrator health"""
    response = requests.get(f"{BASE_URL}/health")
    print("Health Status:")
    print(json.dumps(response.json(), indent=2))
    print()


def execute_python_code(code: str):
    """Execute Python code in the sandbox"""
    payload = {
        "code": code,
        "language": "python",
        "timeout": 30
    }
    
    response = requests.post(f"{BASE_URL}/execute", json=payload)
    result = response.json()
    
    print(f"Execution Result:")
    print(f"Success: {result['success']}")
    if result.get('output'):
        print(f"Output: {result['output']}")
    if result.get('error'):
        print(f"Error: {result['error']}")
    print()


def process_repository(repo_url: str, operation: str = "clone_and_analyze"):
    """Process a single repository"""
    payload = {
        "repo_url": repo_url,
        "operation": operation,
        "branch": "main"
    }
    
    print(f"Processing repository: {repo_url}")
    response = requests.post(f"{BASE_URL}/repository", json=payload)
    result = response.json()
    
    print(f"Repository Operation Result:")
    print(f"Success: {result['success']}")
    print(f"Operation: {result['operation']}")
    if result.get('results'):
        print(f"Results: {json.dumps(result['results'], indent=2)}")
    if result.get('error'):
        print(f"Error: {result['error']}")
    print()


def process_multiple_repositories(repo_urls: list, operation: str = "scan"):
    """Process multiple repositories in batch"""
    payload = {
        "repo_urls": repo_urls,
        "operation": operation,
        "branch": "main"
    }
    
    print(f"Processing {len(repo_urls)} repositories...")
    response = requests.post(f"{BASE_URL}/repositories/batch", json=payload)
    result = response.json()
    
    print(f"Batch Operation Result:")
    print(f"Total: {result['total']}")
    print(f"Successful: {result['successful']}")
    print(f"Failed: {result['failed']}")
    print()
    
    for repo_result in result['results']:
        print(f"  - {repo_result['repo_url']}: {'✓' if repo_result['success'] else '✗'}")
        if repo_result.get('error'):
            print(f"    Error: {repo_result['error']}")
    print()


def main():
    """Run examples"""
    print("=== AI Orchestrator CodeRunner Base Examples ===\n")
    
    # Check health
    print("=" * 60)
    print("1. Health Check")
    print("=" * 60)
    check_health()
    
    # Example 1: Simple print
    print("=" * 60)
    print("2. Code Execution: Simple Hello World")
    print("=" * 60)
    execute_python_code('print("Hello from CodeRunner base!")')
    
    # Example 2: Math calculation
    print("=" * 60)
    print("3. Code Execution: Math Calculation")
    print("=" * 60)
    execute_python_code('''
result = sum(range(1, 11))
print(f"Sum of 1-10: {result}")
''')
    
    # Example 3: Repository analysis
    print("=" * 60)
    print("4. Repository Operations: Analyze Single Repo")
    print("=" * 60)
    # Note: Replace with a real repository URL
    process_repository(
        "https://github.com/octocat/Hello-World",
        operation="clone_and_analyze"
    )
    
    # Example 4: Multiple repository scan
    print("=" * 60)
    print("5. Repository Operations: Batch Scan")
    print("=" * 60)
    # Note: Replace with real repository URLs
    process_multiple_repositories(
        [
            "https://github.com/octocat/Hello-World",
            "https://github.com/octocat/Spoon-Knife"
        ],
        operation="scan"
    )


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to orchestrator.")
        print("Make sure it's running: docker-compose up -d")
    except Exception as e:
        print(f"ERROR: {e}")
