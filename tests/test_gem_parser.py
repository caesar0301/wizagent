"""
Unit tests for the wizagent.gems.gem_parser module.
"""

import pytest
import tempfile
import os
from datetime import datetime
from typing import List, Optional, Dict, Union, Any
from pydantic import BaseModel

from wizagent.gems.gem_parser import (
    GemParser,
    GemParserError,
    TypeMappingError,
    CircularReferenceError,
    parse_yaml_models,
    parse_yaml_file,
)


class TestGemParser:
    """Test cases for the GemParser class."""
    
    def test_basic_model_parsing(self):
        """Test parsing a simple model with basic types."""
        yaml_content = """
task: StructuredExtraction
metadata:
  name: basic test
output_models:
  - name: SimpleModel
    fields:
    - name: text_field
      type: str
      desc: A text field
    - name: number_field
      type: int
      desc: A number field
    - name: flag_field
      type: bool
      desc: A boolean field
"""
        
        parser = GemParser()
        models = parser.parse_from_yaml_string(yaml_content)
        
        assert 'SimpleModel' in models
        SimpleModel = models['SimpleModel']
        
        # Test model creation
        instance = SimpleModel(text_field="test", number_field=42, flag_field=True)
        assert instance.text_field == "test"
        assert instance.number_field == 42
        assert instance.flag_field is True
        
        # Test field descriptions
        fields = SimpleModel.model_fields
        assert fields['text_field'].description == "A text field"
        assert fields['number_field'].description == "A number field"
        assert fields['flag_field'].description == "A boolean field"
    
    def test_cross_reference_models(self):
        """Test parsing models with cross-references (the main example)."""
        yaml_content = """
task: StructuredExtraction
metadata:
  name: hello world
output_models:
  - name: Metric
    fields:
    - name: metric_key
      type: str
      desc: metric name string
    - name: metric_time
      type: Any
      desc: collection timestamp of metric
  - name: Stock
    fields:
    - name: metrics
      type: List[Metric]
      desc: all metrics of stock
"""
        
        parser = GemParser()
        models = parser.parse_from_yaml_string(yaml_content)
        
        assert 'Metric' in models
        assert 'Stock' in models
        
        Metric = models['Metric']
        Stock = models['Stock']
        
        # Test creating instances
        metric1 = Metric(metric_key="price", metric_time=1678886400)
        metric2 = Metric(metric_key="volume", metric_time=1678886500)
        
        stock = Stock(metrics=[metric1, metric2])
        
        assert len(stock.metrics) == 2
        assert stock.metrics[0].metric_key == "price"
        assert stock.metrics[1].metric_key == "volume"
        
        # Test validation
        with pytest.raises(Exception):  # Should fail validation
            Stock(metrics=[{"invalid": "data"}])
    
    def test_complex_types(self):
        """Test parsing models with complex type annotations."""
        yaml_content = """
task: StructuredExtraction
output_models:
  - name: ComplexModel
    fields:
    - name: optional_field
      type: Optional[str]
      desc: An optional string field
    - name: dict_field
      type: Dict[str, int]
      desc: A dictionary field
    - name: union_field
      type: Union[str, int]
      desc: A union field
    - name: datetime_field
      type: datetime
      desc: A datetime field
"""
        
        parser = GemParser()
        models = parser.parse_from_yaml_string(yaml_content)
        
        ComplexModel = models['ComplexModel']
        
        # Test with valid data
        instance = ComplexModel(
            optional_field="test",
            dict_field={"key1": 1, "key2": 2},
            union_field="string_value",
            datetime_field=datetime.now()
        )
        
        assert instance.optional_field == "test"
        assert instance.dict_field == {"key1": 1, "key2": 2}
        assert instance.union_field == "string_value"
        assert isinstance(instance.datetime_field, datetime)
        
        # Test with None optional field
        instance2 = ComplexModel(
            optional_field=None,
            dict_field={},
            union_field=42,
            datetime_field=datetime.now()
        )
        
        assert instance2.optional_field is None
        assert instance2.union_field == 42
    
    def test_custom_type_mapping(self):
        """Test adding custom type mappings."""
        class CustomType:
            def __init__(self, value):
                self.value = value
        
        yaml_content = """
output_models:
  - name: CustomModel
    fields:
    - name: custom_field
      type: custom_type
      desc: A custom type field
"""
        
        parser = GemParser()
        parser.add_type_mapping('custom_type', CustomType)
        
        models = parser.parse_from_yaml_string(yaml_content)
        CustomModel = models['CustomModel']
        
        # The field should accept the custom type
        fields = CustomModel.model_fields
        # Note: The actual type checking depends on Pydantic's behavior with custom types
    
    def test_circular_reference_detection(self):
        """Test detection of circular references between models."""
        yaml_content = """
output_models:
  - name: ModelA
    fields:
    - name: b_ref
      type: ModelB
      desc: Reference to ModelB
  - name: ModelB
    fields:
    - name: a_ref
      type: ModelA
      desc: Reference to ModelA
"""
        
        parser = GemParser()
        
        with pytest.raises(CircularReferenceError):
            parser.parse_from_yaml_string(yaml_content)
    
    def test_missing_output_models(self):
        """Test error handling when output_models is missing."""
        yaml_content = """
task: StructuredExtraction
metadata:
  name: invalid test
"""
        
        parser = GemParser()
        
        with pytest.raises(GemParserError, match="YAML must contain 'output_models' key"):
            parser.parse_from_yaml_string(yaml_content)
    
    def test_invalid_yaml(self):
        """Test error handling for invalid YAML."""
        invalid_yaml = """
task: StructuredExtraction
invalid: yaml: content:
  - broken
"""
        
        parser = GemParser()
        
        with pytest.raises(GemParserError, match="Failed to parse YAML"):
            parser.parse_from_yaml_string(invalid_yaml)
    
    def test_unknown_type(self):
        """Test error handling for unknown types."""
        yaml_content = """
output_models:
  - name: BadModel
    fields:
    - name: bad_field
      type: UnknownType
      desc: A field with unknown type
"""
        
        parser = GemParser()
        
        with pytest.raises(TypeMappingError, match="Unknown type: UnknownType"):
            parser.parse_from_yaml_string(yaml_content)
    
    def test_nested_list_types(self):
        """Test parsing nested list types."""
        yaml_content = """
output_models:
  - name: Item
    fields:
    - name: name
      type: str
      desc: Item name
  - name: Container
    fields:
    - name: items
      type: List[Item]
      desc: List of items
  - name: SuperContainer
    fields:
    - name: containers
      type: List[Container]
      desc: List of containers
"""
        
        parser = GemParser()
        models = parser.parse_from_yaml_string(yaml_content)
        
        Item = models['Item']
        Container = models['Container']
        SuperContainer = models['SuperContainer']
        
        # Test nested structure
        item1 = Item(name="item1")
        item2 = Item(name="item2")
        container = Container(items=[item1, item2])
        super_container = SuperContainer(containers=[container])
        
        assert len(super_container.containers) == 1
        assert len(super_container.containers[0].items) == 2
        assert super_container.containers[0].items[0].name == "item1"
    
    def test_file_parsing(self):
        """Test parsing from file."""
        yaml_content = """
output_models:
  - name: FileModel
    fields:
    - name: field1
      type: str
      desc: First field
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            parser = GemParser()
            models = parser.parse_from_file(temp_path)
            
            assert 'FileModel' in models
            FileModel = models['FileModel']
            
            instance = FileModel(field1="test")
            assert instance.field1 == "test"
        finally:
            os.unlink(temp_path)
    
    def test_file_not_found(self):
        """Test error handling when file doesn't exist."""
        parser = GemParser()
        
        with pytest.raises(GemParserError, match="Failed to read file"):
            parser.parse_from_file("/nonexistent/path/file.yaml")
    
    def test_empty_fields(self):
        """Test model with no fields."""
        yaml_content = """
output_models:
  - name: EmptyModel
"""
        
        parser = GemParser()
        models = parser.parse_from_yaml_string(yaml_content)
        
        EmptyModel = models['EmptyModel']
        instance = EmptyModel()
        
        # Should work fine with no fields
        assert isinstance(instance, BaseModel)
    
    def test_model_order_independence(self):
        """Test that model definition order doesn't matter."""
        yaml_content = """
output_models:
  - name: Stock
    fields:
    - name: metrics
      type: List[Metric]
      desc: all metrics of stock
  - name: Metric
    fields:
    - name: metric_key
      type: str
      desc: metric name string
"""
        
        parser = GemParser()
        models = parser.parse_from_yaml_string(yaml_content)
        
        # Should work even though Stock is defined before Metric
        Metric = models['Metric']
        Stock = models['Stock']
        
        metric = Metric(metric_key="test")
        stock = Stock(metrics=[metric])
        
        assert stock.metrics[0].metric_key == "test"


