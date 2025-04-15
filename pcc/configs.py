
import mcdreforged.api.all as MCDR

from kpi.config import *
from kpi.utils import LazyData
from .utils import *

__all__ = [
	'MSG_ID', 'BIG_BLOCK_BEFOR', 'BIG_BLOCK_AFTER',
	'PCCConfig',
	'get_config', 'init',
]

MSG_ID = MCDR.RText('[PCC]', color=MCDR.RColor.dark_red)
BIG_BLOCK_BEFOR = LazyData(lambda data:
	MCDR.RText('------------ {0} v{1} ::::'.format(data.name, data.version), color=MCDR.RColor.aqua))
BIG_BLOCK_AFTER = LazyData(lambda data:
	MCDR.RText(':::: {0} v{1} ============'.format(data.name, data.version), color=MCDR.RColor.aqua))

class PCCConfig(Config, msg_id=MSG_ID):
	# 0:guest 1:user 2:helper 3:admin 4:owner
	class minimum_permission_level(JSONObject):
		pass

	register_vanilla_command: bool = True
	proxy_mcdr_chat_command: bool = True
	chat_preview_suggestion: bool = False

def get_config() -> PCCConfig:
	return PCCConfig.instance()

def init(server: MCDR.PluginServerInterface):
	global BIG_BLOCK_BEFOR, BIG_BLOCK_AFTER
	metadata = server.get_self_metadata()
	LazyData.load(BIG_BLOCK_BEFOR, metadata)
	LazyData.load(BIG_BLOCK_AFTER, metadata)
	PCCConfig.init_instance(server, load_after_init=True).save()
