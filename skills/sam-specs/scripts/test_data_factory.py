#!/usr/bin/env python3
"""
test_data_factory.py - Generate realistic test data from database schema

This script reads database schema from TECHNICAL_SPEC.md and generates
realistic test data factories using the Faker library. Supports locale-aware
data generation for internationalization testing.

Usage:
    python3 skills/sam-specs/scripts/test_data_factory.py <feature_dir> --generate User --count 50
    python3 skills/sam-specs/scripts/test_data_factory.py .sam/001_user_auth --seed > seed_data.json
    python3 skills/sam-specs/scripts/test_data_factory.py .sam/001_user_auth --edge-cases User

Output:
    Generates test data factories and seed data in .sam/{feature}/tests/fixtures/
"""

import sys
import json
import re
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict

# Try importing faker - if not available, provide instructions
try:
    from faker import Faker
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False

# Import context resolver for locale/currency
try:
    from context_resolver import ContextResolver
    CONTEXT_RESOLVER_AVAILABLE = True
except ImportError:
    CONTEXT_RESOLVER_AVAILABLE = False


@dataclass
class EntityField:
    """Represents a field in a database entity."""
    name: str
    type: str
    constraints: List[str] = field(default_factory=list)
    nullable: bool = True
    default: Any = None
    description: str = ""


@dataclass
class EntitySchema:
    """Represents a database entity/table schema."""
    name: str
    fields: List[EntityField] = field(default_factory=list)
    primary_key: str = "id"
    relationships: Dict[str, str] = field(default_factory=dict)
    indexes: List[str] = field(default_factory=list)


@dataclass
class TestDataConfig:
    """Configuration for test data generation."""
    locale: str = "en_US"
    count: int = 10
    seed: Optional[int] = None
    include_edge_cases: bool = True