class TestConvenienceFunctions:
    """Test the convenience functions."""
    
    def test_parse_yaml_models(self):
        """Test the parse_yaml_models convenience function."""
        yaml_content = """
output_models:
  - name: TestModel
    fields:
    - name: field1
      type: str
      desc: Test field
"""
        
        models = parse_yaml_models(yaml_content)
        assert 'TestModel' in models
        
        TestModel = models['TestModel']
        instance = TestModel(field1="test")
        assert instance.field1 == "test"
    
    def test_parse_yaml_models_with_custom_types(self):
        """Test parse_yaml_models with custom type mappings."""
        class MyCustomType:
            pass
        
        yaml_content = """
output_models:
  - name: CustomModel
    fields:
    - name: custom_field
      type: my_custom
      desc: Custom field
"""
        
        custom_types = {'my_custom': MyCustomType}
        models = parse_yaml_models(yaml_content, custom_types=custom_types)
        
        assert 'CustomModel' in models
    
    def test_parse_yaml_file_function(self):
        """Test the parse_yaml_file convenience function."""
        yaml_content = """
output_models:
  - name: FileTestModel
    fields:
    - name: field1
      type: str
      desc: Test field
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            models = parse_yaml_file(temp_path)
            assert 'FileTestModel' in models
            
            FileTestModel = models['FileTestModel']
            instance = FileTestModel(field1="test")
            assert instance.field1 == "test"
        finally:
            os.unlink(temp_path)


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_complex_nested_types(self):
        """Test very complex nested type structures."""
        yaml_content = """
