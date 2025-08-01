# generate_logs.py
import time
errors = ["ConnectionError", "NullPointerException", "Failed to connect DB"]

with open("logs/sample.log", "a") as f:
    for i in range(10):
        f.write(f"[INFO] Process {i} completed successfully.\n")
        if i % 3 == 0:
            f.write(f"[ERROR] {errors[i % len(errors)]} occurred at iteration {i}.\n")
        time.sleep(2)
