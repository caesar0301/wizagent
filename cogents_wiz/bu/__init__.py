import os
from typing import TYPE_CHECKING

from cogents_wiz.bu.logging_config import setup_logging

# Only set up logging if not in MCP mode or if explicitly requested
if os.environ.get('BROWSER_USE_SETUP_LOGGING', 'true').lower() != 'false':
	from cogents_wiz.bu.config import CONFIG

	# Get log file paths from config/environment
	debug_log_file = getattr(CONFIG, 'BROWSER_USE_DEBUG_LOG_FILE', None)
	info_log_file = getattr(CONFIG, 'BROWSER_USE_INFO_LOG_FILE', None)

	# Set up logging with file handlers if specified
	logger = setup_logging(debug_log_file=debug_log_file, info_log_file=info_log_file)
else:
	import logging

	logger = logging.getLogger('browser_use')

# Monkeypatch BaseSubprocessTransport.__del__ to handle closed event loops gracefully
from asyncio import base_subprocess

_original_del = base_subprocess.BaseSubprocessTransport.__del__


def _patched_del(self):
	"""Patched __del__ that handles closed event loops without throwing noisy red-herring errors like RuntimeError: Event loop is closed"""
	try:
		# Check if the event loop is closed before calling the original
		if hasattr(self, '_loop') and self._loop and self._loop.is_closed():
			# Event loop is closed, skip cleanup that requires the loop
			return
		_original_del(self)
	except RuntimeError as e:
		if 'Event loop is closed' in str(e):
			# Silently ignore this specific error
			pass
		else:
			raise


base_subprocess.BaseSubprocessTransport.__del__ = _patched_del


# Type stubs for lazy imports - fixes linter warnings
if TYPE_CHECKING:
	from cogents_wiz.bu.agent.prompts import SystemPrompt
	from cogents_wiz.bu.agent.service import Agent
	from cogents_wiz.bu.agent.views import ActionModel, ActionResult, AgentHistoryList
	from cogents_wiz.bu.browser import BrowserProfile, BrowserSession
	from cogents_wiz.bu.browser import BrowserSession as Browser
	from cogents_wiz.bu.dom.service import DomService
	from cogents_wiz.bu.llm import models
	from cogents_wiz.bu.llm.anthropic.chat import ChatAnthropic
	from cogents_wiz.bu.llm.azure.chat import ChatAzureOpenAI
	from cogents_wiz.bu.llm.google.chat import ChatGoogle
	from cogents_wiz.bu.llm.groq.chat import ChatGroq
	from cogents_wiz.bu.llm.ollama.chat import ChatOllama
	from cogents_wiz.bu.llm.openai.chat import ChatOpenAI
	from cogents_wiz.bu.tools.service import Controller, Tools


# Lazy imports mapping - only import when actually accessed
_LAZY_IMPORTS = {
	# Agent service (heavy due to dependencies)
	'Agent': ('browser_use.agent.service', 'Agent'),
	# System prompt (moderate weight due to agent.views imports)
	'SystemPrompt': ('browser_use.agent.prompts', 'SystemPrompt'),
	# Agent views (very heavy - over 1 second!)
	'ActionModel': ('browser_use.agent.views', 'ActionModel'),
	'ActionResult': ('browser_use.agent.views', 'ActionResult'),
	'AgentHistoryList': ('browser_use.agent.views', 'AgentHistoryList'),
	'BrowserSession': ('browser_use.browser', 'BrowserSession'),
	'Browser': ('browser_use.browser', 'BrowserSession'),  # Alias for BrowserSession
	'BrowserProfile': ('browser_use.browser', 'BrowserProfile'),
	# Tools (moderate weight)
	'Tools': ('browser_use.tools.service', 'Tools'),
	'Controller': ('browser_use.tools.service', 'Controller'),  # alias
	# DOM service (moderate weight)
	'DomService': ('browser_use.dom.service', 'DomService'),
	# Chat models (very heavy imports)
	'ChatOpenAI': ('browser_use.llm.openai.chat', 'ChatOpenAI'),
	'ChatGoogle': ('browser_use.llm.google.chat', 'ChatGoogle'),
	'ChatAnthropic': ('browser_use.llm.anthropic.chat', 'ChatAnthropic'),
	'ChatGroq': ('browser_use.llm.groq.chat', 'ChatGroq'),
	'ChatAzureOpenAI': ('browser_use.llm.azure.chat', 'ChatAzureOpenAI'),
	'ChatOllama': ('browser_use.llm.ollama.chat', 'ChatOllama'),
	# LLM models module
	'models': ('browser_use.llm.models', None),
}


def __getattr__(name: str):
	"""Lazy import mechanism - only import modules when they're actually accessed."""
	if name in _LAZY_IMPORTS:
		module_path, attr_name = _LAZY_IMPORTS[name]
		try:
			from importlib import import_module

			module = import_module(module_path)
			if attr_name is None:
				# For modules like 'models', return the module itself
				attr = module
			else:
				attr = getattr(module, attr_name)
			# Cache the imported attribute in the module's globals
			globals()[name] = attr
			return attr
		except ImportError as e:
			raise ImportError(f'Failed to import {name} from {module_path}: {e}') from e

	raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
	'Agent',
	'BrowserSession',
	'Browser',  # Alias for BrowserSession
	'BrowserProfile',
	'Controller',
	'DomService',
	'SystemPrompt',
	'ActionResult',
	'ActionModel',
	'AgentHistoryList',
	# Chat models
	'ChatOpenAI',
	'ChatGoogle',
	'ChatAnthropic',
	'ChatGroq',
	'ChatAzureOpenAI',
	'ChatOllama',
	'Tools',
	'Controller',
	# LLM models module
	'models',
]
