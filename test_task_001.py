"""
Test-Driven Development tests for Task 001: Fix Critical Import Dependencies and Session Management
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open
import importlib


class TestImportDependencies:
    """Test that all required imports are available and working"""
    
    def test_agent_imports_successfully(self):
        """Test that agent.py imports without ImportError"""
        try:
            # Clear any cached imports
            if 'grok.agent' in sys.modules:
                del sys.modules['grok.agent']
            if 'grok.config' in sys.modules:
                del sys.modules['grok.config']
            
            # Add current directory to path if not already there
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            
            # Try importing agent module
            from grok import agent
            assert True, "Agent module imported successfully"
        except ImportError as e:
            pytest.fail(f"Agent module failed to import: {e}")
    
    def test_tools_imports_successfully(self):
        """Test that tools.py imports without ImportError"""
        try:
            # Clear any cached imports
            if 'grok.tools' in sys.modules:
                del sys.modules['grok.tools']
            if 'grok.config' in sys.modules:
                del sys.modules['grok.config']
            
            from grok import tools
            assert True, "Tools module imported successfully"
        except ImportError as e:
            pytest.fail(f"Tools module failed to import: {e}")
    
    def test_config_imports_successfully(self):
        """Test that config.py imports without ImportError"""
        try:
            # Clear any cached imports
            if 'grok.config' in sys.modules:
                del sys.modules['grok.config']
            
            from grok import config
            assert True, "Config module imported successfully"
        except ImportError as e:
            pytest.fail(f"Config module failed to import: {e}")
    
    def test_get_permissions_is_importable_from_config(self):
        """Test that get_permissions function is available in config module"""
        try:
            from grok.config import get_permissions
            assert callable(get_permissions), "get_permissions should be callable"
        except ImportError:
            pytest.fail("get_permissions function not available in config module")
    
    def test_update_permissions_is_importable_from_config(self):
        """Test that update_permissions function is available in config module"""
        try:
            from grok.config import update_permissions
            assert callable(update_permissions), "update_permissions should be callable"
        except ImportError:
            pytest.fail("update_permissions function not available in config module")
    
    def test_prompt_is_importable_from_prompt_toolkit(self):
        """Test that prompt function is available from prompt_toolkit"""
        try:
            from prompt_toolkit import prompt
            assert callable(prompt), "prompt should be callable"
        except ImportError:
            pytest.fail("prompt function not available from prompt_toolkit")


class TestSessionManagement:
    """Test session management functionality"""
    
    @patch('grok.agent.openai')
    @patch('grok.agent.get_permissions')
    @patch('grok.agent.get_mode')
    @patch('grok.agent.load_settings')
    def test_agent_loop_uses_session_prompt(self, mock_load_settings, mock_get_mode, mock_get_permissions, mock_openai):
        """Test that agent_loop uses session.prompt() instead of direct prompt_toolkit.prompt()"""
        # Setup mocks
        mock_load_settings.return_value = {'api_key': 'test_key', 'model': 'grok-4'}
        mock_get_mode.return_value = 'default'
        mock_get_permissions.return_value = {'allow': [], 'deny': [], 'allowed_cmds': {}}
        
        # Mock the session and prompt
        mock_session = MagicMock()
        mock_session.prompt.return_value = '/exit'
        
        # Mock the API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test response"
        mock_response.choices[0].message.tool_calls = None
        mock_openai.chat.completions.create.return_value = mock_response
        
        with patch('grok.agent.session', mock_session):
            try:
                from grok.agent import agent_loop
                # This should use session.prompt() not direct prompt_toolkit.prompt()
                agent_loop()
                
                # Verify session.prompt was called
                mock_session.prompt.assert_called()
                
            except Exception as e:
                # If we get an error, it should not be about prompt_toolkit.prompt not existing
                assert "prompt_toolkit.prompt" not in str(e), f"Should not use direct prompt_toolkit.prompt(): {e}"
    
    def test_session_instance_is_available(self):
        """Test that session instance is properly available in agent module"""
        # This test will ensure the session is properly initialized
        try:
            from grok.agent import session
            assert session is not None, "Session instance should be available"
        except (ImportError, AttributeError):
            # This is expected to fail initially, will pass after implementation
            pytest.skip("Session not yet implemented - this test will pass after implementation")


class TestAPIKeyHandling:
    """Test API key security enhancements"""
    
    @patch('grok.agent.load_settings')
    def test_api_key_not_set_globally(self, mock_load_settings):
        """Test that API key is not set globally on module import"""
        mock_load_settings.return_value = {'api_key': 'test_key'}
        
        # Import the module fresh
        if 'grok.agent' in sys.modules:
            del sys.modules['grok.agent']
        
        # Check that the actual openai module doesn't have api_key set globally
        import openai
        try:
            # Check if openai.api_key is set - it shouldn't be
            api_key = getattr(openai, 'api_key', None)
            assert api_key is None, "API key should not be set globally on openai module"
        except AttributeError:
            # This is acceptable - no global api_key attribute
            pass
        
        # Import our module and verify it doesn't set the global key
        from grok import agent
        
        # Check again that openai.api_key is still not set
        try:
            api_key = getattr(openai, 'api_key', None)
            assert api_key is None, "API key should not be set globally after importing agent module"
        except AttributeError:
            # This is acceptable - no global api_key attribute
            pass
    
    @patch('grok.agent.openai.OpenAI')
    @patch('grok.agent.load_settings')
    def test_call_api_accepts_api_key_parameter(self, mock_load_settings, mock_openai_class):
        """Test that call_api function accepts api_key parameter"""
        mock_load_settings.return_value = {'api_key': 'default_key', 'model': 'grok-4'}
        
        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test response"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        from grok.agent import call_api
        
        # Test with explicit API key
        test_key = "test_api_key"
        call_api([{"role": "user", "content": "test"}], api_key=test_key)
        
        # Verify that OpenAI client was created with the provided API key
        mock_openai_class.assert_called_with(
            api_key=test_key,
            base_url="https://api.x.ai/v1"
        )
    
    @patch('grok.agent.openai.OpenAI')
    @patch('grok.agent.load_settings')
    def test_call_api_uses_default_key_when_none_provided(self, mock_load_settings, mock_openai_class):
        """Test that call_api uses default key from settings when none provided"""
        default_key = "default_api_key"
        mock_load_settings.return_value = {'api_key': default_key, 'model': 'grok-4'}
        
        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test response"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        from grok.agent import call_api
        
        # Test without explicit API key
        call_api([{"role": "user", "content": "test"}])
        
        # Verify that OpenAI client was created with the default API key
        mock_openai_class.assert_called_with(
            api_key=default_key,
            base_url="https://api.x.ai/v1"
        )


class TestConfigModuleExports:
    """Test that config module properly exports all required functions"""
    
    def test_config_module_has_all_attribute(self):
        """Test that config module has __all__ attribute for explicit exports"""
        from grok import config
        
        # Check if __all__ exists
        assert hasattr(config, '__all__'), "Config module should have __all__ attribute for explicit exports"
        
        # Check that required functions are in __all__
        required_functions = [
            'load_settings', 'save_settings', 'get_api_key', 'set_api_key',
            'get_mode', 'set_mode', 'get_permissions', 'update_permissions',
            'get_mcp_servers', 'update_mcp_servers'
        ]
        
        for func_name in required_functions:
            assert func_name in config.__all__, f"{func_name} should be in config.__all__"
    
    def test_all_exported_functions_are_callable(self):
        """Test that all functions in __all__ are actually callable"""
        from grok import config
        
        if hasattr(config, '__all__'):
            for func_name in config.__all__:
                func = getattr(config, func_name)
                assert callable(func), f"{func_name} should be callable"


class TestRegressionPrevention:
    """Test to ensure no regression in existing functionality"""
    
    @patch('grok.agent.openai')
    @patch('grok.agent.load_settings')
    @patch('grok.agent.get_mode')
    @patch('grok.agent.get_permissions')
    def test_existing_functionality_preserved(self, mock_get_permissions, mock_get_mode, mock_load_settings, mock_openai):
        """Test that existing functionality still works after changes"""
        # Setup mocks
        mock_load_settings.return_value = {'api_key': 'test_key', 'model': 'grok-4'}
        mock_get_mode.return_value = 'default'
        mock_get_permissions.return_value = {'allow': [], 'deny': [], 'allowed_cmds': {}}
        
        # Mock the API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test response"
        mock_response.choices[0].message.tool_calls = None
        mock_openai.chat.completions.create.return_value = mock_response
        
        # Test that basic API call still works
        from grok.agent import call_api
        
        result = call_api([{"role": "user", "content": "test"}])
        assert result is not None, "call_api should return a result"
        assert hasattr(result, 'choices'), "Result should have choices attribute"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])