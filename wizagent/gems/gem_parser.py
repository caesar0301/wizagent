"""
Gem Parser - Parse Pydantic models from YAML declarations.

This module provides functionality to dynamically create Pydantic models from YAML
configuration files. It supports cross-references between models and handles complex
type relationships using a two-pass parsing approach.
"""

import re
import yaml
from typing import Any, Dict, List, Optional, Union, get_args, get_origin
from datetime import datetime
from pydantic import BaseModel, Field, create_model
from pathlib import Path


class GemParserError(Exception):
    """Base exception for gem parser errors."""
    pass


class TypeMappingError(GemParserError):
    """Raised when a type cannot be mapped to a Python type."""
    pass


class CircularReferenceError(GemParserError):
    """Raised when circular references are detected between models."""
    pass


class GemParser:
    """Parser for converting YAML model declarations to Pydantic models."""
    
    def __init__(self):
        """Initialize the gem parser with default type mappings."""
        self.dynamic_models: Dict[str, type] = {}
        self.type_map = {
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'Any': Any,
            'datetime': datetime,
            'timestamp': int,  # Common representation for timestamps
        }
        self._dependency_graph: Dict[str, set] = {}
    
    def add_type_mapping(self, type_name: str, python_type: type) -> None:
        """Add a custom type mapping.
        
        Args:
            type_name: The string representation of the type in YAML
            python_type: The corresponding Python type
        """
        self.type_map[type_name] = python_type
    
    def parse_from_yaml_string(self, yaml_content: str) -> Dict[str, type]:
        """Parse YAML string and return dynamically created Pydantic models.
        
        Args:
            yaml_content: YAML string containing model definitions
            
        Returns:
            Dictionary mapping model names to Pydantic model classes
            
        Raises:
            GemParserError: If parsing fails
            TypeMappingError: If a type cannot be mapped
            CircularReferenceError: If circular references are detected
        """
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise GemParserError(f"Failed to parse YAML: {e}")
        
        return self._parse_models(data)
    
    def parse_from_file(self, file_path: Union[str, Path]) -> Dict[str, type]:
        """Parse YAML file and return dynamically created Pydantic models.
        
        Args:
            file_path: Path to YAML file containing model definitions
            
        Returns:
            Dictionary mapping model names to Pydantic model classes
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml_content = f.read()
        except (IOError, OSError) as e:
            raise GemParserError(f"Failed to read file {file_path}: {e}")
        
        return self.parse_from_yaml_string(yaml_content)
    
    def _parse_models(self, data: Dict[str, Any]) -> Dict[str, type]:
        """Parse model definitions from loaded YAML data.
        
        Args:
            data: Parsed YAML data
            
        Returns:
            Dictionary mapping model names to Pydantic model classes
        """
        if 'output_models' not in data:
            raise GemParserError("YAML must contain 'output_models' key")
        
        output_models = data['output_models']
        if not isinstance(output_models, list):
            raise GemParserError("'output_models' must be a list")
        
        # Reset state for new parsing
        self.dynamic_models.clear()
        self._dependency_graph.clear()
        self._current_output_models = output_models  # Store for type parsing
        
        # Build dependency graph and detect circular references
        self._build_dependency_graph(output_models)
        self._detect_circular_references()
        
        # Pass 1: Create placeholder classes to resolve references
        for model_def in output_models:
            model_name = model_def['name']
            # Create a simple, empty Pydantic model class
            self.dynamic_models[model_name] = type(model_name, (BaseModel,), {})
        
        # Pass 2: Recreate models with proper fields
        for model_def in output_models:
            self._create_model_with_fields(model_def)
        
        # Pass 3: Update forward references for all models
        # We need to rebuild models in dependency order to resolve forward references
        for model_class in self.dynamic_models.values():
            try:
                # Update the global namespace with all our models for forward reference resolution
                model_class.model_rebuild(global_ns=self.dynamic_models)
            except Exception:
                # Some models might not need forward ref updates
                pass
        
        return self.dynamic_models.copy()
    
    def _build_dependency_graph(self, output_models: List[Dict[str, Any]]) -> None:
        """Build a dependency graph to detect circular references.
        
        Args:
            output_models: List of model definitions
        """
        for model_def in output_models:
            model_name = model_def['name']
            dependencies = set()
            
            if 'fields' in model_def:
                for field_def in model_def['fields']:
                    field_type_str = field_def['type']
                    deps = self._extract_type_dependencies(field_type_str)
                    dependencies.update(deps)
            
            self._dependency_graph[model_name] = dependencies
    
    def _extract_type_dependencies(self, type_str: str) -> set:
        """Extract model dependencies from a type string.
        
        Args:
            type_str: Type string like 'List[Metric]' or 'Optional[Stock]'
            
        Returns:
            Set of model names that this type depends on
        """
        dependencies = set()
        
        # Find all custom type references in brackets
        bracket_pattern = r'\[([^\[\]]+)\]'
        matches = re.findall(bracket_pattern, type_str)
        
        for match in matches:
            # Handle nested types like 'List[Metric]' or 'Dict[str, Stock]'
            parts = [part.strip() for part in match.split(',')]
            for part in parts:
                if part not in self.type_map and part not in ['str', 'int', 'float', 'bool']:
                    dependencies.add(part)
        
        # Also check if the type itself is a custom model (not wrapped in brackets)
        if (type_str not in self.type_map and 
            not any(wrapper in type_str for wrapper in ['List[', 'Dict[', 'Optional[', 'Union[']) and
            type_str not in ['str', 'int', 'float', 'bool', 'Any']):
            dependencies.add(type_str)
        
        return dependencies
    
    def _detect_circular_references(self) -> None:
        """Detect circular references in the dependency graph.
        
        Raises:
            CircularReferenceError: If circular references are detected
        """
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self._dependency_graph.get(node, set()):
                if neighbor in self._dependency_graph:  # Only check neighbors that are actual models
                    if neighbor not in visited:
                        if has_cycle(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True
            
            rec_stack.remove(node)
            return False
        
        for node in self._dependency_graph:
            if node not in visited:
                if has_cycle(node):
                    raise CircularReferenceError(f"Circular reference detected involving model '{node}'")
    
    def _create_model_with_fields(self, model_def: Dict[str, Any]) -> None:
        """Create a model with proper fields using Pydantic's create_model.
        
        Args:
            model_def: Model definition dictionary
        """
        model_name = model_def['name']
        
        if 'fields' not in model_def:
            # Model with no fields - just use the placeholder
            return
        
        field_definitions = {}
        
        for field_def in model_def['fields']:
            field_name = field_def['name']
            field_type_str = field_def['type']
            field_desc = field_def.get('desc', '')
            
            # Parse the field type
            field_type = self._parse_type(field_type_str)
            
            # Create field definition tuple: (type, Field(...))
            # If field_type is a string (forward reference), use it directly
            field_definitions[field_name] = (field_type, Field(description=field_desc))
        
        # Create the new model using Pydantic's create_model
        if field_definitions:
            # Set up model config to allow arbitrary types if needed
            from pydantic import ConfigDict
            
            # Check if any field uses a custom type that might need arbitrary_types_allowed
            needs_arbitrary_types = any(
                hasattr(field_type, '__name__') and field_type not in [str, int, float, bool, Any, datetime]
                and not hasattr(field_type, '__origin__')  # Not a generic type like List, Dict, etc.
                and field_type not in self.dynamic_models.values()
                for field_type, _ in field_definitions.values()
            )
            
            if needs_arbitrary_types:
                # Create model with arbitrary types allowed
                model_config = ConfigDict(arbitrary_types_allowed=True)
                new_model = create_model(
                    model_name, 
                    __config__=model_config,
                    **field_definitions
                )
            else:
                new_model = create_model(model_name, **field_definitions)
            
            self.dynamic_models[model_name] = new_model
    
    def _parse_type(self, type_str: str) -> Union[type, str]:
        """Parse a type string and return the corresponding Python type or forward reference.
        
        Args:
            type_str: Type string like 'str', 'List[Metric]', 'Optional[int]'
            
        Returns:
            Corresponding Python type or forward reference string
            
        Raises:
            TypeMappingError: If the type cannot be mapped
        """
        type_str = type_str.strip()
        
        # Handle List types
        if type_str.startswith('List[') and type_str.endswith(']'):
            inner_type_str = type_str[5:-1]
            inner_type = self._parse_type(inner_type_str)
            # If inner type is a forward reference (string), keep it as string
            if isinstance(inner_type, str):
                return f"List[{inner_type}]"
            return List[inner_type]
        
        # Handle Optional types
        if type_str.startswith('Optional[') and type_str.endswith(']'):
            inner_type_str = type_str[9:-1]
            inner_type = self._parse_type(inner_type_str)
            if isinstance(inner_type, str):
                return f"Optional[{inner_type}]"
            return Optional[inner_type]
        
        # Handle Union types
        if type_str.startswith('Union[') and type_str.endswith(']'):
            inner_types_str = type_str[6:-1]
            inner_types = [self._parse_type(t.strip()) for t in inner_types_str.split(',')]
            # If any inner type is a forward reference, return the whole thing as string
            if any(isinstance(t, str) for t in inner_types):
                return type_str
            return Union[tuple(inner_types)]
        
        # Handle Dict types
        if type_str.startswith('Dict[') and type_str.endswith(']'):
            inner_types_str = type_str[5:-1]
            key_type_str, value_type_str = [t.strip() for t in inner_types_str.split(',', 1)]
            key_type = self._parse_type(key_type_str)
            value_type = self._parse_type(value_type_str)
            # If either type is a forward reference, return the whole thing as string
            if isinstance(key_type, str) or isinstance(value_type, str):
                return type_str
            return Dict[key_type, value_type]
        
        # Check if it's a custom model - return as forward reference string
        if type_str in [model_def['name'] for model_def in self._current_output_models]:
            return type_str  # Return as forward reference string
        
        # Check if it's a built-in type
        if type_str in self.type_map:
            return self.type_map[type_str]
        
        raise TypeMappingError(f"Unknown type: {type_str}")


def parse_yaml_models(yaml_content: str, custom_types: Optional[Dict[str, type]] = None) -> Dict[str, type]:
    """Convenience function to parse YAML models.
    
    Args:
        yaml_content: YAML string containing model definitions
        custom_types: Optional dictionary of custom type mappings
        
    Returns:
        Dictionary mapping model names to Pydantic model classes
    """
    parser = GemParser()
    
    if custom_types:
        for type_name, python_type in custom_types.items():
            parser.add_type_mapping(type_name, python_type)
    
    return parser.parse_from_yaml_string(yaml_content)


def parse_yaml_file(file_path: Union[str, Path], custom_types: Optional[Dict[str, type]] = None) -> Dict[str, type]:
    """Convenience function to parse YAML models from file.
    
    Args:
        file_path: Path to YAML file containing model definitions
        custom_types: Optional dictionary of custom type mappings
        
    Returns:
        Dictionary mapping model names to Pydantic model classes
    """
    parser = GemParser()
    
    if custom_types:
        for type_name, python_type in custom_types.items():
            parser.add_type_mapping(type_name, python_type)
    
    return parser.parse_from_file(file_path)