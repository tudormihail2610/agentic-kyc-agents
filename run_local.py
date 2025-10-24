# agents-tutorial/main.py
import uvicorn
import argparse
import importlib.util
import os
from fastapi import FastAPI
from google.adk.a2a.utils.agent_to_a2a import to_a2a

def load_root_agent(agent_folder: str):
    agent_path = os.path.join(agent_folder, "agent.py")
    spec = importlib.util.spec_from_file_location("agent", agent_path)
    agent_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(agent_module)
    return agent_module.root_agent

def main():
    parser = argparse.ArgumentParser(description="Run agent as FastAPI service")
    parser.add_argument("--agent-folder", required=True, help="Path to the agent folder")
    parser.add_argument("--port", type=int, default=8001, help="Port to run the server on")
    args = parser.parse_args()

    root_agent = load_root_agent(args.agent_folder)
    app: FastAPI = to_a2a(root_agent, host="0.0.0.0", port=args.port)

    uvicorn.run(app, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()