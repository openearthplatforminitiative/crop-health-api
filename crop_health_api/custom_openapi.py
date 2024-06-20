import logging
import os
from pathlib import Path
from string import Template

from crop_health_api.settings import settings

supported_languages = {"cURL": "sh", "JavaScript": "js", "Python": "py"}


def custom_openapi_gen(openapi_schema: dict, example_code_dir: Path):
    openapi_schema["info"]["title"] = settings.title
    openapi_schema["info"]["version"] = settings.version
    openapi_schema["info"]["description"] = settings.api_description
    openapi_schema["servers"] = [{"url": settings.api_url}]

    # Manually modify the schema for the /predictions/{model_name} endpoint
    endpoint_paths = [
        ("/predictions/binary", "Binary"),
        ("/predictions/single-HLT", "SingleHLT"),
        ("/predictions/multi-HLT", "MultiHLT"),
    ]
    method = "post"

    # Manually define the schema for each model response
    for endpoint_path, type_predicate in endpoint_paths:
        if (
            endpoint_path in openapi_schema["paths"]
            and method in openapi_schema["paths"][endpoint_path]
        ):
            # Main description
            openapi_schema["paths"][endpoint_path][method] = {
                "description": f"Health predictions by the {type_predicate} model.",
                "operationId": f"predictions_with_{type_predicate}",
                "requestBody": {
                    "description": "Picture of a plant.",
                    "content": {
                        "*/*": {"schema": {"type": "string", "format": "binary"}}
                    },
                    "required": "true",
                },
            }

            # Errors
            openapi_schema["paths"][endpoint_path][method]["responses"] = {
                "404": {
                    "description": "Model not found or Model Version not found",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["code", "type", "message"],
                                "properties": {
                                    "code": {
                                        "type": "integer",
                                        "description": "Error code.",
                                    },
                                    "type": {
                                        "type": "string",
                                        "description": "Error type.",
                                    },
                                    "message": {
                                        "type": "string",
                                        "description": "Error message.",
                                    },
                                },
                            }
                        }
                    },
                },
                "500": {
                    "description": "Internal Server Error",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["code", "type", "message"],
                                "properties": {
                                    "code": {
                                        "type": "integer",
                                        "description": "Error code.",
                                    },
                                    "type": {
                                        "type": "string",
                                        "description": "Error type.",
                                    },
                                    "message": {
                                        "type": "string",
                                        "description": "Error message.",
                                    },
                                },
                            }
                        }
                    },
                },
                "503": {
                    "description": "No worker is available to serve request",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["code", "type", "message"],
                                "properties": {
                                    "code": {
                                        "type": "integer",
                                        "description": "Error code.",
                                    },
                                    "type": {
                                        "type": "string",
                                        "description": "Error type.",
                                    },
                                    "message": {
                                        "type": "string",
                                        "description": "Error message.",
                                    },
                                },
                            }
                        }
                    },
                },
            }

            # Successful reponse
            openapi_schema["paths"][endpoint_path][method]["responses"]["200"] = {
                "description": (
                    "Predicted class confidences, all summing to 1.0. Actual class names and number of returned classes may vary.",
                ),
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "$ref": f"#/components/schemas/{type_predicate}HealthPredictionResponse",
                        }
                    }
                },
            }

    # The returntypes of each endpoint
    openapi_schema["components"] = {
        "schemas": {
            "BinaryHealthPredictionResponse": {
                "type": "object",
                "properties": {
                    "HLT": {"type": "number"},
                    "NOT_HLT": {"type": "number"},
                },
                "example": {"HLT": 0.85, "NOT_HLT": 0.15},
            },
            "SingleHLTHealthPredictionResponse": {
                "type": "object",
                "properties": {
                    "HLT": {"type": "number"},
                    "CBSD": {"type": "number"},
                    "CMD": {"type": "number"},
                    "MLN": {"type": "number"},
                    "MSV": {"type": "number"},
                    "FAW": {"type": "number"},
                    "MLB": {"type": "number"},
                    "BR": {"type": "number"},
                    "ALS": {"type": "number"},
                    "BS": {"type": "number"},
                    "FW": {"type": "number"},
                    "ANT": {"type": "number"},
                    "CSSVD": {"type": "number"},
                },
                "example": {
                    "HLT": 0.9110000729560852,
                    "FAW": 0.05462193489074707,
                    "CSSVD": 0.025387784466147423,
                    "FW": 0.004624366760253906,
                    "MSV": 0.001886515412479639,
                },
            },
            "MultiHLTHealthPredictionResponse": {
                "type": "object",
                "properties": {
                    "HLT_cassava": {"type": "number"},
                    "CBSD_cassava": {"type": "number"},
                    "CMD_cassava": {"type": "number"},
                    "MLN_maize": {"type": "number"},
                    "HLT_maize": {"type": "number"},
                    "MSV_maize": {"type": "number"},
                    "FAW_maize": {"type": "number"},
                    "MLB_maize": {"type": "number"},
                    "HLT_beans": {"type": "number"},
                    "BR_beans": {"type": "number"},
                    "ALS_beans": {"type": "number"},
                    "HLT_bananas": {"type": "number"},
                    "BS_bananas": {"type": "number"},
                    "FW_bananas": {"type": "number"},
                    "HLT_cocoa": {"type": "number"},
                    "ANT_cocoa": {"type": "number"},
                    "CSSVD_cocoa": {"type": "number"},
                },
                "example": {
                    "HLT_cocoa": 0.27080613374710083,
                    "HLT_bananas": 0.1852046251296997,
                    "FAW_maize": 0.15339095890522003,
                    "HLT_maize": 0.12040198594331741,
                    "FW_bananas": 0.11432896554470062,
                },
            },
        }
    }

    # Derive the API routes from the OpenAPI schema
    api_routes = list(openapi_schema["paths"].keys())
    # remove leading slashes from the routes
    api_routes = [route.lstrip("/") for route in api_routes]

    for route in api_routes:
        code_samples = get_code_samples(route, example_code_dir)
        if code_samples:
            # add leading slashes back to the routes
            route = "/" + route
            if "get" in openapi_schema["paths"][route]:
                openapi_schema["paths"][route]["get"]["x-codeSamples"] = code_samples
            elif "post" in openapi_schema["paths"][route]:
                openapi_schema["paths"][route]["post"]["x-codeSamples"] = code_samples

    return openapi_schema


def get_code_samples(route: str, example_code_dir: Path):
    code_samples = []
    normalized_route_name = route.replace("/", "__")
    for lang, file_ext in supported_languages.items():
        file_with_code_sample = (
            example_code_dir / lang.lower() / f"{normalized_route_name}.{file_ext}"
        )
        print(file_with_code_sample)
        if os.path.isfile(file_with_code_sample):
            with open(file_with_code_sample) as f:
                code_template = Template(f.read())
                code_samples.append(
                    {
                        "lang": lang,
                        "source": code_template.safe_substitute(
                            api_url=settings.api_url,
                        ),
                    }
                )
        else:
            logging.warning(
                "No code sample found for route %s and language %s",
                route,
                lang,
            )
    return code_samples
