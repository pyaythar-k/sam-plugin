#!/usr/bin/env python3
"""
openapi_generator.py - Convert API specifications to OpenAPI 3.0

This script parses API specifications from TECHNICAL_SPEC.md and generates
OpenAPI 3.0 specification YAML files that can be used for:
- API documentation generation
- Client SDK generation
- Contract testing
- API validation

Usage:
    python3 skills/sam-specs/scripts/openapi_generator.py <feature_dir>
    python3 skills/sam-specs/scripts/openapi_generator.py .sam/001_user_auth

Output:
    Generates openapi.yaml in the feature directory
"""

import sys
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import yaml

# Import context resolver for variable interpolation
try:
    from context_resolver import ContextResolver
    CONTEXT_RESOLVER_AVAILABLE = True
except ImportError:
    CONTEXT_RESOLVER_AVAILABLE = False
    ContextResolver = None  # Type stub for when unavailable


@dataclass
class APIEndpoint:
    """Represents a single API endpoint."""
    method: str  # GET, POST, PUT, DELETE, PATCH
    path: str
    summary: str
    description: str = ""
    auth_required: bool = True
    request_body: Optional[Dict[str, Any]] = None
    response_success: Dict[str, Any] = field(default_factory=dict)
    response_errors: List[Dict[str, Any]] = field(default_factory=list)
    path_params: List[Dict[str, str]] = field(default_factory=list)
    query_params: List[Dict[str, str]] = field(default_factory=list)
    headers: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class APISchema:
    """Represents a JSON schema definition."""
    name: str
    type: str
    properties: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    required: List[str] = field(default_factory=list)
    description: str = ""


