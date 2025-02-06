
import mcdreforged.api.all as MCDR
import mcdreforged.info_reactor.info
from mcdreforged.utils import class_utils

import loginproxy

from .utils import *
from .nodes import *

def on_load(server: MCDR.PluginServerInterface):
	server.register_event_listener(loginproxy.ON_POSTLOGIN, login_listener)
	server.register_event_listener(loginproxy.ON_PACKET_C2S, c2s_packet_listener)
	server.register_event_listener(loginproxy.ON_PACKET_S2C, s2c_packet_listener)

def login_listener(server: MCDR.PluginServerInterface, conn: loginproxy.Conn):
	if conn.protocol < loginproxy.Protocol.V1_19_2:
		return
	conn.send_client(loginproxy.PacketBuffer().write_varint(0x4e).write_bool(True).data)

def c2s_packet_listener(server: MCDR.PluginServerInterface, conn: loginproxy.Conn, packet: loginproxy.PacketReader, cancel):
	if conn.protocol < loginproxy.Protocol.V1_19_2:
		return
	if packet.id == 0x04:
		handle_command_packet(server, conn, packet, cancel)
	elif packet.id == 0x05:
		handle_chat_packet(server, conn, packet, cancel)
	elif packet.id == 0x06:
		handle_chat_preview(server, conn, packet, cancel)
	elif packet.id == 0x09:
		handle_command_suggestion_packet(server, conn, packet, cancel)

def s2c_packet_listener(server: MCDR.PluginServerInterface, conn: loginproxy.Conn, packet: loginproxy.PacketReader, cancel):
	if conn.protocol < loginproxy.Protocol.V1_19_2:
		return
	if packet.id == 0x15: # Chat suggestion
		log_warn('server sent chat suggestion packet')
	elif packet.id == 0x0f: # Commands
		handle_command_nodes(server, conn, packet, cancel)
	elif packet.id == 0x42:
		has_motd = packet.read_bool()
		motd = packet.read_string() if has_motd else None
		has_icon = packet.read_bool()
		icon = packet.read_string() if has_icon else None
		preview_chat = packet.read_bool()
		enforce_secure = packet.read_bool()

		preview_chat = True

		buf = loginproxy.PacketBuffer()
		buf.write_varint(packet.id)
		buf.write_bool(has_motd)
		if motd is not None:
			buf.write_string(motd)
		buf.write_bool(has_icon)
		if icon is not None:
			buf.write_string(icon)
		buf.write_bool(preview_chat)
		buf.write_bool(enforce_secure)
		cancel(buf.data)

def handle_command_packet(server: MCDR.PluginServerInterface, conn: loginproxy.Conn, packet: loginproxy.PacketReader, cancel):
	text = packet.read_string()
	handle_text_packet(server, conn, text, cancel)

def handle_chat_packet(server: MCDR.PluginServerInterface, conn: loginproxy.Conn, packet: loginproxy.PacketReader, cancel):
	text = packet.read_string()
	handle_text_packet(server, conn, text, cancel)

def handle_chat_preview(server: MCDR.PluginServerInterface, conn: loginproxy.Conn, packet: loginproxy.PacketReader, cancel):
	cancel()
	qid = packet.read_int()
	text = packet.read_string()
	buf = loginproxy.PacketBuffer().write_varint(0x0c)
	buf.write_int(qid).write_bool(False)
	conn.send_client(buf.data)

	if not text.startswith('!!'):
		buf = loginproxy.PacketBuffer()
		buf.write_varint(0x15)
		buf.write_varint(2)
		buf.write_varint(0)
		conn.send_client(buf.data)
		return

	command_manager = server._mcdr_server.command_manager
	source = PacketCommandSource(server._mcdr_server, conn.name, text)
	suggestions = command_manager.suggest_command(text + ' ', source)

	buf = loginproxy.PacketBuffer()
	buf.write_varint(0x15)
	buf.write_varint(2)
	buf.write_varint(len(suggestions))
	for suggest in suggestions:
		buf.write_string(suggest.suggest_input)
	conn.send_client(buf.data)

def handle_text_packet(server: MCDR.PluginServerInterface, conn: loginproxy.Conn, text: str, cancel):
	if not text.startswith('!!'):
		return
	source = PacketCommandSource(server._mcdr_server, conn.name, text)
	server.execute_command(text, source)
	cancel()

def handle_command_suggestion_packet(server: MCDR.PluginServerInterface, conn: loginproxy.Conn, packet: loginproxy.PacketReader, cancel):
	tid = packet.read_varint()
	text = packet.read_string()
	begin = 0
	if text.startswith('/!!'):
		begin = 1
		text = text[1:]
	elif not text.startswith('!!'):
		return
	cancel()
	command_manager = server._mcdr_server.command_manager
	source = PacketCommandSource(server._mcdr_server, conn.name, text)
	suggestions = command_manager.suggest_command(text, source)

	min_existed = min(len(suggest.existed_input) for suggest in suggestions) if len(suggestions) > 0 else len(text)

	response = loginproxy.PacketBuffer()
	response.write_varint(0x0e)
	response.write_varint(tid)
	response.write_varint(begin + min_existed)
	response.write_varint(len(text) - min_existed)
	response.write_varint(len(suggestions))
	for suggest in suggestions:
		response.write_string(suggest.command[min_existed:])
		response.write_bool(False)
	conn.send_client(response.data)

def handle_command_nodes(server: MCDR.PluginServerInterface, conn: loginproxy.Conn, packet: loginproxy.PacketReader, cancel):
	count = packet.read_varint()
	nodes = []
	for i in range(count):
		nodes.append(Node.parse_from(packet))
	root_index = packet.read_varint()
	root_node = nodes[root_index]
	def add_root_node(node: Node):
		root_node.children.append(len(nodes))
		nodes.append(node)

	node_mcdr = Node(0x02 | 0x04 | 0x10, [], None, '!!MCDR-commands', 5, NodeStringProp.GREEDY_PHRASE, 'minecraft:ask_server')
	add_root_node(node_mcdr)

	buf = loginproxy.PacketBuffer()
	buf.write_varint(packet.id)
	buf.write_varint(len(nodes))
	for n in nodes:
		n.write_to(buf)
	buf.write_varint(root_index)
	conn.send_client(buf.data)
	cancel()

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
