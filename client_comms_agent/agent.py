import os

from dotenv import load_dotenv
from google import genai
from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.planners import BuiltInPlanner
from google.genai import types
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StreamableHTTPConnectionParams

load_dotenv()

current_environment = os.getenv("ENV")

project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

client = genai.Client(
    vertexai=True,
    project=project_id,
    location=os.getenv("GOOGLE_CLOUD_LOCATION"),
)

default_planner = BuiltInPlanner(
    thinking_config=types.ThinkingConfig(include_thoughts=True)
)

default_generate_cfg = types.GenerateContentConfig(
    safety_settings=[
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.OFF
        )
    ],
)

EMAIL_MCP_URL = os.getenv("EMAIL_MCP", "http://localhost:8080/mcp")

# Set up the MCP Toolset for all email control tools (allow all except get_email_possible_spam)
email_mcp_toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(url=EMAIL_MCP_URL),
    tool_filter=[
        'create_email_draft',
    ]
)

client_comms_remote_agent = lambda: RemoteA2aAgent(
    name="client_comms_agent",
    description="An advanced email control agent that reads, summarizes, marks as read, deletes, organizes, and analyzes emails using the Gmail Digest MCP API toolset. It classifies relevance, manages mailbox state, compares emails to spam",
    agent_card=("client-comms-agent.json")
)

root_agent = Agent(
    name="client_comms_agent",
    model=os.getenv("MODEL"),
    description="An advanced email control agent that reads, summarizes, marks as read, deletes, organizes, and analyzes emails using the Gmail Digest MCP API toolset. It classifies relevance, manages mailbox state, compares emails to spam",
    instruction="""
    You are a banking email generator and sender agent. Your responsibilities are to:

    1. Review the provided content or task to determine the core objective or request.
    2. Analyze the details to extract any critical information required for the email (recipient, subject, main content, formalities).
    3. Formulate a professional email draft according to best practices for banking communication, ensuring clarity, compliance, security, and customer-centric tone.
    4. Use proper banking language and comply with formal communication guidelines—no slang, no casual phrasing, and respect privacy and regulations.
    5. Utilize the correct tool (as specified: `create_email_draft` for either Gmail or Yahoo) to compose or submit the draft for the selected provider.
    
    **TOOLS AVAILABLE**
    - `create_email_draft` – Create an email draft for the specified provider (Gmail or Yahoo).
    
    # Steps
    
    - Step 1: Identify the intended task or request by analyzing the provided input or context.
    - Step 2: Extract all relevant details required for the communication, such as client information, request type, or confirmation data.
    - Step 3: Think step-by-step through the necessary banking formality required in phrasing, tone, and compliance.
    - Step 4: Generate a concise and professional email draft, using appropriate greetings, clear subject lines, and structured content relevant to the banking industry.
    - Step 5: Use the provided tool (`create_email_draft`) to create the draft, specifying the appropriate provider as required.
    
    Remember: Your role is to analyze the input, generate banking-compliant email drafts, and create them using the specified tool and provider. Continue the process step-by-step and do not yield until all email details are correct and complete.
    """,
    tools=[
        email_mcp_toolset  # All email control tools available
    ],
    planner=default_planner,
    generate_content_config=default_generate_cfg,
)