output_models:
  - name: BaseItem
    fields:
    - name: id
      type: str
      desc: Item ID
  - name: ComplexModel
    fields:
    - name: nested_dict
      type: Dict[str, List[BaseItem]]
      desc: Complex nested structure
    - name: optional_list
      type: Optional[List[str]]
      desc: Optional list of strings
"""
        
        parser = GemParser()
        models = parser.parse_from_yaml_string(yaml_content)
        
        BaseItem = models['BaseItem']
        ComplexModel = models['ComplexModel']
        
        item = BaseItem(id="test123")
        complex_instance = ComplexModel(
            nested_dict={"key1": [item]},
            optional_list=["a", "b", "c"]
        )
        
        assert complex_instance.nested_dict["key1"][0].id == "test123"
        assert complex_instance.optional_list == ["a", "b", "c"]
    
    def test_self_reference_error(self):
        """Test that self-references are detected as circular."""
        yaml_content = """
output_models:
  - name: SelfRef
    fields:
    - name: self_field
      type: SelfRef
      desc: Self reference
"""
        
        parser = GemParser()
        
        with pytest.raises(CircularReferenceError):
            parser.parse_from_yaml_string(yaml_content)
    
    def test_invalid_output_models_type(self):
        """Test error when output_models is not a list."""
        yaml_content = """
output_models: "not a list"
"""
        
        parser = GemParser()
        
        with pytest.raises(GemParserError, match="'output_models' must be a list"):
            parser.parse_from_yaml_string(yaml_content)
    
    def test_missing_field_name(self):
        """Test handling of missing field names."""
        yaml_content = """
output_models:
  - name: BadFieldModel
    fields:
    - type: str
      desc: Missing name field
"""
        
        parser = GemParser()
        
        # This should raise an error when trying to access the missing 'name' key
        with pytest.raises(KeyError):
            parser.parse_from_yaml_string(yaml_content)
    
    def test_missing_field_type(self):
        """Test handling of missing field types."""
        yaml_content = """
output_models:
  - name: BadFieldModel
    fields:
    - name: bad_field
      desc: Missing type field
"""
        
        parser = GemParser()
        
        # This should raise an error when trying to access the missing 'type' key
        with pytest.raises(KeyError):
            parser.parse_from_yaml_string(yaml_content)
    
    def test_type_dependency_extraction(self):
        """Test the type dependency extraction logic."""
        parser = GemParser()
        
        # Test various type patterns
        assert parser._extract_type_dependencies("str") == set()
        assert parser._extract_type_dependencies("List[CustomType]") == {"CustomType"}
        assert parser._extract_type_dependencies("Dict[str, CustomType]") == {"CustomType"}
        assert parser._extract_type_dependencies("Optional[CustomType]") == {"CustomType"}
        assert parser._extract_type_dependencies("Union[str, CustomType]") == {"CustomType"}
        assert parser._extract_type_dependencies("List[Dict[str, CustomType]]") == {"CustomType"}
    
    def test_multiple_dependencies(self):
        """Test models with multiple dependencies."""
        yaml_content = """
output_models:
  - name: ModelA
    fields:
    - name: field_a
      type: str
      desc: String field
  - name: ModelB
    fields:
    - name: field_b
      type: int
      desc: Int field
  - name: ModelC
    fields:
    - name: a_ref
      type: ModelA
      desc: Reference to A
    - name: b_ref
      type: ModelB
      desc: Reference to B
    - name: mixed_list
      type: List[Union[ModelA, ModelB]]
      desc: Mixed list
"""
        
        parser = GemParser()
        models = parser.parse_from_yaml_string(yaml_content)
        
        ModelA = models['ModelA']
        ModelB = models['ModelB']
        ModelC = models['ModelC']
        
        # Test creating instances
        a = ModelA(field_a="test")
        b = ModelB(field_b=42)
        c = ModelC(a_ref=a, b_ref=b, mixed_list=[a, b])
        
        assert c.a_ref.field_a == "test"
        assert c.b_ref.field_b == 42
        assert len(c.mixed_list) == 2


if __name__ == '__main__':
    pytest.main([__file__])