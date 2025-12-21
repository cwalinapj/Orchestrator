#!/usr/bin/env python3
"""
Example usage of the AI Orchestrator with CodeRunner base
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


def main():
    """Run examples"""
    print("=== AI Orchestrator CodeRunner Base Examples ===\n")
    
    # Check health
    check_health()
    
    # Example 1: Simple print
    print("Example 1: Simple Hello World")
    execute_python_code('print("Hello from CodeRunner base!")')
    
    # Example 2: Math calculation
    print("Example 2: Math Calculation")
    execute_python_code('''
result = sum(range(1, 11))
print(f"Sum of 1-10: {result}")
''')
    
    # Example 3: List comprehension
    print("Example 3: List Comprehension")
    execute_python_code('''
squares = [x**2 for x in range(1, 6)]
print(f"Squares: {squares}")
''')
    
    # Example 4: Error handling
    print("Example 4: Error Handling")
    execute_python_code('''
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"Caught error: {e}")
''')


if __name__ == "__main__":
    main()
