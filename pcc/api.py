
import contextlib
import functools
from typing import Callable, Iterator, Any, Never

import mcdreforged.api.all as MCDR
from mcdreforged.command.command_manager import CommandManager
from mcdreforged.plugin.plugin_registry import PluginCommandHolder

import loginproxy

from .handler import login_listener, on_command_updated
from .utils import *

def on_load(server: MCDR.PluginServerInterface):
	server.register_event_listener(loginproxy.ON_LOGIN, login_listener)

	log_info(f'patching CommandManager.start_command_register')
	patch_CommandManager_start_command_register(server)

def on_unload(server: MCDR.PluginServerInterface):
	if getattr(CommandManager.start_command_register, '__wrapped_by__', None) is server:
		log_info(f'unpatching CommandManager.start_command_register')
		CommandManager.start_command_register = CommandManager.start_command_register.__wrapped__ # type: ignore

def patch_CommandManager_start_command_register(server: MCDR.PluginServerInterface):
	command_manager_start_command_register = CommandManager.start_command_register

	@functools.wraps(command_manager_start_command_register)
	@contextlib.contextmanager
	def patched_start_command_register(command_manager: CommandManager) -> Iterator[Never]:
		with command_manager_start_command_register(command_manager) as callback:
			yield callback
		on_command_updated(server, command_manager)

	setattr(patched_start_command_register, '__wrapped_by__', server)
	CommandManager.start_command_register = patched_start_command_register # type: ignore
