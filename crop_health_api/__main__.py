import asyncio
import pathlib
from contextlib import asynccontextmanager

import requests
from fastapi import FastAPI, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

from crop_health_api.custom_openapi import custom_openapi_gen
from crop_health_api.settings import settings

example_code_dir = pathlib.Path(__file__).parent / "example_code"
openapi_json_cache = None


@asynccontextmanager
async def app_lifespan(app):
    global openapi_json_cache
    # Try to reach TorchServe's /ping endpoint with retries
    # If running docker containers locally, use "http://torchserve:8080" given
    # that "torchserve" is the name of the container running custom TorchServe
    if settings.api_domain == "localhost":
        torchserve_domain = "torchserve"
    else:
        torchserve_domain = "localhost"
    max_retries = 10
    retry_delay = 5  # seconds
    for _ in range(max_retries):
        try:
            response = requests.get(f"http://{torchserve_domain}:8080/ping")
            if response.status_code == 200:
                print("TorchServe is up and running!")
                break
            else:
                raise Exception(
                    f"TorchServe is not ready. Status code: {response.status_code}"
                )
        except (requests.exceptions.ConnectionError, Exception) as e:
            print(
                f"Waiting for TorchServe to be available: {e}. Retrying in {retry_delay} seconds."
            )
            await asyncio.sleep(retry_delay)
    response = requests.options(f"http://{torchserve_domain}:8080", timeout=10)
    if response.status_code == 200:
        openapi_json = response.json()
        # Remove specific endpoints if needed
        endpoints_to_keep = ["/ping"]
        all_endpoints = list(openapi_json["paths"].keys())
        for endpoint in all_endpoints:
            if endpoint not in endpoints_to_keep:
                del openapi_json["paths"][endpoint]

        # Initializing custom endpoints we want to show in the openapi docs
        custom_endpoints = [
            "/predictions/binary",
            "/predictions/single-HLT",
            "/predictions/multi-HLT",
        ]
        for endpoint in custom_endpoints:
            openapi_json["paths"][endpoint] = {"post": {"responses": {}}}

        openapi_json = custom_openapi_gen(openapi_json, example_code_dir)
        openapi_json_cache = openapi_json
    else:
        raise Exception("Failed to load OpenAPI JSON from TorchServe")
    yield


app = FastAPI(
    openapi_url=None,
    lifespan=app_lifespan,
    root_path=settings.api_root_path,
)


@app.get("/openapi.json")
async def get_openapi_json():
    if openapi_json_cache:
        return openapi_json_cache
    else:
        raise HTTPException(status_code=500, detail="OpenAPI JSON is not loaded")


@app.get("/redoc", response_class=HTMLResponse)
async def redoc():
    redoc_html = f"""
    <!DOCTYPE html>
    <html>
    <body>
        <!-- Redoc script that builds the page from OpenAPI spec -->
        <redoc spec-url='{settings.api_url}/openapi.json'></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """
    return redoc_html


@app.get("/docs", include_in_schema=False)
async def docs():
    return get_swagger_ui_html(
        openapi_url=f"{settings.api_root_path}/openapi.json",
        title="Geocoder API",
        swagger_favicon_url="https://www.openepi.io/favicon.ico",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.uvicorn_host, port=settings.uvicorn_port)
