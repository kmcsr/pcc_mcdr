
import mcdreforged.api.all as MCDR

from .utils import *
from . import api

def on_load(server: MCDR.PluginServerInterface, prev_module):
	if prev_module is None:
		log_info('ProxiedChatConnection is on LOAD')
	else:
		log_info('ProxiedChatConnection is on RELOAD')
	api.on_load(server)

def on_unload(server: MCDR.PluginServerInterface):
	log_info('ProxiedChatConnection is on UNLOAD')
