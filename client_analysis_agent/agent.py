import os

from dotenv import load_dotenv
from google import genai
from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.planners import BuiltInPlanner
from google.genai import types

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

def existing_client(first_name: str, last_name: str) -> dict:
    """
    Retrieve details of an existing client based on their first and last name.

    Parameters:
        first_name (str): The first name of the client.
        last_name (str): The last name of the client.

    Returns:
        dict: A dictionary containing the client's details.
    """
    return {
        "first_name": "Keith",
        "last_name": "Rodgers",
        "address": "1234 K ST NYC NY 10001",
        "sex": "m",
        "date_of_birth": "01/12/85",
        "nationality": "usa",
        "height": "5'07\"",
        "weight": "130",
        "eye_color": "brn",
        "date_issued": "05/01/15",
        "date_expires": "05/31/15",
        "issuing_agency": "uav control",
        "email_address": "keith.rodgers.174813974139@yahoo.com"
    }

def verify_missing_documents(first_name: str, last_name: str) -> dict:
    """
    Verify if there are any missing documents for the client based on their first and last name.

    Parameters:
        first_name (str): The first name of the client.
        last_name (str): The last name of the client.

    Returns:
        dict: A dictionary indicating no missing documents.
    """
    return {
        "first_name": first_name,
        "last_name": last_name,
        "missing_documents": []
    }

def update_client_info(first_name: str, last_name: str) -> dict:
    """
    Update the client's information based on their first and last name.

    Parameters:
        first_name (str): The first name of the client.
        last_name (str): The last name of the client.

    Returns:
        dict: A dictionary indicating the update was successful.
    """
    return {
        "first_name": first_name,
        "last_name": last_name,
        "status": "Update successful"
    }

# Remote A2A agent factory for the client verification agent
client_verification_remote_agent = lambda: RemoteA2aAgent(
    name = "client_analysis_agent",
    description = "Remote A2A wrapper exposing the client verification capabilities (verify_name, verify_email, check_documents) defined in agent.json",
    agent_card = ("client-analysis-agent.json")
)

# Root Agent: client-analysis-agent
root_agent = Agent(
    name = "client_analysis_agent",
    model = os.getenv("MODEL"),
    description = "Agent that validates client name and email, and checks whether required client documents are present and completed.",
    instruction="""
You are the Client Verification Agent. Your responsibilities and capabilities mirror the agent.json manifest.

Capabilities (functions):
- verify_name(name): Validate a client's full name according to expected rules (letters, spaces, hyphens, apostrophes, minimum token length and at least two name tokens).
- verify_email(email, check_mx): Validate an email address syntactically; if check_mx is true and the environment allows, attempt an MX/deliverability check and report results.
- check_documents(client_id, required_documents): Check the client's documents against a checklist. If required_documents is omitted, use a sensible default checklist appropriate for the product.

Input / Output contract:
- verify_name -> { valid: bool, reason: str }
- verify_email -> { valid: bool, reason: str, mx_checked: bool, deliverable: bool }
- check_documents -> { client_id: str, documents: [{ name, present, completed, notes }], all_completed: bool }

Processing rules:
1. Always validate and normalize inputs (trim/normalize whitespace).
2. For name validation: require at least two name tokens, each token of length >= 2, allow letters, spaces, hyphens and apostrophes. Return a human-readable reason if invalid.
3. For email validation: perform robust regex validation. If check_mx is true, attempt MX lookup only when DNS/network access is available; set mx_checked accordingly and include a deliverable boolean. If MX lookup is not possible, set mx_checked to false and explain in reason.
4. For document checks: accept an explicit required_documents list or use a default; attempt to locate each required item (presence/completion). Populate notes for any missing or partially-complete items; set all_completed true only when every required document is present and completed.
5. Error handling: return structured error information and avoid raising uncaught exceptions. Log non-sensitive diagnostics when helpful.

Privacy & Safety:
- Do not exfiltrate secrets or unnecessary PII. Return only the structured verification outputs.
- When uncertain, prefer conservative results (e.g., mark as invalid) and provide clear reasoning.

If inputs are ambiguous or missing required fields (for example, missing client_id for document checks), ask for the missing data before proceeding.
""",
    tools=[existing_client, update_client_info, verify_missing_documents],
    planner = default_planner,
    generate_content_config = default_generate_cfg,
)
