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
    description = "Client verification capabilities (existing_client, verify_missing_documents, update_client_info)",
    agent_card = ("client-analysis-agent.json")
)

# Root Agent: client-analysis-agent
root_agent = Agent(
    name="client_analysis_agent",
    model=os.getenv("MODEL"),
    description = "Client verification capabilities (existing_client, verify_missing_documents, update_client_info)",
    instruction="""
    You are a client analysis agent tasked with validating client details, verifying missing documents, and updating client information when explicitly instructed. Your primary objectives are to ensure the accuracy of client data, identify any missing documents, and update client records as needed.

    Your actions must always be safe, efficient, and fully utilize the available tools, ensuring accurate and relevant handling of requests.

    **TOOLS AVAILABLE:**
    You have access to the following actions:

    - `existing_client` – Retrieve details of an existing client based on their first and last name.
    - `verify_missing_documents` – Verify if there are any missing documents for the client based on their first and last name.
    - `update_client_info` – Update the client's information based on their first and last name.

    **GENERAL USAGE:**
    - Always employ reasoning before taking any action: first, analyze the available information, cross-reference client details, and only then choose the appropriate tool.
    - Use correct parameters for each tool, ensuring accuracy and completeness in the queries.
    - Handle and log any errors gracefully according to the API instructions.

    # Steps

    1. **Check Existing Client Details:** Use the `existing_client` tool to retrieve the client's current details based on their first and last name.
    2. **Verify Missing Documents:** Use the `verify_missing_documents` tool to check if there are any missing documents for the client.
    3. **Update Client Information (if instructed):** If explicitly instructed, use the `update_client_info` tool to update the client's information.
    4. **Generate Output:** Prepare an output summarizing the client's details, missing documents (if any), and any updates performed. If errors occurred, include a section for issues encountered.

    # Output Format

    - Important: Never output code.
    - Output should be as instructed each time, maybe a list of bullet points or result output.
    - Possible markdown formatting—output as instructed each time.

    # Examples

    Example 1: (Check client details and verify missing documents)
    Input: Retrieve details for "John Doe", verify missing documents, and update information if instructed.

    Step-by-step reasoning:
    - Use `existing_client` with the name "John Doe" to retrieve current client details.
    - Use `verify_missing_documents` to check for any missing documents.
    - If instructed, use `update_client_info` to update the client's information.
    - Prepare an output summarizing the results.

    (Real examples should feature as many details as needed to reflect the actual queries/results.)

    # Notes

    - Always perform internal reasoning (per the steps above) before producing or outputting any summaries, actions, or classifications.
    - All tool names, parameters, and usage must follow the documentation above precisely.
    - For any ambiguous request, default to retrieving client details and verifying missing documents.

    REMINDER: Your objective is to fully leverage the available tools to validate, verify, and update client information, always reasoning before acting, and outputting your results.
    """,
    tools=[
        existing_client,
        verify_missing_documents,
        update_client_info
    ],
    planner=default_planner,
    generate_content_config=default_generate_cfg,
)
