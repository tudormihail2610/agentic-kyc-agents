#!/usr/bin/env python3
# cr_agent.py
"""
Usage:
  python cr_agent.py run <agent_folder> [--project PROJECT] [--region REGION]
  python cr_agent.py delete <agent_folder> [--project PROJECT] [--region REGION]

Run:
  adk deploy cloud_run --project <project> --region <region> --service_name <agent_folder> --a2a <agent_folder>

Delete (tries ADK first, then gcloud fallback):
  adk delete cloud_run --project <project> --region <region> --service_name <agent_folder>
  gcloud run services delete <agent_folder> --project <project> --region <region> --quiet
"""
import os
import sys
import argparse
import subprocess
from dotenv import load_dotenv

load_dotenv()

def run_command(cmd, auto_confirm=False) -> int:
    print("Running:", " ".join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    import threading
    def stream_output(stream, label):
        print(f"--- {label} ---")
        for line in iter(stream.readline, b''):
            if line:
                sys.stdout.buffer.write(line) if label == "STDOUT" else sys.stderr.buffer.write(line)
                sys.stdout.flush() if label == "STDOUT" else sys.stderr.flush()
        stream.close()
    t_out = threading.Thread(target=stream_output, args=(proc.stdout, "STDOUT"))
    t_err = threading.Thread(target=stream_output, args=(proc.stderr, "STDERR"))
    t_out.start()
    t_err.start()
    if auto_confirm:
        try:
            proc.stdin.write(b'y\n')
            proc.stdin.flush()
        except Exception as e:
            print(f"Failed to send auto-confirm: {e}", file=sys.stderr)
    t_out.join()
    t_err.join()
    proc.wait()
    print("\nExit code:", proc.returncode)
    return proc.returncode

def run_agent(agent_folder: str, agent: str, project: str, region: str) -> int:
    cmd = [
        "adk", "deploy", "cloud_run",
        "--project", project,
        "--region", region,
        "--service_name", agent,
        "--a2a", agent_folder,
    ]
    return run_command(cmd)

def delete_agent(agent: str, project: str, region: str) -> int:
    # Try ADK delete first
    adk_cmd = [
        "adk", "delete", "cloud_run",
        "--project", project,
        "--region", region,
        "--service_name", agent,
    ]
    rc = run_command(adk_cmd, auto_confirm=True)
    if rc == 0:
        print("Deleted with adk successfully.")
        return 0

    print("adk delete failed (or not available). Trying gcloud fallback...")
    gcloud_cmd = [
        "gcloud", "run", "services", "delete", agent,
        "--project", project,
        "--region", region,
        "--quiet",
    ]
    rc = run_command(gcloud_cmd, auto_confirm=True)
    if rc == 0:
        print("Deleted with gcloud successfully.")
        return 0

    print("Both adk and gcloud delete attempts failed. See output above for details.", file=sys.stderr)
    return rc

def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["run", "delete"], help="Action to execute")
    p.add_argument("agent_folder", help="Agent folder / Cloud Run service name")
    p.add_argument("agent",help="Agent name")
    p.add_argument("--project", help="GCP project id (or set GOOGLE_CLOUD_PROJECT)")
    p.add_argument("--region", default="us-central1", help="GCP region (default: us-central1)")
    args = p.parse_args()

    project = args.project or os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        print("ERROR: --project not provided and GOOGLE_CLOUD_PROJECT not set", file=sys.stderr)
        sys.exit(2)

    if args.action == "run":
        sys.exit(run_agent(args.agent_folder, args.agent, project, args.region))
    else:
        sys.exit(delete_agent(args.agent, project, args.region))

if __name__ == "__main__":
    main()