class TestDataFactory:
    """Generate realistic test data from database schema."""

    def __init__(self, feature_dir: Path):
        self.feature_dir = feature_dir
        self.spec_file = feature_dir / "TECHNICAL_SPEC.md"
        self.entities: Dict[str, EntitySchema] = {}
        self.config: TestDataConfig = TestDataConfig()
        self.context_resolver: Optional[ContextResolver] = None

        # Set up faker if available
        if FAKER_AVAILABLE:
            self.faker = Faker()
        else:
            self.faker = None

        # Initialize context resolver
        if CONTEXT_RESOLVER_AVAILABLE:
            self.context_resolver = ContextResolver(feature_dir)
            try:
                self.context_resolver.load_context()
                # Get locale from context
                locale = self.context_resolver.get_value("application.locale", "en_US")
                if FAKER_AVAILABLE:
                    self.faker = Faker(locale)
            except Exception as e:
                print(f"  ⚠ Could not load context: {e}")

        # Create fixtures directory
        self.fixtures_dir = feature_dir / "tests" / "fixtures"
        self.fixtures_dir.mkdir(parents=True, exist_ok=True)

    def load_schema(self) -> None:
        """Load database schema from TECHNICAL_SPEC.md."""
        if not self.spec_file.exists():
            raise FileNotFoundError(f"Technical spec not found: {self.spec_file}")

        with open(self.spec_file, 'r') as f:
            content = f.read()

        # Extract database schema section
        schema_match = re.search(
            r'# Database Schema.*?(?=#\s|\Z)',
            content,
            re.DOTALL
        )

        if not schema_match:
            raise ValueError("Database Schema section not found in TECHNICAL_SPEC.md")

        schema_content = schema_match.group(0)

        # Extract CREATE TABLE statements
        table_pattern = r'CREATE TABLE\s+(\w+)\s*\((.*?)\);'
        tables = re.findall(table_pattern, schema_content, re.DOTALL)

        for table_name, table_def in tables:
            entity = self._parse_table_definition(table_name, table_def)
            self.entities[entity.name] = entity

        print(f"  Loaded {len(self.entities)} entity schemas")

    def _parse_table_definition(self, table_name: str, table_def: str) -> EntitySchema:
        """Parse a CREATE TABLE definition."""
        fields = []
        primary_key = "id"

        # Split by comma, but handle nested parentheses
        field_defs = self._split_field_definitions(table_def)

        for field_def in field_defs:
            field_def = field_def.strip()
            if not field_def:
                continue

            # Check for constraints
            if field_def.upper().startswith("PRIMARY KEY"):
                # Extract primary key name
                pk_match = re.search(r'PRIMARY KEY\s*\((\w+)', field_def, re.IGNORECASE)
                if pk_match:
                    primary_key = pk_match.group(1)
                continue

            if field_def.upper().startswith("FOREIGN KEY"):
                # Extract relationship
                fk_match = re.search(r'FOREIGN KEY\s*\((\w+)\)\s*REFERENCES\s+(\w+)', field_def, re.IGNORECASE)
                if fk_match:
                    field_name, ref_table = fk_match.groups()
                    if table_name not in self.entities:
                        self.entities[table_name] = EntitySchema(name=table_name)
                    self.entities[table_name].relationships[field_name] = ref_table
                continue

            # Parse field definition
            field = self._parse_field_definition(field_def)
            if field:
                fields.append(field)

        return EntitySchema(
            name=table_name,
            fields=fields,
            primary_key=primary_key
        )

    def _split_field_definitions(self, table_def: str) -> List[str]:
        """Split field definitions by comma, respecting nested parentheses."""
        fields = []
        current = ""
        depth = 0

        for char in table_def:
            if char == '(':
                depth += 1
                current += char
            elif char == ')':
                depth -= 1
                current += char
            elif char == ',' and depth == 0:
                fields.append(current.strip())
                current = ""
            else:
                current += char

        if current.strip():
            fields.append(current.strip())

        return fields

    def _parse_field_definition(self, field_def: str) -> Optional[EntityField]:
        """Parse a single field definition."""
        # Match: field_name TYPE [NOT NULL] [DEFAULT value] [COMMENT]
        match = re.match(
            r'(\w+)\s+([A-Za-z]+(?:\(\d+\))?(?:\s+\w+)*)\s*(.*)',
            field_def.strip()
        )

        if not match:
            return None

        name = match.group(1)
        type_info = match.group(2)
        constraints_str = match.group(3) if match.group(3) else ""

        # Parse constraints
        constraints = []
        nullable = True
        default = None

        if "NOT NULL" in constraints_str.upper():
            nullable = False
            constraints.append("NOT NULL")

        if "UNIQUE" in constraints_str.upper():
            constraints.append("UNIQUE")

        # Extract default value
        default_match = re.search(r'DEFAULT\s+([^\s,]+)', constraints_str, re.IGNORECASE)
        if default_match:
            default = default_match.group(1).strip("'\"")

        return EntityField(
            name=name,
            type=type_info.upper(),
            constraints=constraints,
            nullable=nullable,
            default=default
        )

    def generate_factory(self, entity_name: str) -> str:
        """Generate a test data factory function for an entity."""
        entity_name = entity_name.lower()
        entity = self.entities.get(entity_name)

        if not entity:
            raise ValueError(f"Entity '{entity_name}' not found in schema")

        # Generate TypeScript factory
        factory_code = self._generate_typescript_factory(entity)

        # Write to file
        factory_file = self.fixtures_dir / f"{entity_name}.factory.ts"
        with open(factory_file, 'w') as f:
            f.write(factory_code)

        print(f"  ✓ Generated factory: {factory_file}")
        return str(factory_file)

    def _generate_typescript_factory(self, entity: EntitySchema) -> str:
        """Generate a TypeScript factory function."""
        entity_camel = ''.join(word.capitalize() for word in entity.name.split('_'))

        # Generate type definition
        type_def = f"export interface {entity_camel} {{\n"
        for field in entity.fields:
            ts_type = self._map_sql_to_typescript(field.type)
            optional = "?" if field.nullable else ""
            type_def += f"  {field.name}{optional}: {ts_type};\n"
        type_def += "}\n\n"

        # Generate factory function
        factory_code = type_def
        factory_code += f'/**\n * Factory function for {entity.name} entity\n'
        factory_code += f" * Auto-generated from database schema\n"
        factory_code += f" * Generated: {datetime.now().isoformat()}\n"
        factory_code += f" */\n\n"

        factory_code += f"import {{ faker }} from '@faker-js/faker';\n\n"

        factory_code += f"export const create{entity_camel} = "
        factory_code += f"(overrides: Partial<{entity_camel}> = {{}}): {entity_camel} => ({{\n"

        for field in entity.fields:
            if field.name == entity.primary_key:
                factory_code += f"  {field.name}: overrides.{field.name} ?? faker.uuid(),\n"
            else:
                fake_value = self._get_fake_value_for_field(field)
                if fake_value:
                    factory_code += f"  {field.name}: overrides.{field.name} ?? {fake_value},\n"
                elif field.nullable:
                    factory_code += f"  {field.name}: overrides.{field.name} ?? null,\n"

        factory_code += "  ...overrides\n"
        factory_code += "});\n\n"

        # Generate helper function for arrays
        factory_code += f"/**\n * Generate an array of {entity.name} entities\n */\n"
        factory_code += f"export const create{entity_camel}List = ("
        factory_code += f"count: number, overrides?: Partial<{entity_camel}>): {entity_camel}[] => {{\n"
        factory_code += f"  return Array.from({{ length: count }}, () => create{entity_camel}(overrides));\n"
        factory_code += "};\n"

        return factory_code

    def _map_sql_to_typescript(self, sql_type: str) -> str:
        """Map SQL type to TypeScript type."""
        type_map = {
            "UUID": "string",
            "VARCHAR": "string",
            "TEXT": "string",
            "INTEGER": "number",
            "BIGINT": "number",
            "SMALLINT": "number",
            "BOOLEAN": "boolean",
            "TIMESTAMP": "Date",
            "TIMESTAMPTZ": "Date",
            "DATE": "Date",
            "JSON": "Record<string, any>",
            "JSONB": "Record<string, any>",
            "DECIMAL": "number",
            "FLOAT": "number",
            "DOUBLE": "number"
        }

        # Extract base type (remove size constraints)
        base_type = sql_type.upper().split('(')[0]

        return type_map.get(base_type, "any")

    def _get_fake_value_for_field(self, field: EntityField) -> Optional[str]:
        """Generate a faker expression for a field."""
        if not FAKER_AVAILABLE:
            return None

        field_name = field.name.lower()
        field_type = field.type.upper()

        # Field name-based generation
        if "email" in field_name:
            return "faker.internet.email()"
        elif "name" in field_name and "first" not in field_name and "last" not in field_name:
            return "faker.person.fullName()"
        elif "first_name" in field_name or "firstname" in field_name:
            return "faker.person.firstName()"
        elif "last_name" in field_name or "lastname" in field_name:
            return "faker.person.lastName()"
        elif "username" in field_name:
            return "faker.internet.userName()"
        elif "password" in field_name:
            return "faker.internet.password({ length: 16 })"
        elif "phone" in field_name:
            return "faker.phone.number()"
        elif "address" in field_name:
            return "faker.location.streetAddress()"
        elif "city" in field_name:
            return "faker.location.city()"
        elif "country" in field_name:
            return "faker.location.countryCode('alpha-2')"
        elif "zip" in field_name or "postal" in field_name:
            return "faker.location.zipCode()"
        elif "url" in field_name or "website" in field_name:
            return "faker.internet.url()"
        elif "company" in field_name:
            return "faker.company.name()"

        # Type-based generation
        if field_type in ["INTEGER", "BIGINT", "SMALLINT", "DECIMAL", "FLOAT", "DOUBLE"]:
            return "faker.number.int({ min: 1, max: 1000 })"
        elif field_type == "BOOLEAN":
            return "faker.datatype.boolean()"
        elif field_type in ["TIMESTAMP", "TIMESTAMPTZ", "DATE"]:
            return "faker.date.recent({ refDate: '2024-01-01T00:00:00Z' })"
        elif field_type == "UUID":
            return "faker.string.uuid()"

        # Default: generate a random string
        if field_type in ["VARCHAR", "TEXT"]:
            size = 50
            size_match = re.search(r'VARCHAR\((\d+)\)', field_type)
            if size_match:
                size = int(size_match.group(1))
            return f"faker.lorem.slug() // TODO: Verify field size ({size})"

        return None

    def generate_seed_data(self, count: int = 10) -> Dict:
        """Generate seed data for all entities."""
        if not FAKER_AVAILABLE:
            print("  ⚠ Faker not available. Install with: pip install faker")
            return {}

        seed_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "locale": self.config.locale,
                "count": count
            },
            "entities": {}
        }

        for entity_name, entity in self.entities.items():
            entity_data = []

            for _ in range(count):
                record = {}
                for field in entity.fields:
                    if field.name == entity.primary_key:
                        record[field.name] = self.faker.uuid()
                    else:
                        record[field.name] = self._generate_field_value(field)

                entity_data.append(record)

            seed_data["entities"][entity_name] = entity_data

        return seed_data

    def _generate_field_value(self, field: EntityField) -> Any:
        """Generate a fake value for a field using Faker."""
        if not self.faker:
            return f"<{field.type}>"

        field_name = field.name.lower()
        field_type = field.type.upper()

        # Field name-based generation
        if "email" in field_name:
            return self.faker.email()
        elif "name" in field_name and "first" not in field_name and "last" not in field_name:
            return self.faker.name()
        elif "first_name" in field_name or "firstname" in field_name:
            return self.faker.first_name()
        elif "last_name" in field_name or "lastname" in field_name:
            return self.faker.last_name()
        elif "username" in field_name:
            return self.faker.user_name()
        elif "password" in field_name:
            return self.faker.password(length=16)
        elif "phone" in field_name:
            return self.faker.phone_number()
        elif "address" in field_name:
            return self.faker.address().replace('\n', ', ')
        elif "city" in field_name:
            return self.faker.city()
        elif "country" in field_name:
            return self.faker.country_code()
        elif "zip" in field_name or "postal" in field_name:
            return self.faker.postcode()
        elif "url" in field_name or "website" in field_name:
            return self.faker.url()
        elif "company" in field_name:
            return self.faker.company()

        # Type-based generation
        if field_type in ["INTEGER", "BIGINT", "SMALLINT", "DECIMAL", "FLOAT", "DOUBLE"]:
            return self.faker.random_int(min=1, max=1000)
        elif field_type == "BOOLEAN":
            return self.faker.boolean()
        elif field_type in ["TIMESTAMP", "TIMESTAMPTZ", "DATE"]:
            return self.faker.date_time_this_year().isoformat()
        elif field_type == "UUID":
            return self.faker.uuid()

        # Default: random string
        if field_type in ["VARCHAR", "TEXT"]:
            return self.faker.word()

        return None

    def generate_edge_cases(self, entity_name: str) -> Dict:
        """Generate edge case test data for an entity."""
        entity_name = entity_name.lower()
        entity = self.entities.get(entity_name)

        if not entity:
            raise ValueError(f"Entity '{entity_name}' not found")

        edge_cases = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "entity": entity_name,
                "description": "Edge case test data"
            },
            "cases": []
        }

        # Maximum values
        max_case = {}
        for field in entity.fields:
            if field.name != entity.primary_key:
                max_case[field.name] = self._generate_max_value(field)
        edge_cases["cases"].append({"name": "Maximum Values", "data": max_case})

        # Minimum values
        min_case = {}
        for field in entity.fields:
            if field.name != entity.primary_key:
                min_case[field.name] = self._generate_min_value(field)
        edge_cases["cases"].append({"name": "Minimum Values", "data": min_case})

        # Null values (for nullable fields)
        null_case = {}
        for field in entity.fields:
            if field.name != entity.primary_key and field.nullable:
                null_case[field.name] = None
        edge_cases["cases"].append({"name": "Null Values", "data": null_case})

        # Empty strings
        empty_case = {}
        for field in entity.fields:
            if field.name != entity.primary_key and "TEXT" in field.type or "VARCHAR" in field.type:
                empty_case[field.name] = ""
        edge_cases["cases"].append({"name": "Empty Strings", "data": empty_case})

        return edge_cases

    def _generate_max_value(self, field: EntityField) -> Any:
        """Generate maximum value for a field."""
        field_type = field.type.upper()

        if "VARCHAR" in field_type:
            size = 255
            size_match = re.search(r'VARCHAR\((\d+)\)', field_type)
            if size_match:
                size = int(size_match.group(1))
            return "x" * size
        elif field_type in ["INTEGER", "BIGINT", "SMALLINT"]:
            return 2147483647  # Max 32-bit int
        elif field_type == "BOOLEAN":
            return True
        elif field_type in ["DECIMAL", "FLOAT", "DOUBLE"]:
            return 999999.99
        else:
            return "MAX_VALUE"

    def _generate_min_value(self, field: EntityField) -> Any:
        """Generate minimum value for a field."""
        field_type = field.type.upper()

        if field_type in ["INTEGER", "BIGINT", "SMALLINT"]:
            return -2147483648  # Min 32-bit int
        elif field_type == "BOOLEAN":
            return False
        elif field_type in ["DECIMAL", "FLOAT", "DOUBLE"]:
            return -999999.99
        else:
            return "MIN_VALUE"

    def _apply_locale_formatting(self, data: Dict) -> Dict:
        """Apply locale-aware formatting to generated data."""
        if not self.context_resolver:
            return data

        # Get locale from context
        locale = self.context_resolver.get_value("application.locale", "en_US")
        currency = self.context_resolver.get_value("application.currency", "USD")

        # Apply formatting to appropriate fields
        for entity_name, entity in self.entities.items():
            for field in entity.fields:
                field_name = field.name.lower()
                if "price" in field_name or "amount" in field_name or "cost" in field_name:
                    # Format as currency
                    # This would be applied in the generated factory code
                    pass

        return data


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 test_data_factory.py <feature_dir> [--generate ENTITY] [--count N] [--seed] [--edge-cases ENTITY]")
        print("Example: python3 test_data_factory.py .sam/001_user_auth --generate User --count 50")
        print("Example: python3 test_data_factory.py .sam/001_user_auth --seed > seed_data.json")
        print("Example: python3 test_data_factory.py .sam/001_user_auth --edge-cases User")
        sys.exit(1)

    feature_dir = Path(sys.argv[1])
    generate_entity = None
    count = 10
    output_seed = False
    edge_cases_entity = None

    # Parse arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--generate" and i + 1 < len(sys.argv):
            generate_entity = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--count" and i + 1 < len(sys.argv):
            count = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--seed":
            output_seed = True
            i += 1
        elif sys.argv[i] == "--edge-cases" and i + 1 < len(sys.argv):
            edge_cases_entity = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    if not feature_dir.exists():
        print(f"Error: Feature directory not found: {feature_dir}")
        sys.exit(1)

    # Create factory
    factory = TestDataFactory(feature_dir)

    # Load schema
    print(f"Loading schema from: {factory.spec_file}")
    factory.load_schema()

    # Execute requested operation
    if generate_entity:
        print(f"Generating factory for: {generate_entity}")
        factory.generate_factory(generate_entity)

    elif output_seed:
        print(f"Generating {count} seed records...")
        seed_data = factory.generate_seed_data(count)
        print(json.dumps(seed_data, indent=2, default=str))

    elif edge_cases_entity:
        print(f"Generating edge cases for: {edge_cases_entity}")
        edge_cases = factory.generate_edge_cases(edge_cases_entity)
        print(json.dumps(edge_cases, indent=2, default=str))

    else:
        # Default: generate factories for all entities
        print("Generating factories for all entities...")
        for entity_name in factory.entities.keys():
            factory.generate_factory(entity_name)

    print(f"\n✓ Test data generation complete!")
    print(f"  Output directory: {factory.fixtures_dir}")


if __name__ == "__main__":
    main()
