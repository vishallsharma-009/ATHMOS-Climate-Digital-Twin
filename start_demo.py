import subprocess
import time
import os
import sys

def main():
    print("========================================")
    print("🚀 Starting ATHMOS Digital Twin...")
    print("========================================")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    frontend_dir = os.path.join(base_dir, "frontend")

    # Start FastAPI Backend
    print("\n[1] Starting AI Backend (FastAPI)...")
    backend_cmd = "uvicorn app:app --host 127.0.0.0 --port 8000" if os.name == 'nt' else "uvicorn app:app --host 0.0.0.0 --port 8000"
    backend_process = subprocess.Popen(
        backend_cmd, 
        cwd=backend_dir, 
        shell=True,
        stdout=sys.stdout, 
        stderr=sys.stderr
    )
    
    time.sleep(3) # Give the backend a moment to start
    
    # Start React Frontend
    print("\n[2] Starting React Dashboard (Vite)...")
    frontend_cmd = "npm run dev"
    frontend_process = subprocess.Popen(
        frontend_cmd, 
        cwd=frontend_dir, 
        shell=True,
        stdout=sys.stdout, 
        stderr=sys.stderr
    )

    print("\n✅ ATHMOS Engine is Running!")
    print("🌍 Open your browser and navigate to: http://localhost:5173\n")

    try:
        # Keep the main process alive while the subprocesses run
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping services...")
        backend_process.kill()
        frontend_process.kill()
        print("Done.")

if __name__ == "__main__":
    main()
