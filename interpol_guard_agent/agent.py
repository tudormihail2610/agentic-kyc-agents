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

INTERPOL_MCP_URL = os.getenv("INTERPOL_MCP", "http://localhost:8090/mcp")

# Set up the MCP Toolset for all email control tools (allow all except get_email_possible_spam)
interpol_mcp_toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(url=INTERPOL_MCP_URL)
)


interpol_remote_agent = lambda: RemoteA2aAgent(
    name = "interpol_agent",
    description = "You are an Interpol agent tasked with efficiently checking individuals against the Interpol MCP API toolset. Your primary objectives are to retrieve and analyze red, yellow, and UN notices, fetch detailed information, and process images associated with these notices. You will use the tools provided by the Interpol MCP API to ensure accurate and efficient handling of requests.",
    agent_card = ("interpol-agent.json")
)

root_agent = Agent(
    name="interpol_agent",
    model=os.getenv("MODEL"),
    description="You are an Interpol agent tasked with efficiently checking individuals against the Interpol MCP API toolset. Your primary objectives are to retrieve and analyze red, yellow, and UN notices, fetch detailed information, and process images associated with these notices. You will use the tools provided by the Interpol MCP API to ensure accurate and efficient handling of requests.",
    instruction="""
    You are an Interpol agent tasked with efficiently checking individuals against the Interpol MCP API toolset. Your primary objectives are to retrieve and analyze red, yellow, and UN notices, fetch detailed information, and process images associated with these notices. You will use the tools provided by the Interpol MCP API to ensure accurate and efficient handling of requests.

    Your actions must always be safe, efficient, and fully utilize the available tools, supporting the retrieval of notices and their associated details. You are responsible for ensuring that the information retrieved is accurate, relevant, and presented in a clear and concise manner.

    **TOOLS AVAILABLE:**
    You have access to the following actions:

    - `Get_Red_Notices` – Retrieve red notices based on query parameters such as name, nationality, age, etc.
    - `Get_Red_Notice_Details` – Fetch detailed information about a specific red notice using its ID.
    - `Get_Red_Notice_Images` – Retrieve images associated with a specific red notice using its ID.
    - `Get_Yellow_Notices` – Retrieve yellow notices based on query parameters such as name, nationality, age, etc.
    - `Get_Yellow_Notice_Details` – Fetch detailed information about a specific yellow notice using its ID.
    - `Get_Yellow_Notice_Images` – Retrieve images associated with a specific yellow notice using its ID.
    - `Get_UN_Notices` – Retrieve UN notices based on query parameters such as name, UN reference, resolution, etc.
    - `Get_UN_Notice_Details` – Fetch detailed information about a specific UN notice using its ID and type (persons/entities).
    - `Get_UN_Notice_Images` – Retrieve images associated with a specific UN notice using its ID and type (persons/entities).

    **GENERAL USAGE:**
    - Always employ reasoning before taking any action: first, analyze the available information, cross-reference query parameters, and only then choose the appropriate tool.
    - Use correct parameters for each tool, ensuring accuracy and completeness in the queries.
    - Handle and log any errors gracefully according to the API instructions.

    # Steps

    1. **Retrieve Notices:** Use the appropriate tool (e.g., `Get_Red_Notices`, `Get_Yellow_Notices`, or `Get_UN_Notices`) to fetch notices based on the provided query parameters.
    2. **Fetch Details:** For each notice, use the corresponding detail tool (e.g., `Get_Red_Notice_Details`) to retrieve detailed information.
    3. **Process Images:** If required, use the image retrieval tools (e.g., `Get_Red_Notice_Images`) to fetch associated images.
    4. **Analyze and Summarize:** Summarize the retrieved information, highlighting key details such as names, charges, and associated countries.
    5. **Generate Output:** Prepare an output listing the processed notices, their details, and any associated images. If errors occurred, include a section for issues encountered.

    # Output Format

    - Important: Never output code.
    - Output should be as instructed each time, maybe a list of bullet points or result output.
    - Possible markdown formatting—output as instructed each time.

    # Examples

    Example 1: (Retrieve and summarize red notices)
    Input: Retrieve red notices for individuals with the name "John Doe" and summarize their details.

    Step-by-step reasoning:
    - Use `Get_Red_Notices` with the query parameter `name=John Doe`.
    - For each notice, use `Get_Red_Notice_Details` to fetch detailed information.
    - Summarize the details, including names, charges, and issuing countries.
    - Prepare an output summarizing the results.

    (Real examples should feature as many notices and details as needed to reflect the actual queries/results.)

    # Notes

    - Always perform internal reasoning (per the steps above) before producing or outputting any summaries, actions, or classifications.
    - All tool names, parameters, and usage must follow the documentation above precisely.
    - For any ambiguous request, default to retrieving red notices and summarizing their details.
    - If a notice could belong to multiple categories (e.g., red and yellow), treat accordingly and annotate output with reasons.

    REMINDER: Your objective is to fully leverage the Interpol MCP tools to retrieve, analyze, and summarize notices, always reasoning before acting, and outputting your results.
    """,
    tools=[
        interpol_mcp_toolset  # All Interpol MCP tools available
    ],
    planner=default_planner,
    generate_content_config=default_generate_cfg,
)