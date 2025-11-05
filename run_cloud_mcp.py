import os
import sys
import argparse
import subprocess
from dotenv import load_dotenv
import datetime

load_dotenv()

def log(msg):
    print(f"[{datetime.datetime.now().isoformat()}] {msg}")

def run_command(cmd) -> int:
    log(f"Executing command: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Print output in real time
    while True:
        out = proc.stdout.readline()
        if out:
            print(out.decode(), end='')
        if proc.poll() is not None:
            break
    # Print any remaining output
    remaining_out, remaining_err = proc.communicate()
    if remaining_out:
        print(remaining_out.decode(), end='')
    if remaining_err:
        print(remaining_err.decode(), end='')
    log(f"Command exit code: {proc.returncode}")
    return proc.returncode

def build_and_deploy(service_name: str, project: str, location: str) -> int:
    image_name = f"gcr.io/{project}/{service_name}"
    log(f"Starting build for service '{service_name}' in project '{project}' and location '{location}'")
    log(f"Container image name: {image_name}")
    # Build the container image
    rc = run_command([
        "gcloud", "builds", "submit", "--tag", image_name, "--project", project
    ])
    if rc != 0:
        log("ERROR: Build failed.")
        return rc
    log("Build succeeded. Starting deployment to Cloud Run...")
    # Deploy to Cloud Run
    rc = run_command([
        "gcloud", "run", "deploy", service_name,
        "--image", image_name,
        "--platform", "managed",
        "--region", location,
        "--project", project,
        "--allow-unauthenticated",
        "--port", "8080"
    ])
    if rc == 0:
        log("Deployment complete. Check your Cloud Run dashboard for the public URL.")
    else:
        log("ERROR: Deployment failed.")
    return rc

def delete_service(service_name: str, project: str, location: str) -> int:
    log(f"Deleting Cloud Run service '{service_name}' in project '{project}' and location '{location}'")
    rc = run_command([
        "gcloud", "run", "services", "delete", service_name,
        "--project", project,
        "--region", location,
        "--platform", "managed",
        "--quiet"
    ])
    if rc == 0:
        log("Cloud Run service stopped (deleted).")
    else:
        log("ERROR: Service deletion failed.")
    return rc

def main():
    p = argparse.ArgumentParser(description="Deploy or delete MCP Cloud Run service.")
    p.add_argument("action", choices=["run", "delete"], help="Action to execute")
    p.add_argument("service_name", help="Cloud Run service name")
    p.add_argument("--project", help="GCP project id (or set in .env as GOOGLE_CLOUD_PROJECT)")
    p.add_argument("--location", help="GCP location/region (or set in .env as GOOGLE_CLOUD_LOCATION)")
    args = p.parse_args()

    project = args.project or os.getenv("GOOGLE_CLOUD_PROJECT")
    location = args.location or os.getenv("GOOGLE_CLOUD_LOCATION")

    log(f"Resolved project: {project}")
    log(f"Resolved location: {location}")

    if not project:
        log("ERROR: --project not provided and GOOGLE_CLOUD_PROJECT not set in .env")
        sys.exit(2)
    if not location:
        log("ERROR: --location not provided and GOOGLE_CLOUD_LOCATION not set in .env")
        sys.exit(2)

    if args.action == "run":
        sys.exit(build_and_deploy(args.service_name, project, location))
    else:
        sys.exit(delete_service(args.service_name, project, location))

if __name__ == "__main__":
    main()
