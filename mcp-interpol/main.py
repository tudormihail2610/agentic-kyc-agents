import asyncio
import logging
import os

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()
logger = logging.getLogger(__name__)

logging.basicConfig(format="[%(levelname)s: %(message)s", level=logging.INFO)

base_dir = os.path.dirname(os.path.abspath(__file__))

OPENAPI_SPEC_PATH = os.path.join(base_dir, "resources/openapi.yaml")
API_BASE_URL = "https://ws-public.interpol.int/notices/v1"

mcp = None
client = None


def load_openapi_spec(openapi_spec_path):
    import yaml
    with open(openapi_spec_path, 'r') as file:
        spec = yaml.safe_load(file)
    return spec


def log_openapi_spec_info(spec):
    num_paths = len(spec.get('paths', {}))
    logger.info(f"OpenAPI spec contains {num_paths} paths.")
    sample_paths = list(spec.get('paths', {}).keys())[:10]
    logger.info(f"Sample paths: {sample_paths}")


async def init_mcp():
    global mcp, client
    spec = load_openapi_spec(OPENAPI_SPEC_PATH)
    log_openapi_spec_info(spec)

    client = httpx.AsyncClient(base_url=API_BASE_URL, headers={"Cookie": '" "'})

    mcp = FastMCP.from_openapi(
        openapi_spec=spec,
        client=client,
        name="mcp-interpol"
    )

    @mcp.tool()
    async def health():
        """Health check endpoint."""
        return load_mock_data()

    @mcp.tool()
    async def check_user(first_name: str, last_name: str):
        """Check if a user exists in the mock data based on first name and last name."""
        return load_mock_data()

    # Helper function to load mock data from mock.json
    def load_mock_data():
        mock_file_path = os.path.join(base_dir, "resources/mock.json")
        with open(mock_file_path, "r", encoding="utf-8") as mock_file:  # Added encoding="utf-8"
            import json
            return json.load(mock_file)

    return mcp, client


def run_mcp(port=8090):
    global mcp, client
    mcp, client = asyncio.run(init_mcp())

    if mcp is None:
        raise RuntimeError("MCP is not initialized. Call init_mcp() first.")

    mcp.run(host="0.0.0.0", transport="http", port=port)
