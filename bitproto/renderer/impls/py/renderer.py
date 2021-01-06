"""
Renderer for Python.
"""
from typing import List

from bitproto._ast import MessageField
from bitproto.renderer.block import (Block, BlockAheadNotice, BlockBindAlias,
                                     BlockBindConstant, BlockBindEnum,
                                     BlockBindEnumField, BlockBindMessage,
                                     BlockBindMessageField, BlockBindProto,
                                     BlockComposition, BlockWrapper)
from bitproto.renderer.impls.py.formatter import PyFormatter as F
from bitproto.renderer.renderer import Renderer
from bitproto.utils import cached_property, override


class BlockStatementPass(Block[F]):
    @override(Block)
    def render(self) -> None:
        self.push("pass")


class BlockProtoDocstring(BlockBindProto[F]):
    @override(Block)
    def render(self) -> None:
        self.push_definition_docstring()


class BlockGeneralImports(Block[F]):
    @override(Block)
    def render(self) -> None:
        self.push("from dataclasses import dataclass, field")
        self.push("from typing import ClassVar, Dict, List")


class BlockGeneralFunctionInt8(Block[F]):
    @override(Block)
    def render(self) -> None:
        self.push("def int8(i: int) -> int:")
        self.push("return i if i < 128 else i - 256", indent=4)


class BlockGeneralFunctionInt16(Block[F]):
    @override(Block)
    def render(self) -> None:
        self.push("def int16(i: int) -> int:")
        self.push("return i if i < 32768 else i - 65536", indent=4)


class BlockGeneralFunctionInt32(Block[F]):
    @override(Block)
    def render(self) -> None:
        self.push("def int32(i: int) -> int:")
        self.push("return i if i < 2147483648 else i - 4294967296", indent=4)


class BlockGeneralFunctionInt64(Block[F]):
    @override(Block)
    def render(self) -> None:
        self.push("def int64(i: int) -> int:")
        self.push(
            "return i if i < 9223372036854775808 else i - 18446744073709551616",
            indent=4,
        )


class BlockGeneralGlobalFunctions(BlockComposition[F]):
    @override(BlockComposition)
    def separator(self) -> str:
        return "\n\n\n"

    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockGeneralFunctionInt8(),
            BlockGeneralFunctionInt16(),
            BlockGeneralFunctionInt32(),
            BlockGeneralFunctionInt64(),
        ]


class BlockImportChildProto(BlockBindProto[F]):
    @override(Block)
    def render(self) -> None:
        statement = self.formatter.format_import_statement(self.d, as_name=self.name)
        self.push(statement)


class BlockImportChildProtoList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockImportChildProto(proto, name=name)
            for name, proto in self.bound.protos(recursive=False)
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockImportList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockGeneralImports(),
            BlockImportChildProtoList(),
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n\n"


class BlockAlias(BlockBindAlias[F]):
    @cached_property
    def alias_name(self) -> str:
        return self.formatter.format_alias_name(self.d)

    @cached_property
    def alias_type(self) -> str:
        return self.formatter.format_type(self.d.type)

    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        self.push(f"{self.alias_name} = {self.alias_type}")


class BlockAliasList(BlockComposition):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockAlias(alias, name=name)
            for name, alias in self.bound.aliases(recursive=True, bound=self.bound)
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockConstant(BlockBindConstant[F]):
    @cached_property
    def constant_name(self) -> str:
        return self.formatter.format_constant_name(self.d)

    @cached_property
    def constant_value(self) -> str:
        return self.formatter.format_value(self.d.value)

    @cached_property
    def constant_type(self) -> str:
        return self.formatter.format_constant_type(self.d)

    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        self.push(f"{self.constant_name}: {self.constant_type} = {self.constant_value}")


class BlockConstantList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockConstant(constant, name=name)
            for name, constant in self.bound.constants(recursive=True, bound=self.bound)
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockEnumFieldBase(BlockBindEnumField[F]):
    @cached_property
    def field_name(self) -> str:
        return self.formatter.format_enum_field_name(self.d)

    @cached_property
    def field_value(self) -> str:
        return self.formatter.format_int_value(self.d.value)

    @cached_property
    def field_type(self) -> str:
        enum = self.d.enum
        return self.formatter.format_enum_type(enum)


class BlockEnumField(BlockEnumFieldBase):
    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        self.push(f"{self.field_name}: {self.field_type} = {self.field_value}")


