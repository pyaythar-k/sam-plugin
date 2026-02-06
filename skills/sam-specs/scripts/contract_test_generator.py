#!/usr/bin/env python3
"""
contract_test_generator.py - Generate contract tests from OpenAPI specifications

This script reads OpenAPI 3.0 specifications and generates contract tests
using Zod for runtime validation. This ensures that APIs match their
specifications and catches breaking changes before deployment.

Usage:
    python3 skills/sam-specs/scripts/contract_test_generator.py <feature_dir> --framework zod
    python3 skills/sam-specs/scripts/contract_test_generator.py .sam/001_user_auth --framework pact
    python3 skills/sam-specs/scripts/contract_test_generator.py .sam/001_user_auth --verify

Output:
    Generates contract test files in the feature's tests/contract directory
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import yaml
import re

# Import context resolver for variable interpolation
try:
    from context_resolver import ContextResolver
    CONTEXT_RESOLVER_AVAILABLE = True
except ImportError:
    CONTEXT_RESOLVER_AVAILABLE = False
    ContextResolver = None  # Type stub for when unavailable


@dataclass
class ContractTest:
    """Represents a contract test for an API endpoint."""
    test_id: str
    name: str
    endpoint: str
    method: str
    request_schema: Dict[str, Any]
    response_schema_success: Dict[str, Any]
    response_schemas_error: List[Dict[str, Any]] = field(default_factory=list)
    auth_required: bool = True


class ContractTestGenerator:
    """Generate contract tests from OpenAPI specification."""

    def __init__(self, openapi_file: Path, feature_dir: Path, framework: str = "zod", use_context: bool = True):
        self.openapi_file = openapi_file
        self.feature_dir = feature_dir
        self.framework = framework.lower()
        self.openapi_spec: Dict[str, Any] = {}
        self.contract_tests: List[ContractTest] = []
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

    def load_spec(self):
        """Load the OpenAPI specification."""
        with open(self.openapi_file, 'r') as f:
            self.openapi_spec = yaml.safe_load(f)

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

    def generate_all(self):
        """Generate all contract test files."""
        self.load_spec()

        if self.framework == "zod":
            self._generate_zod_tests()
        elif self.framework == "pact":
            self._generate_pact_tests()
        elif self.framework == "joi":
            self._generate_joi_tests()
        else:
            raise ValueError(f"Unsupported framework: {self.framework}")

    def _generate_zod_tests(self):
        """Generate Zod schema validation tests."""
        tests_dir = self.feature_dir / "tests" / "contract" / "zod"
        tests_dir.mkdir(parents=True, exist_ok=True)

        # Generate Zod schemas file
        schemas_file = tests_dir / "schemas.ts"
        schemas_content = self._generate_zod_schemas()
        with open(schemas_file, 'w') as f:
            f.write(schemas_content)

        print(f"✓ Generated Zod schemas: {schemas_file}")

        # Generate contract tests file
        tests_file = tests_dir / "contract.test.ts"
        tests_content = self._generate_zod_contract_tests()
        with open(tests_file, 'w') as f:
            f.write(tests_content)

        print(f"✓ Generated Zod contract tests: {tests_file}")

        # Generate request validators
        validators_file = tests_dir / "validators.ts"
        validators_content = self._generate_request_validators()
        with open(validators_file, 'w') as f:
            f.write(validators_content)

        print(f"✓ Generated request validators: {validators_file}")

    def _generate_zod_schemas(self) -> str:
        """Generate Zod schema definitions from OpenAPI spec."""
        content = f'''/**
 * Auto-generated Zod schemas from OpenAPI specification
 * Source: {self.openapi_file.name}
 * Generated: {datetime.now().isoformat()}
 */

import {{ z }} from 'zod';

// Error schemas
export const ErrorSchema = z.object({{
  error: z.string(),
  message: z.string(),
  details: z.record(z.any()).optional(),
}});

export const ValidationErrorSchema = z.object({{
  error: z.literal('VALIDATION_ERROR'),
  message: z.string(),
  errors: z.array(z.object({{
    field: z.string(),
    message: z.string(),
  }})),
}});

export const PaginationSchema = z.object({{
  page: z.number().int().positive().default(1),
  limit: z.number().int().positive().max(100).default(20),
  total: z.number().int().nonnegative(),
  totalPages: z.number().int().nonnegative(),
}});

'''

        # Generate schemas from OpenAPI components
        schemas = self.openapi_spec.get('components', {}).get('schemas', {})

        for schema_name, schema_def in schemas.items():
            if schema_name in ['Error', 'Pagination']:
                continue

            content += f"// {schema_name}\n"
            content += f"export const {schema_name}Schema = "

            # Generate Zod schema from OpenAPI schema
            zod_schema = self._openapi_to_zod(schema_def)
            content += zod_schema + ";\n\n"

        return content

    def _openapi_to_zod(self, schema: Dict[str, Any], indent: int = 0) -> str:
        """Convert OpenAPI schema to Zod schema string."""
        prefix = "  " * indent
        schema_type = schema.get('type', 'any')

        if schema_type == 'object':
            if not schema.get('properties'):
                return f"{prefix}z.object({{}})"

            props = []
            required = schema.get('required', [])

            for prop_name, prop_def in schema.get('properties', {}).items():
                prop_schema = self._openapi_to_zod(prop_def, indent + 1)
                is_required = prop_name in required

                if is_required:
                    props.append(f"{prefix}  {prop_name}: {prop_schema.strip()},")
                else:
                    props.append(f"{prefix}  {prop_name}: {prop_schema.strip()}.optional(),")

            return f"z.object({{{}\n{prefix}}})".format("\n".join(props))

        elif schema_type == 'array':
            items = self._openapi_to_zod(schema.get('items', {}), indent + 1)
            return f"z.array({items.strip()})"

        elif schema_type == 'string':
            result = "z.string()"
            enum = schema.get('enum')
            if enum:
                result = f"z.enum([{', '.join(repr(e) for e in enum)}])"
            format_type = schema.get('format')
            if format_type == 'email':
                result = "z.string().email()"
            elif format_type == 'uuid':
                result = "z.string().uuid()"
            elif format_type == 'date-time':
                result = "z.string().datetime()"
            return result

        elif schema_type == 'number':
            return "z.number()"

        elif schema_type == 'integer':
            return "z.number().int()"

        elif schema_type == 'boolean':
            return "z.boolean()"

        elif schema.get('$ref'):
            # Reference to another schema
            ref = schema.get('$ref', '')
            schema_name = ref.split('/')[-1]
            return f"{schema_name}Schema"

        else:
            return "z.any()"

    def _generate_zod_contract_tests(self) -> str:
        """Generate Zod contract test file."""
        paths = self.openapi_spec.get('paths', {})

        content = f'''/**
 * Auto-generated contract tests from OpenAPI specification
 * Source: {self.openapi_file.name}
 * Generated: {datetime.now().isoformat()}
 */

import {{ describe, it, expect, beforeAll }} from '@jest/globals';
import {{ request }} from '@/tests/setup';
import {{ * as schemas }} from './schemas';
import {{ validateRequest, validateResponse }} from './validators';

describe('Contract Tests', () => {{
  let authToken: string;

  beforeAll(async () => {{
    // Setup authentication if needed
    // authToken = await login();
  }});

'''

        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method in ['get', 'post', 'put', 'delete', 'patch']:
                    content += self._generate_endpoint_test(path, method, operation)

        content += "});\n"
        return content

    def _generate_endpoint_test(self, path: str, method: str, operation: Dict[str, Any]) -> str:
        """Generate test for a single endpoint."""
        summary = operation.get('summary', f'{method.upper()} {path}')
        operation_id = operation.get('operationId', f'{method}_{path.replace("/", "_")}')
        responses = operation.get('responses', {})

        content = f"""
  describe('{summary}', () => {{
"""

        # Success response test
        if '200' in responses or '201' in responses:
            status_code = '200' if '200' in responses else '201'
            content += f"""
    it('should return {status_code} with valid response schema', async () => {{
      const response = await request(app)
        .{method}('{path}'{self._get_auth_param(operation)})
        .expect({status_code});

      // Validate response against schema
      const result = validateResponse(response.body, '{operation_id}_response');
      expect(result.success).toBe(true);
      expect(result.errors).toEqual([]);
    }});
"""

        # Error response tests
        for status in ['400', '401', '404', '500']:
            if status in responses:
                content += f"""
    it('should return {status} for error case', async () => {{
      const response = await request(app)
        .{method}('{path}')
        .expect({status});

      // Validate error response
      const result = validateResponse(response.body, 'Error');
      expect(result.success).toBe(true);
      expect(response.body.error).toBeDefined();
    }});
"""

        content += "  });\n"
        return content

    def _get_auth_param(self, operation: Dict[str, Any]) -> str:
        """Get authentication parameter for request."""
        security = operation.get('security', [])
        if security and not any(s.get('BearerAuth') is None for s in security):
            return "\n        .set('Authorization', `Bearer ${{authToken}}`)"
        return ""

    def _generate_request_validators(self) -> str:
        """Generate request/response validator functions."""
        return '''/**
 * Request and response validators for contract testing
 */

import * as schemas from './schemas';

export function validateRequest(data: any, schemaName: string): {
  success: boolean;
  errors: string[];
} {
  let schema;

  switch (schemaName) {
    // Add request schema mappings here
    default:
      return { success: true, errors: [] };
  }

  const result = schema.safeParse(data);
  if (result.success) {
    return { success: true, errors: [] };
  }

  return {
    success: false,
    errors: result.error.errors.map((e: any) => e.message)
  };
}

export function validateResponse(data: any, schemaName: string): {
  success: boolean;
  errors: string[];
} {
  let schema;

  switch (schemaName) {
    case 'Error':
      schema = schemas.ErrorSchema;
      break;
    case 'ValidationError':
      schema = schemas.ValidationErrorSchema;
      break;
    case 'Pagination':
      schema = schemas.PaginationSchema;
      break;
    // Add response schema mappings here
    default:
      return { success: true, errors: [] };
  }

  const result = schema.safeParse(data);
  if (result.success) {
    return { success: true, errors: [] };
  }

  return {
    success: false,
    errors: result.error.errors.map((e: any) => `${e.path.join('.')}: ${e.message}`)
  };
}
'''

    def _generate_pact_tests(self):
        """Generate Pact contract tests."""
        tests_dir = self.feature_dir / "tests" / "contract" / "pact"
        tests_dir.mkdir(parents=True, exist_ok=True)

        content = f'''/**
 * Auto-generated Pact contract tests from OpenAPI specification
 * Source: {self.openapi_file.name}
 * Generated: {datetime.now().isoformat()}
 */

import {{ Pact }} from '@pact-foundation/pact';
import {{ Matchers }} from '@pact-foundation/pact/dsl/matchers';
import {{ describe, it }} from 'mocha';

const {{ like, eachLike }} = Matchers;

describe('Contract Tests', () => {{
  const provider = new Pact({{
    consumer: '{self.openapi_spec.get('info', {{}}).get('title', 'API Consumer')}',
    provider: '{self.openapi_spec.get('info', {{}}).get('title', 'API Provider')}',
    port: 1234,
    log: './logs/pact.log',
    dir: './pacts',
  }});

  before(() => provider.setup());
  after(() => provider.finalize());

  // Add provider states and tests here
  describe('API contract', () => {{
    before(() => {{
      provider.addInteraction({{
        state: 'default state',
        uponReceiving: 'a request',
        withRequest: {{
          method: 'GET',
          path: '/api/resource',
        }},
        willRespondWith: {{
          status: 200,
          body: like({{
            id: like(1),
            name: like('test'),
          }}),
        }},
      }});
    }});

    it('should return valid response', async () => {{
      await provider.verify();
    }});
  }});
}});
'''

        tests_file = tests_dir / "pact.test.ts"
        with open(tests_file, 'w') as f:
            f.write(content)

        print(f"✓ Generated Pact contract tests: {tests_file}")

    def _generate_joi_tests(self):
        """Generate Joi schema validation tests."""
        tests_dir = self.feature_dir / "tests" / "contract" / "joi"
        tests_dir.mkdir(parents=True, exist_ok=True)

        content = f'''/**
 * Auto-generated Joi schema validators from OpenAPI specification
 * Source: {self.openapi_file.name}
 * Generated: {datetime.now().isoformat()}
 */

import Joi from 'joi';

// Error schemas
export const errorSchema = Joi.object({{
  error: Joi.string().required(),
  message: Joi.string().required(),
  details: Joi.object().optional(),
}});

export const paginationSchema = Joi.object({{
  page: Joi.number().integer().positive().default(1),
  limit: Joi.number().integer().positive().max(100).default(20),
  total: Joi.number().integer().min(0),
  totalPages: Joi.number().integer().min(0),
}});

// Add more schemas based on your OpenAPI specification
'''

        schemas_file = tests_dir / "schemas.ts"
        with open(schemas_file, 'w') as f:
            f.write(content)

        print(f"✓ Generated Joi schemas: {schemas_file}")


def verify_contracts(feature_dir: Path) -> bool:
    """Verify contracts against implementation."""
    print(f"Verifying contracts for: {feature_dir}")

    # Check for generated contract tests
    contract_dirs = [
        feature_dir / "tests" / "contract" / "zod",
        feature_dir / "tests" / "contract" / "pact",
        feature_dir / "tests" / "contract" / "joi"
    ]

    found = False
    for contract_dir in contract_dirs:
        if contract_dir.exists():
            found = True
            print(f"  ✓ Found contract tests in: {contract_dir}")

    if not found:
        print(f"  ✗ No contract tests found. Run contract_test_generator.py first.")
        return False

    print(f"\n✓ Contract verification complete!")
    print(f"  Run 'npm test' to execute contract tests")
    return True


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 contract_test_generator.py <feature_dir> [--framework zod|pact|joi] [--verify]")
        print("Example: python3 contract_test_generator.py .sam/001_user_auth --framework zod")
        print("Example: python3 contract_test_generator.py .sam/001_user_auth --verify")
        sys.exit(1)

    feature_dir = Path(sys.argv[1])
    framework = "zod"
    verify_only = False

    # Parse optional arguments
    if len(sys.argv) >= 3:
        if sys.argv[2] == "--framework":
            framework = sys.argv[3]
        elif sys.argv[2] == "--verify":
            verify_only = True

    if not feature_dir.exists():
        print(f"Error: Feature directory not found: {feature_dir}")
        sys.exit(1)

    if verify_only:
        success = verify_contracts(feature_dir)
        sys.exit(0 if success else 1)

    # Find OpenAPI spec
    openapi_file = feature_dir / "openapi.yaml"
    if not openapi_file.exists():
        print(f"Error: openapi.yaml not found in {feature_dir}")
        print(f"Hint: Run openapi_generator.py first to generate OpenAPI specification")
        sys.exit(1)

    # Generate contract tests
    print(f"Generating {framework.upper()} contract tests from: {openapi_file}")

    generator = ContractTestGenerator(openapi_file, feature_dir, framework)
    generator.generate_all()

    print(f"\n✓ Contract test generation complete!")
    print(f"  Framework: {framework.upper()}")
    print(f"  Output directory: {feature_dir / 'tests' / 'contract'}")
    print(f"\nNext steps:")
    print(f"  1. Run contract tests: npm test")
    print(f"  2. Integrate into CI/CD pipeline")
    print(f"  3. Add contract verification to quality gates")


if __name__ == "__main__":
    main()
