
import mcdreforged.api.all as MCDR
import mcdreforged.info_reactor.info
from mcdreforged.utils import class_utils
from mcdreforged.utils.types.message import MessageText

from loginproxy import Conn
from packet_parser import chat_object_to_nbt

__all__ = [
	'PacketCommandSource', 'PlayerChatPacketInfo',
]

class PacketCommandSource(MCDR.PlayerCommandSource):
	def __init__(self, mcdr_server, conn: Conn, chat: str):
		super().__init__(mcdr_server, PlayerChatPacketInfo(conn.name, chat, self), conn.name)

		self.conn = conn
		self.chat = chat

	@property
	def is_player(self) -> bool:
		return True

	def reply(self, message: MessageText, *, encoding: str | None = None, **kwargs):
		if isinstance(message, str):
			message = MCDR.RText(message)
		data = message.to_json_object()
		if isinstance(data, list):
			data = {
				'text': '',
				'extra': data,
			}
		tag = chat_object_to_nbt(data)
		buf = self.conn.new_packet('play_system_chat_message')
		tag.to_bytes(buf)
		buf.write_bool(False)
		buf.send()

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
