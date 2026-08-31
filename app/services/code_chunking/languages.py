LANGUAGE_CONFIG = {
    "py": {
        "ts_language": "python",
        "top_level_types": {"function_definition", "class_definition"},
        "container_types": {"class_definition"},
        "container_body_wrapper": "block",
        "method_types": {"function_definition"},
        "body_pairing": {},
    },
    "js": {
        "ts_language": "javascript",
        "top_level_types": {"function_declaration", "class_declaration"},
        "container_types": {"class_declaration"},
        "container_body_wrapper": "class_body",
        "method_types": {"method_definition"},
        "body_pairing": {},
    },
    "jsx": {
        "ts_language": "javascript",
        "top_level_types": {"function_declaration", "class_declaration"},
        "container_types": {"class_declaration"},
        "container_body_wrapper": "class_body",
        "method_types": {"method_definition"},
        "body_pairing": {},
    },
    "ts": {
        "ts_language": "typescript",
        "top_level_types": {"function_declaration", "class_declaration"},
        "container_types": {"class_declaration"},
        "container_body_wrapper": "class_body",
        "method_types": {"method_definition"},
        "body_pairing": {},
    },
    "tsx": {
        "ts_language": "tsx",
        "top_level_types": {"function_declaration", "class_declaration"},
        "container_types": {"class_declaration"},
        "container_body_wrapper": "class_body",
        "method_types": {"method_definition"},
        "body_pairing": {},
    },
    "dart": {
        "ts_language": "dart",
        "top_level_types": {"function_signature", "class_definition"},
        "container_types": {"class_definition"},
        "container_body_wrapper": "class_body",
        "method_types": {"method_signature"},
        "body_pairing": {
            "function_signature": "function_body",
            "method_signature": "function_body",
        },
    },
}


def get_language_config(extension: str) -> dict | None:
    return LANGUAGE_CONFIG.get(extension.lstrip("."))
