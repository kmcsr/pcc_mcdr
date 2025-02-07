
import loginproxy

class Protocol:
	__slots__ = (
		'version',
		# C2S
		'chat_command_id',
		'chat_message_id',
		'command_suggestions_request_id',
		# S2C
		'commands_id',
		'chat_preview_id',
		'command_suggestions_response_id',
		'chat_suggestion_id',
		'server_data_id',
		'set_display_chat_preview_id',
	)

	def __init__(self, version: int):
		self.version = version
