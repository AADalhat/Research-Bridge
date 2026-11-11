import sys
from pathlib import Path

# Ensure workspace directory is in python path
workspace_dir = str(Path(__file__).parent.resolve())
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

import broker
import tasks
from dramatiq.cli import main

if __name__ == "__main__":
    print("[CrownBird AI Worker] Starting Dramatiq worker connected to Redis...")
    # On Windows, use 1 process with multiple worker threads
    sys.argv = ["dramatiq", "tasks", "--processes", "1", "--threads", "4"]
    main()