class BlockEnumBase(BlockBindEnum[F]):
    @cached_property
    def enum_type_name(self) -> str:
        return self.formatter.format_enum_type(self.d)


class BlockEnumFieldList(BlockEnumBase, BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [BlockEnumField(field) for field in self.d.fields()]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockEnumFieldListWrapper(BlockEnumBase, BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block:
        return BlockEnumFieldList(self.d)

    @override(BlockWrapper)
    def before(self) -> None:
        self.render_enum_type()

    def render_enum_type(self) -> None:
        self.push_definition_comments()
        self.push(f"{self.enum_type_name} = int")


class BlockEnumValueToNameMapItem(BlockEnumFieldBase):
    @override(Block)
    def render(self) -> None:
        self.push(f'{self.field_value}: "{self.field_name}",')


class BlockEnumValueToNameMapItemList(BlockEnumBase, BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockEnumValueToNameMapItem(field, indent=4) for field in self.d.fields()
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockEnumValueToNameMap(BlockEnumBase, BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block:
        return BlockEnumValueToNameMapItemList(self.d)

    @override(BlockWrapper)
    def before(self) -> None:
        map_name = self.formatter.format_enum_value_to_name_map_name(self.d)
        self.push(f"{map_name}: Dict[{self.enum_type_name}, str] = {{")

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("}")


class BlockEnum(BlockEnumBase, BlockComposition[F]):
    @override(BlockComposition[F])
    def blocks(self) -> List[Block]:
        return [
            BlockEnumFieldListWrapper(self.d),
            BlockEnumValueToNameMap(self.d),
        ]


class BlockEnumList(BlockComposition[F]):
    @override(BlockComposition[F])
    def blocks(self) -> List[Block]:
        return [
            BlockEnum(enum)
            for name, enum in self.bound.enums(recursive=True, bound=self.bound)
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n\n\n"


class BlockMessageField(BlockBindMessageField[F]):
    @cached_property
    def field_name(self) -> str:
        return self.d.name

    @cached_property
    def field_type(self) -> str:
        return self.formatter.format_type(self.d.type)

    @cached_property
    def field_default_value(self) -> str:
        return self.formatter.format_field_default_value(self.d.type)

    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        self.push(f"{self.field_name}: {self.field_type} = {self.field_default_value}")


class BlockMessageBase(BlockBindMessage[F]):
    @cached_property
    def class_name(self) -> str:
        return self.formatter.format_message_name(self.d)


class BlockMessageSize(BlockMessageBase):
    @override(Block)
    def render(self) -> None:
        self.push_comment(f"Number of bytes to serialize class {self.class_name}")
        nbytes = self.formatter.format_int_value(self.d.nbytes())
        self.push(f"MESSAGE_BYTES_LENGTH: ClassVar[int] = {nbytes}")


class BlockMessageFieldList(BlockMessageBase, BlockComposition[F]):
    @cached_property
    def fields(self) -> List[MessageField]:
        return self.d.sorted_fields()

    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        fields = self.d.sorted_fields()
        return [BlockMessageField(field, indent=self.indent) for field in fields]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockMessageClassDefs(BlockMessageBase, BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockMessageSize(self.d, indent=self.indent),
            BlockMessageFieldList(self.d, indent=self.indent),
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n\n"


class BlockMessageClass(BlockMessageBase, BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block[F]:
        return BlockMessageClassDefs(self.d, indent=4)

    @override(BlockWrapper)
    def before(self) -> None:
        self.push("@dataclass")
        self.push(f"class {self.class_name}:")
        self.push_definition_docstring(indent=4)


class BlockMessage(BlockMessageBase, BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [BlockMessageClass(self.d)]


class BlockMessageList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockMessage(message, name=name)
            for name, message in self.bound.messages(recursive=True, bound=self.bound)
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n\n\n"


class BlockHeadList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockAheadNotice(),
            BlockProtoDocstring(self.bound),
            BlockImportList(),
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n\n"


class BlockList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockHeadList(),
            BlockGeneralGlobalFunctions(),
            BlockAliasList(),
            BlockConstantList(),
            BlockEnumList(),
            BlockMessageList(),
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n\n\n"


class RendererPy(Renderer[F]):
    """Renderer for Python language."""

    @override(Renderer)
    def file_extension(self) -> str:
        return ".py"

    @override(Renderer)
    def formatter(self) -> F:
        return F()

    @override(Renderer)
    def block(self) -> Block[F]:
        return BlockList()
