import os

from dotenv import load_dotenv
from google import genai
from google.adk.agents import Agent, SequentialAgent, LoopAgent, ParallelAgent
from google.adk.planners import BuiltInPlanner
from google.genai import types

from client_analysis_agent.agent import client_verification_remote_agent
from client_approval_agent.agent import client_approval_remote_agent
from client_comms_agent.agent import client_comms_remote_agent
from comms_approval_agent.agent import comms_approval_remote_agent
from interpol_guard_agent.agent import interpol_remote_agent

load_dotenv()

current_environment = os.getenv("ENV")

project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
bucket_name = f"gs://{project_id}-bucket"
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

validator_loop = LoopAgent(
    name="client_validator_loop",
    sub_agents=[client_approval_remote_agent()],
    max_iterations=4
).to_agent()

# inner sequential: analysis then repeated validation
analysis_then_validation = SequentialAgent(
    name="analysis_then_validation",
    sub_agents=[client_verification_remote_agent(), validator_loop]
)

# parallel: run analysis+validation sequence in parallel with interpol guard
analysis_and_guard_parallel = ParallelAgent(
    name="analysis_and_guard_parallel",
    sub_agents=[analysis_then_validation, interpol_remote_agent()]
)

# top-level KYC workflow as requested
kyc_workflow = SequentialAgent(
    name="kyc_workflow_agent",
    sub_agents=[analysis_and_guard_parallel, client_comms_remote_agent(), comms_approval_remote_agent()]
)

root_agent = Agent(
    name="master_agent",
    model=os.getenv("MODEL"),
    description="Orchestrates and controls the workflow, delegating tasks to other agents.",
    instruction="""
    You are a manager that is responsible for overseeing the work of the other agents.

    Always delegate tasks to the appropriate sub-agent to complete the work. Use your best judgement to determine which 
    sub-agent is best suited for each task.

    You are reponsible dor delegating tasks to the following agents:
    - client_analysis_agent
    - client_approval_agent
    - client_comms_agent
    - comms_approval_agent
    - interpol_guard_agent
    """,
    sub_agents=[kyc_workflow],
    planner=default_planner,
    generate_content_config=default_generate_cfg,
)