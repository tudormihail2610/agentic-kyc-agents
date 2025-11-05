import os

from dotenv import load_dotenv
from google import genai
from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.planners import BuiltInPlanner
from google.genai import types
import re
from typing import List, Optional, Dict, Any

load_dotenv()

current_environment = os.getenv("ENV")

project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

client = genai.Client(
    vertexai = True,
    project = project_id,
    location = os.getenv("GOOGLE_CLOUD_LOCATION"),
)

default_planner = BuiltInPlanner(
    thinking_config = types.ThinkingConfig(include_thoughts = True)
)

default_generate_cfg = types.GenerateContentConfig(
    safety_settings=[
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.OFF
        )
    ],
)

# --- New: validation helper functions added as tools ---

NAME_TOKEN_RE = re.compile(r"^[A-Za-z\-']+$")
EMAIL_RE = re.compile(
    r"^(?P<local>[A-Za-z0-9!#$%&'*+/=?^_`{|}~.-]+)@(?P<domain>[A-Za-z0-9.-]+\.[A-Za-z]{2,})$"
)


def verify_name(full_name: str) -> Dict[str, Any]:
    """
    Validate a client's full name.

    Rules derived from client_analysis_agent:
    - Require at least two name tokens (first + last).
    - Each token must be at least 2 characters long.
    - Tokens may contain letters, hyphens and apostrophes only.

    Returns: { valid: bool, reason: str }
    """
    if not full_name or not isinstance(full_name, str):
        return {"valid": False, "reason": "Name must be a non-empty string."}

    # Normalize whitespace
    normalized = " ".join(full_name.strip().split())
    tokens = normalized.split(" ")

    if len(tokens) < 2:
        return {"valid": False, "reason": "Full name must include at least two name parts (e.g., first and last name)."}

    for t in tokens:
        if len(t) < 2:
            return {"valid": False, "reason": f"Name token '{t}' is too short (minimum 2 characters)."}
        if not NAME_TOKEN_RE.match(t):
            return {"valid": False, "reason": f"Name token '{t}' contains invalid characters. Only letters, hyphens and apostrophes are allowed."}

    return {"valid": True, "reason": "Name looks valid.", "normalized": normalized}


def verify_email(email: str, check_mx: bool = False) -> Dict[str, Any]:
    """
    Validate an email address syntactically and optionally check MX records.

    Returns: { valid: bool, reason: str, mx_checked: bool, deliverable: bool }
    - mx_checked: whether an MX lookup was attempted
    - deliverable: True only if MX lookup succeeded and returned at least one MX host
    """
    if not email or not isinstance(email, str):
        return {"valid": False, "reason": "Email must be a non-empty string.", "mx_checked": False, "deliverable": False}

    email = email.strip()
    m = EMAIL_RE.match(email)
    if not m:
        return {"valid": False, "reason": "Email failed syntactic validation.", "mx_checked": False, "deliverable": False}

    domain = m.group("domain")

    mx_checked = False
    deliverable = False
    mx_reason = "MX check not performed."

    if check_mx:
        # Attempt to perform an MX lookup if dnspython is available and network is permitted.
        try:
            import dns.resolver  # type: ignore

            mx_checked = True
            try:
                answers = dns.resolver.resolve(domain, "MX")
                hosts = [r.exchange.to_text() for r in answers]
                if hosts:
                    deliverable = True
                    mx_reason = f"Found MX hosts: {hosts[:3]}"  # only include small sample
                else:
                    mx_reason = "No MX hosts found for domain."
            except Exception as e:
                mx_reason = f"MX lookup attempted but failed: {e}"
        except Exception:
            mx_checked = False
            mx_reason = "dnspython is not installed or DNS lookup not permitted in this environment."

    return {
        "valid": True,
        "reason": "Email passed syntactic checks." if not check_mx else f"Email syntactically valid; {mx_reason}",
        "mx_checked": mx_checked,
        "deliverable": deliverable,
    }


def check_documents(client_id: str, required_documents: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Check the presence and completion of required documents for a client.

    Because this agent runs without a backing database in this repo, this function acts as a deterministic validator
    that returns a structured checklist. Integration with a real datastore should replace the placeholder logic.

    Returns: {
      client_id: str,
      documents: [{ name, present, completed, notes }],
      all_completed: bool
    }
    """
    if not client_id:
        return {"error": "client_id is required for document checks."}

    default_docs = ["id_card", "proof_of_address", "proof_of_income"]
    docs = required_documents or default_docs

    result_docs = []
    all_completed = True

    # Placeholder behavior: mark documents as missing so the approval agent is conservative.
    for d in docs:
        entry = {"name": d, "present": False, "completed": False, "notes": "Document not found in the system. Please upload or mark as provided."}
        result_docs.append(entry)
        all_completed = False

    return {"client_id": client_id, "documents": result_docs, "all_completed": all_completed}


# client_approval_remote_agent = lambda: RemoteA2aAgent(
#     name = "client_approval_agent",
#     description = "Remote A2A wrapper that validates the updated data for the client",
#     agent_card = ("client-approval-agent.json")
# )

# Restore simple RemoteA2aAgent factory and remove the manual pool implementation.
client_approval_remote_agent = lambda: RemoteA2aAgent(
    name = "client_approval_agent",
    description = "Remote A2A wrapper that validates the updated data for the client",
    agent_card = ("client-approval-agent.json")
)

# Root agent definition with the validation tools attached
root_agent = Agent(
    name = "client_approval_agent",
    model = os.getenv("MODEL"),
    description = "An agent that reviews and approves updated client information before finalizing changes in the system.",
    instruction="""
You are a Client Approval Agent responsible for reviewing and validating updated client information before changes are committed.

Capabilities (tools):
- verify_name(full_name) -> { valid: bool, reason: str, normalized?: str }
- verify_email(email, check_mx=False) -> { valid: bool, reason: str, mx_checked: bool, deliverable: bool }
- check_documents(client_id, required_documents=None) -> { client_id: str, documents: [{ name, present, completed, notes }], all_completed: bool }

Validation rules (summary):
- Name: at least two tokens, each >= 2 characters, only letters, hyphens and apostrophes.
- Email: robust regex validation; optional MX check when environment supports DNS lookups (mx_checked indicates whether MX lookup was performed).
- Documents: if required_documents is omitted, a conservative default checklist is used; the function returns presence/completion status and notes for missing items.

When uncertain, take the conservative path (mark invalid/missing) and provide clear reasons. Do not expose secrets or unnecessary PII in responses.
""",
    tools=[verify_name, verify_email, check_documents],
    planner = default_planner,
    generate_content_config = default_generate_cfg,
)