
import enum
from typing import final, Type, Self, Any, Callable

from loginproxy import PacketBuffer, PacketReader

__all__ = [
	'IntRange',
	'LongRange',
	'FloatRange',
	'DoubleRange',
	'NodeStringProp',
	'NodeEntityProp',
	'NodeScoreHolderProp',
	'Node',
]

@final
class IntRange:
	def __init__(self,
		flags: int, # Byte
		min: int | None, # Optional integer
		max: int | None, # Optional integer
	):
		self.flags = flags
		self.min = min
		self.max = max

	def write_to(self, b: PacketBuffer) -> None:
		b.write_byte(self.flags)
		if self.flags & 0x01:
			assert self.min is not None
			b.write_int(self.min)
		if self.flags & 0x02:
			assert self.max is not None
			b.write_int(self.max)

	@classmethod
	def parse_from(cls, r: PacketReader) -> Self:
		flags = r.read_byte()
		min = r.read_int() if flags & 0x01 else None
		max = r.read_int() if flags & 0x02 else None
		return cls(flags, min, max)

@final
class LongRange:
	def __init__(self,
		flags: int, # Byte
		min: int | None, # Optional long
		max: int | None, # Optional long
	):
		self.flags = flags
		self.min = min
		self.max = max

	def write_to(self, b: PacketBuffer) -> None:
		b.write_byte(self.flags)
		if self.flags & 0x01:
			assert self.min is not None
			b.write_long(self.min)
		if self.flags & 0x02:
			assert self.max is not None
			b.write_long(self.max)

	@classmethod
	def parse_from(cls, r: PacketReader) -> Self:
		flags = r.read_byte()
		min = r.read_long() if flags & 0x01 else None
		max = r.read_long() if flags & 0x02 else None
		return cls(flags, min, max)

@final
class FloatRange:
	def __init__(self,
		flags: int, # Byte
		min: float | None, # Optional float
		max: float | None, # Optional float
	):
		self.flags = flags
		self.min = min
		self.max = max

	def write_to(self, b: PacketBuffer) -> None:
		b.write_byte(self.flags)
		if self.flags & 0x01:
			assert self.min is not None
			b.write_float(self.min)
		if self.flags & 0x02:
			assert self.max is not None
			b.write_float(self.max)

	@classmethod
	def parse_from(cls, r: PacketReader) -> Self:
		flags = r.read_byte()
		min = r.read_float() if flags & 0x01 else None
		max = r.read_float() if flags & 0x02 else None
		return cls(flags, min, max)

@final
class DoubleRange:
	def __init__(self,
		flags: int, # Byte
		min: float | None, # Optional double
		max: float | None, # Optional double
	):
		self.flags = flags
		self.min = min
		self.max = max

	def write_to(self, b: PacketBuffer) -> None:
		b.write_byte(self.flags)
		if self.flags & 0x01:
			assert self.min is not None
			b.write_double(self.min)
		if self.flags & 0x02:
			assert self.max is not None
			b.write_double(self.max)

	@classmethod
	def parse_from(cls, r: PacketReader) -> Self:
		flags = r.read_byte()
		min = r.read_double() if flags & 0x01 else None
		max = r.read_double() if flags & 0x02 else None
		return cls(flags, min, max)

@final
class NodeStringProp(enum.Enum):
	SINGLE_WORD = 0
	QUOTABLE_PHRASE = 1
	GREEDY_PHRASE = 2

	def write_to(self, b: PacketBuffer) -> None:
		b.write_varint(self.value)

	@classmethod
	def parse_from(cls, r: PacketReader) -> Self:
		value = r.read_varint()
		return cls(value)

@final
class NodeEntityProp():
	def __init__(self,
		flags: int, # Byte
	):
		self.flags = flags

	def write_to(self, b: PacketBuffer) -> None:
		b.write_byte(self.flags)

	@classmethod
	def parse_from(cls, r: PacketReader) -> Self:
		flags = r.read_byte()
		return cls(flags)

@final
class NodeScoreHolderProp():
	def __init__(self,
		flags: int, # Byte
	):
		self.flags = flags

	def write_to(self, b: PacketBuffer) -> None:
		b.write_byte(self.flags)

	@classmethod
	def parse_from(cls, r: PacketReader) -> Self:
		flags = r.read_byte()
		return cls(flags)


