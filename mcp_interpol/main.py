import asyncio
import logging
import os

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()
logger = logging.getLogger(__name__)

logging.basicConfig(format="[%(levelname)s: %(message)s", level=logging.INFO)

base_dir=os.path.dirname(os.path.abspath(__file__))

OPENAPI_SPEC_PATH = os.path.join(base_dir, "resources/openapi.yaml")
API_BASE_URL="https://ws-public.interpol.int/notices/v1"

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

    async def log_request_headers(request: httpx.Request):
        # Convert header keys to camel case
        # request.headers = {key.title(): value for key, value in request.headers.items()}
        if "User-Agent" in request.headers:
            del request.headers["User-Agent"]  # Remove the User-Agent header
        logger.info(f"Request Headers: {request.headers}")

    client.event_hooks = {
        "request": [log_request_headers]
    }

    mcp = FastMCP.from_openapi(
        openapi_spec=spec,
        client=client,
        name="mcp-interpol"
    )

    @mcp.tool()
    async def health():
        """Health check endpoint."""
        return {"status": "healthy"}

    @mcp.tool()
    async def debug():
        """Debug endpoint to test connectivity."""
        try:
            response = await client.get("/red?forename=MAX&name=Mustermann&nationality=DE&ageMax=120&ageMin=18&sexId=F&arrestWarrantCountryId=DE&page=1&resultPerPage=200")
            response.raise_for_status()  # Raise an error for HTTP status codes >= 400
            return {
                "status_code": response.status_code,
                "response": response.json() if response.content else {}
            }
        except httpx.RequestError as exc:
            return {
                "error": f"An error occurred while making the request: {str(exc)}"
            }
        except httpx.HTTPStatusError as exc:
            return {
                "error": f"HTTP error occurred: {str(exc)}",
                "status_code": exc.response.status_code,
                "response": exc.response.text
            }
        except ValueError as exc:
            return {
                "error": f"Failed to parse JSON response: {str(exc)}",
                "response_text": response.text if 'response' in locals() else None
            }

    return mcp, client

def run_mcp(port=8090):
    global mcp, client
    mcp, client = asyncio.run(init_mcp())

    if mcp is None:
        raise RuntimeError("MCP is not initialized. Call init_mcp() first.")

    mcp.run(host="0.0.0.0", transport="http", port=port)
