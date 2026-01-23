import json
import pytest

from posthog.temporal.data_imports.sources.common.base import SimpleSource
from posthog.temporal.data_imports.sources.common.config import Config, config
from products.data_warehouse.backend.types import ExternalDataSourceType
from posthog.schema import SourceConfig


@config
class TestConfig(Config):
    """Test config class for testing base source."""
    api_key: str
    endpoint: str = "https://example.com"


class TestSimpleSource(SimpleSource[TestConfig]):
    """Test source class for testing base source."""
    
    @property
    def source_type(self) -> ExternalDataSourceType:
        return ExternalDataSourceType.STRIPE
    
    @property
    def get_source_config(self) -> SourceConfig:
        return SourceConfig(name="test", fields=[])


class TestParseConfig:
    """Tests for the parse_config method."""
    
    def test_parse_config_with_dict_input(self):
        """Test that parse_config works with a dictionary input."""
        source = TestSimpleSource()
        job_inputs = {"api_key": "test_key", "endpoint": "https://api.example.com"}
        
        config = source.parse_config(job_inputs)
        
        assert isinstance(config, TestConfig)
        assert config.api_key == "test_key"
        assert config.endpoint == "https://api.example.com"
    
    def test_parse_config_with_json_string_input(self):
        """Test that parse_config works with a JSON string input."""
        source = TestSimpleSource()
        job_inputs_dict = {"api_key": "test_key", "endpoint": "https://api.example.com"}
        job_inputs_json = json.dumps(job_inputs_dict)
        
        config = source.parse_config(job_inputs_json)
        
        assert isinstance(config, TestConfig)
        assert config.api_key == "test_key"
        assert config.endpoint == "https://api.example.com"
    
    def test_parse_config_with_invalid_json_string(self):
        """Test that parse_config raises ValueError for invalid JSON string."""
        source = TestSimpleSource()
        invalid_json = '{"api_key": "test_key", invalid}'
        
        with pytest.raises(ValueError) as exc_info:
            source.parse_config(invalid_json)
        
        assert "Invalid JSON string for job_inputs" in str(exc_info.value)
    
    def test_parse_config_with_invalid_type(self):
        """Test that parse_config raises TypeError for invalid input type."""
        source = TestSimpleSource()
        
        with pytest.raises(TypeError) as exc_info:
            source.parse_config([1, 2, 3])  # type: ignore
        
        assert "job_inputs must be a dict or JSON string" in str(exc_info.value)
        assert "got list" in str(exc_info.value)
    
    def test_parse_config_with_default_values(self):
        """Test that parse_config uses default values when fields are missing."""
        source = TestSimpleSource()
        job_inputs = {"api_key": "test_key"}
        
        config = source.parse_config(job_inputs)
        
        assert config.api_key == "test_key"
        assert config.endpoint == "https://example.com"  # default value


class TestValidateConfig:
    """Tests for the validate_config method."""
    
    def test_validate_config_with_valid_dict(self):
        """Test that validate_config returns True for valid dictionary input."""
        source = TestSimpleSource()
        job_inputs = {"api_key": "test_key", "endpoint": "https://api.example.com"}
        
        is_valid, errors = source.validate_config(job_inputs)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_config_with_valid_json_string(self):
        """Test that validate_config returns True for valid JSON string input."""
        source = TestSimpleSource()
        job_inputs_dict = {"api_key": "test_key", "endpoint": "https://api.example.com"}
        job_inputs_json = json.dumps(job_inputs_dict)
        
        is_valid, errors = source.validate_config(job_inputs_json)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_config_with_invalid_json_string(self):
        """Test that validate_config returns False for invalid JSON string."""
        source = TestSimpleSource()
        invalid_json = '{"api_key": "test_key", invalid}'
        
        is_valid, errors = source.validate_config(invalid_json)
        
        assert is_valid is False
        assert len(errors) == 1
        assert "Invalid JSON string for job_inputs" in errors[0]
    
    def test_validate_config_with_invalid_type(self):
        """Test that validate_config returns False for invalid input type."""
        source = TestSimpleSource()
        
        is_valid, errors = source.validate_config([1, 2, 3])  # type: ignore
        
        assert is_valid is False
        assert len(errors) == 1
        assert "job_inputs must be a dict or JSON string" in errors[0]
        assert "got list" in errors[0]
    
    def test_validate_config_with_missing_required_field(self):
        """Test that validate_config returns False when required field is missing."""
        source = TestSimpleSource()
        job_inputs = {"endpoint": "https://api.example.com"}  # missing api_key
        
        is_valid, errors = source.validate_config(job_inputs)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("api_key" in error for error in errors)
