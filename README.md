# System Bootstrap

A minimal, production-grade Python bootstrap project.

## Overview

This project provides a clean starting point with:
- **Single Entry Point**: Execution starts strictly from `app/main.py`.
- **Structured Logging**: JSON-formatted logs for better observability.
- **Graceful Shutdown**: Handles `SIGINT` (Ctrl+C) and `SIGTERM` correctly.

## how to Run

### Mac / Linux
Run the provided shell script:
```bash
./run.sh
```

### Windows
Run the batch script:
```cmd
run.bat
```

## Expected Output

When running, you should see logs similar to:
```
{"timestamp": "...", "level": "INFO", "message": "System starting..."}
{"timestamp": "...", "level": "INFO", "message": "System initialized. Running main loop."}
```

To stop the system, press `Ctrl+C`. You will see:
```
{"timestamp": "...", "level": "INFO", "message": "Received signal 2. Shutting down gracefully..."}
{"timestamp": "...", "level": "INFO", "message": "Cleanup complete. Exiting."}
```