@final
class Node:
	ID_MAP = {
		0:  'brigadier:bool',
		1:  'brigadier:float',
		2:  'brigadier:double',
		3:  'brigadier:integer',
		4:  'brigadier:long',
		5:  'brigadier:string',
		6:  'minecraft:entity',
		7:  'minecraft:game_profile',
		8:  'minecraft:block_pos',
		9:  'minecraft:column_pos',
		10: 'minecraft:vec3with',
		11: 'minecraft:vec2with',
		12: 'minecraft:block_state',
		13: 'minecraft:block_predicate',
		14: 'minecraft:item_stack',
		15: 'minecraft:item_predicate',
		16: 'minecraft:color',
		17: 'minecraft:component',
		18: 'minecraft:message',
		19: 'minecraft:nbt',
		20: 'minecraft:nbt_tag',
		21: 'minecraft:nbt_path',
		22: 'minecraft:objective',
		23: 'minecraft:objective_criteria',
		24: 'minecraft:operation',
		25: 'minecraft:particle',
		26: 'minecraft:angle',
		27: 'minecraft:rotationwith',
		28: 'minecraft:scoreboard_slot',
		29: 'minecraft:score_holder',
		30: 'minecraft:swizzle',
		31: 'minecraft:team',
		32: 'minecraft:item_slot',
		33: 'minecraft:resource_location',
		34: 'minecraft:function',
		35: 'minecraft:entity_anchor',
		36: 'minecraft:int_range',
		37: 'minecraft:float_range',
		38: 'minecraft:dimension',
		39: 'minecraft:gamemode',
		40: 'minecraft:time',
		41: 'minecraft:resource_or_tag',
		42: 'minecraft:resource_or_tag_key',
		43: 'minecraft:resource',
		44: 'minecraft:resource_key',
		45: 'minecraft:template_mirror',
		46: 'minecraft:template_rotation',
		47: 'minecraft:uuid',
	}

	def __init__(self,
		flags: int, # Byte
		children: list[int], # Array of VarInt
		redirect_node: int | None, # Optional VarInt
		name: str | None, # Optional String (32767)
		parser_id: int | None, # Optional Varint
		properties: Any | None, # Optional Varies
		suggestions_type: str | None, # Optional Identifier
	):
		"""
		Flags:
			| Bit mask | Field Name           | Notes
			| 0x03     | Node type            | 0: root, 1: literal, 2: argument. 3 is not used.
			| 0x04     | Is executable        | Set if the node stack to this point constitutes a valid command.
			| 0x08     | Has redirect         | Set if the node redirects to another node.
			| 0x10     | Has suggestions type | Only present for argument nodes.
		"""
		self.flags = flags
		self.children = children # Array of indices of child nodes.
		self.redirect_node = redirect_node # Only if flags & 0x08. Index of redirect node.
		self.name = name # Only for argument and literal nodes.
		self.parser_id = parser_id # Only for argument nodes.
		self.properties = properties # Only for argument nodes. Varies by parser.
		self.suggestions_type = suggestions_type # Only if flags & 0x10.

	def __str__(self) -> str:
		return f"<Node flags={bin(self.flags)} children={self.children} {f'name=' + self.name if self.name else ''} parser={self.parser_sid} {f'suggestions_type=' + self.suggestions_type if self.suggestions_type else ''}>"

	__repr__ = __str__

	@property
	def parser_sid(self) -> str | None:
		if self.parser_id is None:
			return None
		return self.__class__.ID_MAP[self.parser_id]

	def write_to(self, b: PacketBuffer) -> None:
		b.write_varint(self.flags)
		b.write_varint(len(self.children))
		for child in self.children:
			b.write_varint(child)
		if self.flags & 0x08:
			assert self.redirect_node is not None
			b.write_varint(self.redirect_node)
		if self.flags & 0x03 in (1, 2):
			assert self.name is not None
			b.write_string(self.name)
		if self.flags & 0x03 == 2:
			assert self.parser_id is not None
			b.write_varint(self.parser_id)
			self.__class__.encode_properties(self.parser_id, self.properties, b)
		if self.flags & 0x10:
			assert self.suggestions_type is not None
			b.write_string(self.suggestions_type)

	@classmethod
	def parse_from(cls, r: PacketReader) -> Self:
		flags = r.read_varint()
		children = []
		for _ in range(r.read_varint()):
			child = r.read_varint()
			children.append(child)
		redirect_node = r.read_varint() if flags & 0x08 else None
		name = r.read_string() if flags & 0x03 in (1, 2) else None
		if flags & 0x03 == 2 :
			parser_id = r.read_varint()
			properties = cls.parse_properties(parser_id, r)
		else:
			parser_id = None
			properties = None
		suggestions_type = r.read_string() if flags & 0x10 else None
		return cls(flags, children, redirect_node, name, parser_id, properties, suggestions_type)

	@classmethod
	def encode_properties(cls, parser_id: int, properties: Any, b: PacketBuffer) -> None:
		sid = cls.ID_MAP[parser_id]
		if sid in cls.properties_encoder:
			encoder, _ = cls.properties_encoder[sid]
			encoder(properties, b)

	@classmethod
	def parse_properties(cls, parser_id: int, r: PacketReader) -> Any:
		sid = cls.ID_MAP[parser_id]
		if sid in cls.properties_encoder:
			_, parser = cls.properties_encoder[sid]
			return parser(r)
		return None

	properties_encoder: dict[str, tuple[Callable, Callable]] = {
		'brigadier:double': (DoubleRange.write_to, DoubleRange.parse_from),
		'brigadier:float': (FloatRange.write_to, FloatRange.parse_from),
		'brigadier:integer': (IntRange.write_to, IntRange.parse_from),
		'brigadier:long': (LongRange.write_to, LongRange.parse_from),
		'brigadier:string': (NodeStringProp.write_to, NodeStringProp.parse_from),
		'minecraft:entity': (NodeEntityProp.write_to, NodeEntityProp.parse_from),
		'minecraft:score_holder': (NodeScoreHolderProp.write_to, NodeScoreHolderProp.parse_from),
		# TODO
	}
