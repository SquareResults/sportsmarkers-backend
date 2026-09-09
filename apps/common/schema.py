def add_error_responses(result, generator, request, public):
    """Document the shared DRF error envelope, including field validation details."""
    result["components"]["schemas"]["ApiError"] = {
        "type": "object",
        "required": ["error"],
        "properties": {
            "error": {
                "type": "object",
                "required": ["status", "details"],
                "properties": {"status": {"type": "integer"}, "details": {}},
            }
        },
    }
    for path in result["paths"].values():
        for method, operation in path.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            for code in ("400", "401", "403", "404", "405", "429"):
                operation["responses"].setdefault(
                    code,
                    {
                        "description": "API error with field errors or a detail message.",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ApiError"}
                            }
                        },
                    },
                )
    return result