class OpenAPIGenerator:
    """Generate OpenAPI 3.0 specification from TECHNICAL_SPEC.md."""

    def __init__(self, spec_file: Path, feature_dir: Path, use_context: bool = True):
        self.spec_file = spec_file
        self.feature_dir = feature_dir
        self.feature_id = feature_dir.name
        self.content = ""
        self.lines: List[str] = []
        self.endpoints: List[APIEndpoint] = []
        self.schemas: Dict[str, APISchema] = {}
        self.use_context = use_context and CONTEXT_RESOLVER_AVAILABLE
        self.context_resolver: Optional[ContextResolver] = None

        if self.use_context:
            self.context_resolver = ContextResolver(self.feature_dir)
            try:
                self.context_resolver.load_context()
            except Exception as e:
                # Context loading is optional - log warning and continue
                print(f"  ⚠ Could not load context: {e}")
                self.use_context = False

    def resolve_context(self, template: str) -> str:
        """
        Resolve {{VARIABLE}} placeholders in a template string.

        Args:
            template: String containing potential placeholders

        Returns:
            String with placeholders resolved (if context available)
        """
        if self.use_context and self.context_resolver:
            return self.context_resolver.resolve_string(template)
        return template

    def parse(self) -> Dict[str, Any]:
        """Parse the technical specification and generate OpenAPI spec."""
        with open(self.spec_file, 'r') as f:
            self.content = f.read()
            self.lines = self.content.split('\n')

        # Extract metadata
        feature_name = self._extract_feature_name()

        # Parse API Specification section
        self._parse_api_section()

        # Generate OpenAPI spec
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": feature_name,
                "version": "1.0.0",
                "description": self._extract_description()
            },
            "servers": [
                {
                    "url": "http://localhost:3000",
                    "description": "Development server"
                }
            ],
            "paths": self._generate_paths(),
            "components": self._generate_components()
        }

        return openapi_spec

    def _extract_feature_name(self) -> str:
        """Extract feature name from spec."""
        for line in self.lines:
            match = re.match(r'#\s+Technical\s+Specification:\s*(.+)', line)
            if match:
                return match.group(1).strip()
        return self.feature_id.replace('_', ' ').title()

    def _extract_description(self) -> str:
        """Extract API description from spec."""
        # Look for a description near the API Specification section
        for i, line in enumerate(self.lines):
            if 'API Specification' in line:
                # Look ahead for description
                for j in range(i + 1, min(i + 10, len(self.lines))):
                    if self.lines[j].strip() and not self.lines[j].startswith('#'):
                        return self.lines[j].strip()
        return f"API for {self._extract_feature_name()}"

    def _parse_api_section(self):
        """Parse the API Specification section."""
        in_api_section = False
        current_resource = None
        current_method = None
        current_endpoint = None

        for i, line in enumerate(self.lines):
            # Check for API Specification section
            if 'API Specification' in line or 'API' in line and 'Specification' in line:
                in_api_section = True
                continue

            # Exit API section at next major section
            if in_api_section and line.startswith('# ') and 'API' not in line:
                break

            if not in_api_section:
                continue

            # Resource headers (### {RESOURCE_NAME})
            if line.startswith('### ') and 'Resource' not in line:
                current_resource = line.replace('###', '').strip().lower()
                continue

            # Method headers (#### {METHOD} /api/{resource})
            method_match = re.match(r'####\s+(GET|POST|PUT|DELETE|PATCH)\s+(.+)', line)
            if method_match:
                current_method = method_match.group(1)
                path = method_match.group(2).strip()

                # Save previous endpoint
                if current_endpoint:
                    self.endpoints.append(current_endpoint)

                # Parse the endpoint
                current_endpoint = self._parse_endpoint(path, current_method, current_resource, i)
                continue

            # Purpose line
            if current_endpoint and '**Purpose**' in line:
                current_endpoint.summary = line.split(':', 1)[1].strip() if ':' in line else ""

            # Authentication line
            if current_endpoint and '**Authentication**' in line.lower():
                auth_text = line.split(':', 1)[1].strip().lower() if ':' in line else ""
                current_endpoint.auth_required = 'not' not in auth_text and 'optional' not in auth_text

            # Request Body section
            if current_endpoint and '**Request Body**' in line:
                current_endpoint.request_body = self._parse_schema_block(i + 1)

            # Response section
            if current_endpoint and ('**Response**' in line or 'Response:' in line):
                status_match = re.search(r'(\d{3})', line)
                if status_match:
                    status_code = int(status_match.group(1))
                    if 200 <= status_code < 300:
                        current_endpoint.response_success = self._parse_schema_block(i + 1)
                    else:
                        error_schema = self._parse_schema_block(i + 1)
                        error_schema['status_code'] = status_code
                        current_endpoint.response_errors.append(error_schema)

        # Save last endpoint
        if current_endpoint:
            self.endpoints.append(current_endpoint)

    def _parse_endpoint(self, path: str, method: str, resource: str, start_line: int) -> APIEndpoint:
        """Parse a single API endpoint."""
        return APIEndpoint(
            method=method,
            path=path,
            summary="",
            description=""
        )

    def _parse_schema_block(self, start_line: int) -> Dict[str, Any]:
        """Parse a JSON schema block from markdown."""
        schema = {"type": "object", "properties": {}, "required": []}

        for i in range(start_line, min(start_line + 50, len(self.lines))):
            line = self.lines[i].strip()

            # End of code block
            if line.startswith('```') or line.startswith('#'):
                break

            # Parse JSON fields (field: type format)
            field_match = re.match(r'"(\w+)":\s*"(\w+)"', line)
            if field_match:
                field_name = field_match.group(1)
                field_type = field_match.group(2)
                schema["properties"][field_name] = {"type": self._map_type(field_type)}

        return schema

    def _map_type(self, field_type: str) -> str:
        """Map custom type to OpenAPI type."""
        type_map = {
            "string": "string",
            "number": "number",
            "integer": "integer",
            "boolean": "boolean",
            "array": "array",
            "object": "object",
            "email": "string",
            "url": "string",
            "uuid": "string",
            "timestamp": "string",
            "date": "string"
        }
        return type_map.get(field_type.lower(), "string")

    def _generate_paths(self) -> Dict[str, Any]:
        """Generate OpenAPI paths object."""
        paths = {}

        for endpoint in self.endpoints:
            if endpoint.path not in paths:
                paths[endpoint.path] = {}

            path_item = {
                "summary": endpoint.summary,
                "description": endpoint.description,
                "responses": {
                    "200": {"description": "Success"},
                    "400": {"description": "Bad Request"},
                    "401": {"description": "Unauthorized"},
                    "404": {"description": "Not Found"},
                    "500": {"description": "Internal Server Error"}
                }
            }

            # Add security if auth required
            if endpoint.auth_required:
                path_item["security"] = [{"BearerAuth": []}]

            # Add request body for POST/PUT/PATCH
            if endpoint.method in ["POST", "PUT", "PATCH"] and endpoint.request_body:
                path_item["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": endpoint.request_body
                        }
                    }
                }

            # Add success response schema
            if endpoint.response_success:
                path_item["responses"]["200"] = {
                    "description": "Success",
                    "content": {
                        "application/json": {
                            "schema": endpoint.response_success
                        }
                    }
                }

            # Add error responses
            for error in endpoint.response_errors:
                status_code = str(error.get("status_code", 400))
                path_item["responses"][status_code] = {
                    "description": f"Error {status_code}",
                    "content": {
                        "application/json": {
                            "schema": error
                        }
                    }
                }

            paths[endpoint.path][endpoint.method.lower()] = path_item

        return paths

    def _generate_components(self) -> Dict[str, Any]:
        """Generate OpenAPI components object."""
        return {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            },
            "schemas": {
                "Error": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string"},
                        "message": {"type": "string"},
                        "code": {"type": "string"}
                    },
                    "required": ["error", "message"]
                },
                "Pagination": {
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer"},
                        "limit": {"type": "integer"},
                        "total": {"type": "integer"}
                    }
                }
            }
        }

    def write_yaml(self, output_file: Path):
        """Write OpenAPI specification to YAML file."""
        spec = self.parse()

        with open(output_file, 'w') as f:
            yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

        print(f"✓ Generated OpenAPI specification: {output_file}")

        # Print summary
        print(f"  Endpoints: {len(self.endpoints)}")
        for endpoint in self.endpoints:
            print(f"    - {endpoint.method} {endpoint.path}")


