
import mcdreforged.api.all as MCDR
from mcdreforged.command.command_manager import CommandManager
from mcdreforged.plugin.plugin_registry import PluginCommandHolder

import loginproxy
from packet_parser.commandnode import Node, NodeStringProp

from .configs import *
from .source import *
from .utils import *

__all__ = [
	'on_command_updated',
	'login_listener',
]

class CommandStorage:
	_nodes: list[Node]
	root: int

	def __init__(self, nodes: list[Node], root: int):
		self._nodes = nodes.copy()
		self.root = root

	def get_nodes(self) -> list[Node]:
		return [Node(n.protocol, n.flags, n.children.copy(), n.redirect_node, n.name, n.parser_id, n.properties, n.suggestions_type) for n in self._nodes]

mcdr_root_commands: dict[str, list[PluginCommandHolder]] = {}
mcdr_root_nodes: dict[int, list[tuple[Node, list[Node]]]] | None = None

def on_command_updated(server: MCDR.PluginServerInterface, command_manager: CommandManager):
	global mcdr_root_commands
	mcdr_root_commands = command_manager.root_nodes
	rebuild_mcdr_command_nodes()

	proxy = loginproxy.get_proxy()
	for conn in proxy.get_conns():
		refresh_commands(conn)

def rebuild_mcdr_command_nodes() -> None:
	global mcdr_root_nodes
	mcdr_root_nodes = None
	root_nodes: dict[int, list[tuple[Node, list[Node]]]] = {}
	protocols = set(conn.protocol for conn in loginproxy.get_proxy().get_conns())
	for protocol in protocols:
		root_nodes[protocol] = build_mcdr_root_nodes(protocol)
	mcdr_root_nodes = root_nodes

def build_mcdr_root_nodes(protocol: int) -> list[tuple[Node, list[Node]]]:
	global mcdr_root_commands
	root_nodes: list[tuple[Node, list[Node]]] = []
	for name, holders in mcdr_root_commands.items():
		node: Node | None = None
		children: list[Node] = []
		for holder in holders:
			node = build_mcdr_node(protocol, name, holder.node, node, children)
			if not holder.allow_duplicates:
				break
		if node is not None:
			root_nodes.append((node, children))
	return root_nodes

def build_mcdr_node(protocol: int, name: str, root: MCDR.Literal, node: Node | None, children: list[Node]) -> Node:
	if node is None:
		node = Node(protocol, Node.LITERAL | Node.EXECUTABLE_FLAG, [], None, name, None, None, None)
		arg_node = Node(protocol, Node.ARGUMENT | Node.EXECUTABLE_FLAG | Node.SUGGESTIONS_FLAG, [], None, 'args...', 5, NodeStringProp.GREEDY_PHRASE, 'minecraft:ask_server')
		children.append(arg_node)
	return node

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
	source = PacketCommandSource(server._mcdr_server, event.conn, text)
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
	source = PacketCommandSource(server._mcdr_server, event.conn, text)
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
	source = PacketCommandSource(server._mcdr_server, event.conn, text)
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

	conn = event.conn
	packet = event.reader
	count = packet.read_varint()
	nodes = []
	for i in range(count):
		nodes.append(Node.parse_from(event.conn.protocol, packet))
	root_index = packet.read_varint()

	conn._custom_data['commands'] = CommandStorage(nodes, root_index)
	refresh_commands(conn)

def refresh_commands(conn: loginproxy.Conn):
	global mcdr_root_nodes
	if mcdr_root_nodes is None:
		return
	mcdr_roots = mcdr_root_nodes.get(conn.protocol, None)
	if mcdr_roots is None:
		new_thread(rebuild_mcdr_command_nodes)()
		return

	storage: CommandStorage = conn._custom_data['commands']
	nodes = storage.get_nodes()
	root_index = storage.root
	root_node = nodes[root_index]

	for node, children in mcdr_roots:
		root_node.children.append(len(nodes))
		nodes.append(node)
		for child in children:
			node.children.append(len(nodes))
			nodes.append(node)

	buf = conn.new_packet('play_commands')
	buf.write_varint(len(nodes))
	for n in nodes:
		n.write_to(buf)
	buf.write_varint(root_index)
	buf.send()

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
