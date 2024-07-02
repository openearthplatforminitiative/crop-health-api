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
                "description": "Predicted class confidences, all summing to 1.0.",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "$ref": f"#/components/schemas/{type_predicate}PredictionResponse",
                        }
                    }
                },
            }

    # The returntypes of each endpoint
    openapi_schema["components"] = {
        "schemas": {
            "BinaryPredictionResponse": {
                "type": "object",
                "properties": {
                    "HLT": {"type": "number", "description": "Healthy"},
                    "NOT_HLT": {"type": "number", "description": "Not Healthy"},
                },
                "required": ["HLT", "NOT_HLT"],
                "example": {"HLT": 0.85, "NOT_HLT": 0.15},
            },
            "SingleHLTPredictionResponse": {
                "type": "object",
                "properties": {
                    "HLT": {"type": "number", "description": "Healthy"},
                    "CBSD": {
                        "type": "number",
                        "description": "Cassava Brown Streak Disease",
                    },
                    "CMD": {"type": "number", "description": "Cassava Mosaic Disease"},
                    "MLN": {"type": "number", "description": "Maize Lethal Necrosis"},
                    "MSV": {"type": "number", "description": "Maize Streak Virus"},
                    "FAW": {"type": "number", "description": "Fall Armyworm"},
                    "MLB": {"type": "number", "description": "Maize Leaf Blight"},
                    "BR": {"type": "number", "description": "Bean Rust"},
                    "ALS": {"type": "number", "description": "Angular Leaf Spot"},
                    "BS": {"type": "number", "description": "Black Sigatoka"},
                    "FW": {"type": "number", "description": "Fusarium Wilt Race 1"},
                    "ANT": {"type": "number", "description": "Anthracnose"},
                    "CSSVD": {
                        "type": "number",
                        "description": "Cocoa Swollen Shoot Virus Disease",
                    },
                },
                "required": [
                    "HLT",
                    "CBSD",
                    "CMD",
                    "MLN",
                    "MSV",
                    "FAW",
                    "MLB",
                    "BR",
                    "ALS",
                    "BS",
                    "FW",
                    "ANT",
                    "CSSVD",
                ],
                "example": {
                    "HLT": 0.8450168371200562,
                    "CSSVD": 0.14720021188259125,
                    "ANT": 0.007312592584639788,
                    "CMD": 0.00043629767606034875,
                    "BR": 1.8495124095352367e-05,
                    "CBSD": 6.3890015553624835e-06,
                    "FW": 3.867091891152086e-06,
                    "FAW": 3.0916353352949955e-06,
                    "ALS": 1.4288182228483493e-06,
                    "MSV": 6.82656491335365e-07,
                    "MLB": 1.0789210591610754e-07,
                    "BS": 1.5242493489608933e-08,
                    "MLN": 1.5041418111039206e-09
                },
            },
            "MultiHLTPredictionResponse": {
                "type": "object",
                "properties": {
                    "HLT_cassava": {"type": "number", "description": "Healthy Cassava"},
                    "CBSD_cassava": {
                        "type": "number",
                        "description": "Cassava Brown Streak Disease",
                    },
                    "CMD_cassava": {
                        "type": "number",
                        "description": "Cassava Mosaic Disease",
                    },
                    "MLN_maize": {
                        "type": "number",
                        "description": "Maize Lethal Necrosis",
                    },
                    "HLT_maize": {"type": "number", "description": "Healthy Maize"},
                    "MSV_maize": {
                        "type": "number",
                        "description": "Maize Streak Virus",
                    },
                    "FAW_maize": {"type": "number", "description": "Fall Armyworm"},
                    "MLB_maize": {"type": "number", "description": "Maize Leaf Blight"},
                    "HLT_beans": {"type": "number", "description": "Healthy Beans"},
                    "BR_beans": {"type": "number", "description": "Bean Rust"},
                    "ALS_beans": {"type": "number", "description": "Angular Leaf Spot"},
                    "HLT_bananas": {"type": "number", "description": "Healthy Bananas"},
                    "BS_bananas": {"type": "number", "description": "Black Sigatoka"},
                    "FW_bananas": {
                        "type": "number",
                        "description": "Fusarium Wilt Race 1",
                    },
                    "HLT_cocoa": {"type": "number", "description": "Healthy Cocoa"},
                    "ANT_cocoa": {"type": "number", "description": "Anthracnose"},
                    "CSSVD_cocoa": {
                        "type": "number",
                        "description": "Cocoa Swollen Shoot Virus Disease",
                    },
                },
                "required": [
                    "HLT_cassava",
                    "CBSD_cassava",
                    "CMD_cassava",
                    "MLN_maize",
                    "HLT_maize",
                    "MSV_maize",
                    "FAW_maize",
                    "MLB_maize",
                    "HLT_beans",
                    "BR_beans",
                    "ALS_beans",
                    "HLT_bananas",
                    "BS_bananas",
                    "FW_bananas",
                    "HLT_cocoa",
                    "ANT_cocoa",
                    "CSSVD_cocoa",
                ],
                "example": {
                    "HLT_cocoa": 0.4922555685043335,
                    "CSSVD_cocoa": 0.31238827109336853,
                    "HLT_beans": 0.1199931725859642,
                    "HLT_maize": 0.055395256727933884,
                    "ANT_cocoa": 0.008309438824653625,
                    "BR_beans": 0.005891730077564716,
                    "HLT_bananas": 0.002898828824982047,
                    "ALS_beans": 0.0012257732450962067,
                    "CMD_cassava": 0.0009540125029161572,
                    "HLT_cassava": 0.0003349129983689636,
                    "FAW_maize": 0.00016859767492860556,
                    "CBSD_cassava": 0.00010111751180374995,
                    "MSV_maize": 3.91885478165932e-05,
                    "FW_bananas": 2.3203281671158038e-05,
                    "MLB_maize": 2.0815876268898137e-05,
                    "MLN_maize": 8.257627115426658e-08,
                    "BS_bananas": 9.579996351760656e-09
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