class OpenAPIGeneratorFromTemplate:
    """Generate OpenAPI spec from template with simplified parsing."""

    def __init__(self, feature_dir: Path):
        self.feature_dir = feature_dir
        self.feature_id = feature_dir.name
        self.spec_file = feature_dir / "TECHNICAL_SPEC.md"
        self.content = ""

    def generate(self) -> Dict[str, Any]:
        """Generate OpenAPI spec from technical spec."""
        if not self.spec_file.exists():
            print(f"Warning: TECHNICAL_SPEC.md not found, using defaults")
            return self._generate_default_spec()

        with open(self.spec_file, 'r') as f:
            self.content = f.read()

        # Extract API endpoints using regex patterns
        endpoints = self._extract_endpoints()

        return {
            "openapi": "3.0.0",
            "info": self._get_info(),
            "servers": [
                {"url": "http://localhost:3000", "description": "Development"},
                {"url": "https://api.example.com", "description": "Production"}
            ],
            "paths": self._generate_paths_from_endpoints(endpoints),
            "components": self._get_components()
        }

    def _get_info(self) -> Dict[str, Any]:
        """Extract info section."""
        name = self.feature_id.replace('_', ' ').title()

        # Try to extract from spec
        match = re.search(r'# Technical Specification:\s*(.+)', self.content)
        if match:
            name = match.group(1).strip()

        return {
            "title": f"{name} API",
            "version": "1.0.0",
            "description": f"RESTful API for {name}"
        }

    def _extract_endpoints(self) -> List[Dict[str, Any]]:
        """Extract API endpoints from spec."""
        endpoints = []
        lines = self.content.split('\n')
        in_api_section = False

        for i, line in enumerate(lines):
            # Find API section
            if '## API Specification' in line or '# API Specification' in line:
                in_api_section = True
                continue

            if in_api_section and line.startswith('## ') and 'API' not in line:
                break

            if not in_api_section:
                continue

            # Match endpoint headers like #### POST /api/users
            match = re.match(r'#+\s+(GET|POST|PUT|DELETE|PATCH)\s+(/.+)', line)
            if match:
                method = match.group(1)
                path = match.group(2).strip()

                # Look ahead for purpose
                purpose = ""
                for j in range(i + 1, min(i + 5, len(lines))):
                    if 'Purpose:' in lines[j] or '**Purpose**' in lines[j]:
                        purpose = lines[j].split(':', 1)[1].strip().strip('*').strip()
                        break
                    if lines[j].startswith('####') or lines[j].startswith('###'):
                        break

                endpoints.append({
                    "method": method,
                    "path": path,
                    "summary": purpose
                })

        return endpoints

    def _generate_paths_from_endpoints(self, endpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate paths object from extracted endpoints."""
        paths = {}

        for endpoint in endpoints:
            path = endpoint["path"]
            method = endpoint["method"].lower()

            if path not in paths:
                paths[path] = {}

            paths[path][method] = {
                "summary": endpoint.get("summary", ""),
                "responses": {
                    "200": {"description": "Success"},
                    "400": {"description": "Bad Request"},
                    "401": {"description": "Unauthorized"},
                    "500": {"description": "Internal Server Error"}
                }
            }

            # Add request body for POST/PUT/PATCH
            if method in ["post", "put", "patch"]:
                paths[path][method]["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                }

        return paths

    def _get_components(self) -> Dict[str, Any]:
        """Get components section."""
        return {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            },
            "schemas": {
                "Error": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string"},
                        "message": {"type": "string"}
                    },
                    "required": ["error"]
                }
            }
        }

    def _generate_default_spec(self) -> Dict[str, Any]:
        """Generate default empty spec."""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": f"{self.feature_id.replace('_', ' ').title()} API",
                "version": "1.0.0",
                "description": "API specification"
            },
            "paths": {},
            "components": {}
        }

    def write_yaml(self, output_file: Path):
        """Write OpenAPI spec to file."""
        spec = self.generate()

        with open(output_file, 'w') as f:
            yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

        print(f"✓ Generated OpenAPI specification: {output_file}")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 openapi_generator.py <feature_dir>")
        print("Example: python3 openapi_generator.py .sam/001_user_auth")
        sys.exit(1)

    feature_dir = Path(sys.argv[1])

    if not feature_dir.exists():
        print(f"Error: Feature directory not found: {feature_dir}")
        sys.exit(1)

    spec_file = feature_dir / "TECHNICAL_SPEC.md"

    # Generate OpenAPI specification
    print(f"Generating OpenAPI specification from: {spec_file}")

    generator = OpenAPIGeneratorFromTemplate(feature_dir)
    output_file = feature_dir / "openapi.yaml"
    generator.write_yaml(output_file)

    print(f"\n✓ OpenAPI generation complete!")
    print(f"  Output: {output_file}")
    print(f"\nYou can now:")
    print(f"  - View the spec: https://redocly.github.io/redoc/?url={output_file}")
    print(f"  - Generate contract tests: python3 contract_test_generator.py {feature_dir}")


if __name__ == "__main__":
    main()
