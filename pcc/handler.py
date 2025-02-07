
import mcdreforged.api.all as MCDR

import loginproxy
from packet_parser.commandnode import Node, NodeStringProp

from .configs import *
from .source import *
from .utils import *

__all__ = [
	'login_listener',
]

def login_listener(server: MCDR.PluginServerInterface, conn: loginproxy.Conn, cancel):
	if conn.protocol < loginproxy.Protocol.V1_19_2:
		return
	cfg = get_config()

	if cfg.proxy_mcdr_chat_command:
		conn.register_packet('play_chat_message', lambda event: handle_chat_message(server, event))
	if cfg.register_vanilla_command:
		conn.register_packet('play_chat_command', lambda event: handle_chat_command(server, event))
		conn.register_packet('play_command_suggestions_request', lambda event: handle_command_suggestions_request(server, event))
		conn.register_packet('play_commands', lambda event: handle_commands(server, event))
	if cfg.chat_preview_suggestion and conn.protocol == loginproxy.Protocol.V1_19_2:
		conn.register_packet('play_chat_preview_c2s', lambda event: handle_chat_preview(server, event))
		conn.register_packet('play_server_data', lambda event: handle_server_data(server, event))
		conn.send_client(loginproxy.PacketBuffer().write_varint(0x4e).write_bool(True).data)

def handle_chat_command(server: MCDR.PluginServerInterface, event: loginproxy.PacketEvent):
	text = event.reader.read_string()
	handle_text_packet(server, event, text)

def handle_chat_message(server: MCDR.PluginServerInterface, event: loginproxy.PacketEvent):
	text = event.reader.read_string()
	handle_text_packet(server, event, text)

def handle_text_packet(server: MCDR.PluginServerInterface, event: loginproxy.PacketEvent, text: str):
	if not text.startswith('!!'):
		return
	log_info(f'Player {repr(event.player)} executing command:', text)
	source = PacketCommandSource(server._mcdr_server, event.player, text)
	server.execute_command(text, source)
	event.cancel()

def handle_chat_preview(server: MCDR.PluginServerInterface, event: loginproxy.PacketEvent):
	event.cancel()

	conn = event.conn
	packet = event.reader
	qid = packet.read_int()
	text = packet.read_string()
	conn.new_packet('play_chat_preview_s2c').\
		write_int(qid).\
		write_bool(False).\
		send()

	if not text.startswith('!!'):
		buf = loginproxy.PacketBuffer()
		conn.new_packet('play_chat_suggestions').\
			write_varint(2).\
			write_varint(0).\
			send()
		return

	command_manager = server._mcdr_server.command_manager
	source = PacketCommandSource(server._mcdr_server, event.player, text)
	suggestions = command_manager.suggest_command(text + ' ', source)

	buf = conn.new_packet('play_chat_suggestions').\
		write_varint(2).\
		write_varint(len(suggestions))
	for suggest in suggestions:
		buf.write_string(suggest.suggest_input)
	buf.send()

def handle_command_suggestions_request(server: MCDR.PluginServerInterface, event: loginproxy.PacketEvent):
	packet = event.reader
	tid = packet.read_varint()
	text = packet.read_string()
	begin = 0
	if text.startswith('/!!'):
		begin = 1
		text = text[1:]
	elif not text.startswith('!!'):
		return

	event.cancel()

	command_manager = server._mcdr_server.command_manager
	source = PacketCommandSource(server._mcdr_server, event.player, text)
	suggestions = command_manager.suggest_command(text, source)

	min_existed = min(len(suggest.existed_input) for suggest in suggestions) if len(suggestions) > 0 else len(text)

	response = event.conn.new_packet('play_command_suggestions_response').\
		write_varint(tid).\
		write_varint(begin + min_existed).\
		write_varint(len(text) - min_existed).\
		write_varint(len(suggestions))
	for suggest in suggestions:
		response.write_string(suggest.command[min_existed:])
		response.write_bool(False)
	response.send()

def handle_commands(server: MCDR.PluginServerInterface, event: loginproxy.PacketEvent):
	event.cancel()

	packet = event.reader
	count = packet.read_varint()
	nodes = []
	for i in range(count):
		nodes.append(Node.parse_from(event.conn.protocol, packet))
	root_index = packet.read_varint()
	root_node = nodes[root_index]
	def add_root_node(node: Node):
		root_node.children.append(len(nodes))
		nodes.append(node)

	node_mcdr = Node(event.conn.protocol, 0x02 | 0x04 | 0x10, [], None, '!!MCDR-commands', 5, NodeStringProp.GREEDY_PHRASE, 'minecraft:ask_server')
	add_root_node(node_mcdr)

	buf = loginproxy.PacketBuffer()
	buf.write_varint(packet.id)
	buf.write_varint(len(nodes))
	for n in nodes:
		n.write_to(buf)
	buf.write_varint(root_index)
	event.conn.send_client(buf.data)

def handle_server_data(server: MCDR.PluginServerInterface, event: loginproxy.PacketEvent):
	event.cancel()

	packet = event.reader
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
	event.conn.send_client(buf.data)
