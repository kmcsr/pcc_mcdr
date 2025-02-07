
import mcdreforged.api.all as MCDR
import mcdreforged.info_reactor.info
from mcdreforged.utils import class_utils

__all__ = [
	'PacketCommandSource', 'PlayerChatPacketInfo',
]

class PacketCommandSource(MCDR.PlayerCommandSource):
	def __init__(self, mcdr_server, player: str, chat: str):
		super().__init__(mcdr_server, PlayerChatPacketInfo(player, chat, self), player)

		self.player: str = player
		self.chat: str = chat

	@property
	def is_player(self) -> bool:
		return True

	def reply(self, message, *, encoding: str | None = None, **kwargs):
		self._mcdr_server.basic_server_interface.tell(self.player, message, encoding=encoding)

	def __eq__(self, other) -> bool:
		return isinstance(other, PacketCommandSource) and self.player == other.player

	def __str__(self):
		return 'NetworkPlayer {}'.format(self.player)

	def __repr__(self):
		return class_utils.represent(self, {
			'player': self.player,
			'network': True,
		})

class PlayerChatPacketInfo(MCDR.Info):
	def __init__(self, player: str, chat: str, command_source: PacketCommandSource):
		super().__init__(mcdreforged.info_reactor.info.InfoSource.SERVER, chat)
		self.content = chat
		self.player = player
		self._command_source: PacketCommandSource = command_source

	def get_command_source(self) -> MCDR.InfoCommandSource:
		return self._command_source
