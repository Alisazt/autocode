"""
Guardrails engine for validating generated artifacts.

This simplified implementation uses JSON Schema to validate artifacts
of known types.  Only a single schema (for "architecture") is
provided in this prototype.  Additional schemas can be registered by
extending the `schemas` dictionary.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple, List

import jsonschema


class GuardrailsEngine:
    """Validate artifacts against predefined JSON schemas."""

    def __init__(self) -> None:
        # Define a minimal schema for an architecture artifact as per the
        # specification.  In a full system you would load these from
        # configuration or separate files.
        self.schemas: Dict[str, Dict[str, Any]] = {
            "architecture": {
                "type": "object",
                "required": ["nfr", "security", "api_spec", "adr_records"],
                "properties": {
                    "nfr": {
                        "type": "array",
                        "minItems": 5,
                        "items": {"type": "string", "minLength": 50},
                    },
                    "security": {
                        "type": "array",
                        "minItems": 3,
                        "items": {"type": "string"},
                    },
                    "api_spec": {
                        "type": "string",
                        "pattern": r".*openapi.*3\.[0-9].*",  # must contain OpenAPI 3.x
                    },
                    "adr_records": {
                        "type": "array",
                        "minItems": 3,
                        "items": {
                            "type": "object",
                            "required": ["title", "decision", "consequences"],
                            "properties": {
                                "title": {"type": "string"},
                                "decision": {"type": "string"},
                                "consequences": {"type": "string"},
                            },
                        },
                    },
                },
            }
        }

    def validate_artifact(self, artifact_type: str, content: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate `content` against the schema for `artifact_type`.

        Returns a tuple of (is_valid, errors).  If there is no schema
        registered for the given type the artifact is considered valid.
        """
        if artifact_type not in self.schemas:
            return True, []
        schema = self.schemas[artifact_type]
        try:
            jsonschema.validate(content, schema)
            return True, []
        except jsonschema.ValidationError as exc:
            return False, [str(exc)]
