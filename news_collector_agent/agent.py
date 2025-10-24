import os

from dotenv import load_dotenv
from google import genai
from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.planners import BuiltInPlanner
from google.genai import types

from google.adk.tools import google_search

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


news_collector_remote_agent = lambda: RemoteA2aAgent(
    name = "news_collector_agent",
    description = "Uses Google Search to collect news articles and summarizes them.",
    agent_card = ("news-collector-agent.json")
)

root_agent = Agent(
    name = "news_collector_agent",
    model = os.getenv("MODEL"),
    description="Uses Google Search to collect news articles and summarizes them.",
    instruction="""
    1. Search for recent news articles using Google Search based .
    2. Summarize the collected news articles into concise, readable reports.
    3. Ensure the summary is clear and highlights the most important information from the articles.
    4. Always just return the news summary that you have created, nothing else that you need to do.
    """,
    tools=[google_search],
    planner=default_planner,
    generate_content_config=default_generate_cfg,
)