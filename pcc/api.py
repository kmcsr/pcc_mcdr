
import mcdreforged.api.all as MCDR

import loginproxy

from .handler import login_listener

def on_load(server: MCDR.PluginServerInterface):
	server.register_event_listener(loginproxy.ON_POST_LOGIN, login_listener)
