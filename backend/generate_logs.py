# # generate_logs.py
# import time
# errors = ["ConnectionError", "NullPointerException", "Failed to connect DB"]

# with open("logs/sample.log", "a") as f:
#     for i in range(10):
#         f.write(f"[INFO] Process {i} completed successfully.\n")
#         if i % 3 == 0:
#             f.write(f"[ERROR] {errors[i % len(errors)]} occurred at iteration {i}.\n")
#         time.sleep(2)



import time
import random
from datetime import datetime

# Sample test cases with different outcomes
test_cases = [
    ("Login with valid credentials", "PASS"),
    ("Login with invalid credentials", "FAIL"),
    ("User registration", "PASS"),
    ("Password reset", "PASS"),
    ("Session timeout", "FAIL"),
    ("API endpoint test", "PASS"),
    ("Database connection", "PASS"),
    ("File upload", "FAIL"),
    ("Email notification", "PASS"),
    ("Payment processing", "PASS")
]

# Error messages for failed tests
error_messages = [
    "Database connection timeout error occurred",
    "JavaScript undefined variable error in login.js",
    "Python API endpoint failed with 500 error",
    "SQL query timeout after 30 seconds",
    "Authentication token expired",
    "Network connection refused",
    "File upload size exceeds limit",
    "Email service unavailable"
]

with open("../logs/sample.log", "w") as f:
    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] Starting Test Suite Execution\n")
    
    for i, (test_name, result) in enumerate(test_cases):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if result == "PASS":
            f.write(f"[{timestamp}] [PASS] Test case: {test_name} - PASSED\n")
        else:
            f.write(f"[{timestamp}] [FAIL] Test case: {test_name} - FAILED\n")
            # Add error message for failed tests
            error_msg = random.choice(error_messages)
            f.write(f"[{timestamp}] [ERROR] {error_msg}\n")
        
        time.sleep(1)  # Simulate test execution time
    
    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] Test Suite Completed\n")
    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [SUMMARY] Total Tests: {len(test_cases)}, Passed: {sum(1 for _, r in test_cases if r == 'PASS')}, Failed: {sum(1 for _, r in test_cases if r == 'FAIL')}\n")

print("✅ Sample log file generated with test cases!")