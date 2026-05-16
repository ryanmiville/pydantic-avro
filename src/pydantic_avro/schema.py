from __future__ import annotations

import copy
import inspect
import re
import types
from dataclasses import dataclass, field
from enum import Enum
from typing import Annotated, Any, Literal, Union, get_args, get_origin

from fastavro import parse_schema
from pydantic_core import PydanticUndefined

from .errors import AvroSchemaGenerationError

AvroType = str | dict[str, Any] | list[Any]
_NONE_TYPE = type(None)
_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_INVALID_NAME_CHAR_RE = re.compile(r"[^A-Za-z0-9_]")


def generate_avro_schema(model_cls: type[Any]) -> dict[str, Any]:
    generator = SchemaGenerator()
    schema = generator.model_schema(model_cls, path=model_cls.__name__)
    if not isinstance(schema, dict):  # pragma: no cover - root models always emit first
        raise AvroSchemaGenerationError("Root Avro schema must be a record")
    try:
        parse_schema(copy.deepcopy(schema))
    except AvroSchemaGenerationError:
        raise
    except Exception as exc:
        raise AvroSchemaGenerationError(
            f"Generated Avro schema for {model_cls.__name__} is invalid"
        ) from exc
    return schema


@dataclass(frozen=True)
class PythonNamedType:
    type_: type[Any]


@dataclass(frozen=True)
class LiteralEnumNamedType:
    symbols: tuple[str, ...]


@dataclass(frozen=True)
class LiteralEnumSpec:
    full_name: str
    name: str
    namespace: str
    symbols: tuple[str, ...]


NamedTypeOwner = PythonNamedType | LiteralEnumNamedType


@dataclass
class SchemaGenerator:
    named_types: dict[str, NamedTypeOwner] = field(default_factory=dict)
    emitted_names: set[str] = field(default_factory=set)
    visiting: set[type[Any]] = field(default_factory=set)

    def model_schema(self, model_cls: type[Any], *, path: str) -> AvroType:
        self._ensure_avro_model(model_cls, path)
        name, namespace, full_name = record_names(model_cls)
        self._claim_name(full_name, model_cls, path)

        if model_cls in self.visiting:
            raise AvroSchemaGenerationError(
                f"Recursive Avro model reference at field '{path}' is not supported in v0"
            )
        if full_name in self.emitted_names:
            return full_name

        self.emitted_names.add(full_name)
        self.visiting.add(model_cls)
        try:
            schema: dict[str, Any] = {
                "type": "record",
                "name": name,
            }
            if namespace:
                schema["namespace"] = namespace
            doc = own_doc(model_cls)
            if doc:
                schema["doc"] = doc
            schema["fields"] = [
                self.field_schema(
                    field_name,
                    field_info,
                    record_name=name,
                    record_namespace=namespace,
                )
                for field_name, field_info in model_cls.model_fields.items()
            ]
            return schema
        finally:
            self.visiting.remove(model_cls)

    def field_schema(
        self,
        python_name: str,
        field_info: Any,
        *,
        record_name: str,
        record_namespace: str,
    ) -> dict[str, Any]:
        avro_name = avro_field_name(python_name, field_info)
        default = avro_field_default(field_info, path=avro_name)
        avro_type = self.avro_type(
            field_info.annotation,
            path=avro_name,
            default=default,
            literal_enum_name=f"{record_name}_{avro_name}_Enum",
            literal_enum_namespace=record_namespace,
        )
        result: dict[str, Any] = {"name": avro_name, "type": avro_type}

        description = getattr(field_info, "description", None)
        if description:
            result["doc"] = description
        if default is not PydanticUndefined:
            result["default"] = self.avro_default(
                field_info.annotation, default, path=avro_name
            )
        return result

    def avro_type(
        self,
        annotation: Any,
        *,
        path: str,
        default: Any = PydanticUndefined,
        literal_enum_name: str | None = None,
        literal_enum_namespace: str = "",
    ) -> AvroType:
        annotation = unwrap_annotated(annotation)
        origin = get_origin(annotation)

        if annotation is _NONE_TYPE or annotation is None:
            return "null"
        if annotation is bool:
            return "boolean"
        if annotation is int:
            return "long"
        if annotation is float:
            return "double"
        if annotation is str:
            return "string"
        if annotation is bytes:
            return "bytes"

        if origin is Literal:
            return self.literal_enum_schema(
                annotation,
                path=path,
                name=literal_enum_name,
                namespace=literal_enum_namespace,
            )
        if origin in (Union, types.UnionType):
            return self.union_type(
                annotation,
                path=path,
                default=default,
                literal_enum_name=literal_enum_name,
                literal_enum_namespace=literal_enum_namespace,
            )
        if origin is list:
            (item_type,) = self.single_type_arg(annotation, path=path, container="list")
            return {
                "type": "array",
                "items": self.avro_type(item_type, path=f"{path}[]"),
            }
        if origin is dict:
            key_type, value_type = self.type_args(annotation, path=path, container="dict", count=2)
            if key_type is not str:
                raise AvroSchemaGenerationError(
                    f"Field '{path}' uses a map with non-string keys, which Avro does not support"
                )
            return {
                "type": "map",
                "values": self.avro_type(value_type, path=f"{path}{{}}"),
            }

        if inspect.isclass(annotation) and issubclass(annotation, Enum):
            return self.enum_schema(annotation, path=path)
        if inspect.isclass(annotation) and is_avro_model(annotation):
            return self.model_schema(annotation, path=path)

        if annotation is Any:
            detail = "typing.Any"
        else:
            detail = getattr(annotation, "__qualname__", repr(annotation))
        raise AvroSchemaGenerationError(
            f"Unsupported Avro type for field '{path}': {detail} is not supported in v0"
        )

    def union_type(
        self,
        annotation: Any,
        *,
        path: str,
        default: Any,
        literal_enum_name: str | None,
        literal_enum_namespace: str,
    ) -> list[Any]:
        args = tuple(unwrap_annotated(arg) for arg in get_args(annotation))
        non_null = [arg for arg in args if arg is not _NONE_TYPE]
        has_null = len(non_null) != len(args)
        if not has_null or len(non_null) != 1:
            raise AvroSchemaGenerationError(
                f"Field '{path}' uses an unsupported union; only nullable T | None is supported in v0"
            )
        avro_non_null = self.avro_type(
            non_null[0],
            path=path,
            literal_enum_name=literal_enum_name,
            literal_enum_namespace=literal_enum_namespace,
        )
        if default is not PydanticUndefined and default is not None:
            return [avro_non_null, "null"]
        return ["null", avro_non_null]

    def literal_enum_schema(
        self, annotation: Any, *, path: str, name: str | None, namespace: str
    ) -> AvroType:
        if name is None:
            raise AvroSchemaGenerationError(
                f"Field '{path}' uses Literal inside a container, which is not supported in v0"
            )
        spec = parse_literal_enum(
            annotation,
            enum_name=name,
            namespace=namespace,
            path=path,
        )
        self._claim_literal_enum(spec, path)
        if spec.full_name in self.emitted_names:
            return spec.full_name

        self.emitted_names.add(spec.full_name)
        schema: dict[str, Any] = {
            "type": "enum",
            "name": spec.name,
            "symbols": list(spec.symbols),
        }
        if spec.namespace:
            schema["namespace"] = spec.namespace
        return schema

    def enum_schema(self, enum_cls: type[Enum], *, path: str) -> AvroType:
        name = enum_cls.__name__
        validate_avro_name(name, f"Enum name for field '{path}'")
        namespace = sanitize_module(enum_cls.__module__)
        full_name = combine_full_name(namespace, name)
        self._claim_name(full_name, enum_cls, path)
        if full_name in self.emitted_names:
            return full_name

        self.emitted_names.add(full_name)
        symbols = enum_symbols(enum_cls, path=path)
        schema: dict[str, Any] = {"type": "enum", "name": name, "symbols": symbols}
        if namespace:
            schema["namespace"] = namespace
        return schema

    def avro_default(self, annotation: Any, default: Any, *, path: str) -> Any:
        annotation = unwrap_annotated(annotation)
        origin = get_origin(annotation)
        if origin in (Union, types.UnionType):
            if default is None:
                return None
            non_null = [
                arg
                for arg in get_args(annotation)
                if unwrap_annotated(arg) is not _NONE_TYPE
            ]
            if len(non_null) != 1:
                raise AvroSchemaGenerationError(
                    f"Field '{path}' has an unsupported Avro default value in v0"
                )
            return self.avro_default(non_null[0], default, path=path)
        if origin is list:
            if not isinstance(default, list):
                raise AvroSchemaGenerationError(
                    f"Field '{path}' has an unsupported Avro default value in v0"
                )
            (item_type,) = self.single_type_arg(annotation, path=path, container="list")
            return [
                self.avro_default(item_type, item, path=f"{path}[]")
                for item in default
            ]
        if origin is dict:
            if not isinstance(default, dict):
                raise AvroSchemaGenerationError(
                    f"Field '{path}' has an unsupported Avro default value in v0"
                )
            key_type, value_type = self.type_args(
                annotation, path=path, container="dict", count=2
            )
            if key_type is not str or any(not isinstance(key, str) for key in default):
                raise AvroSchemaGenerationError(
                    f"Field '{path}' has a map default with non-string keys, which Avro does not support"
                )
            return {
                key: self.avro_default(value_type, value, path=f"{path}{{}}")
                for key, value in default.items()
            }
        if isinstance(default, Enum):
            return self.enum_symbol(default, path=path)
        if default is None or isinstance(default, bool | int | float | str):
            return default
        raise AvroSchemaGenerationError(
            f"Field '{path}' has an unsupported Avro default value in v0"
        )

    def enum_symbol(self, value: Enum, *, path: str) -> str:
        symbols = enum_symbols(type(value), path=path)
        symbol = enum_value_symbol(value) if enum_values_are_symbols(type(value)) else value.name
        if symbol not in symbols:
            raise AvroSchemaGenerationError(
                f"Field '{path}' has an enum default that is not an Avro symbol"
            )
        return symbol

    def single_type_arg(self, annotation: Any, *, path: str, container: str) -> tuple[Any]:
        args = get_args(annotation)
        if len(args) != 1:
            raise AvroSchemaGenerationError(
                f"Field '{path}' uses an unparameterized {container}, which is not supported in v0"
            )
        return args

    def type_args(
        self, annotation: Any, *, path: str, container: str, count: int
    ) -> tuple[Any, ...]:
        args = get_args(annotation)
        if len(args) != count:
            raise AvroSchemaGenerationError(
                f"Field '{path}' uses an unparameterized {container}, which is not supported in v0"
            )
        return args

    def _claim_name(self, full_name: str, type_: type[Any], path: str) -> None:
        owner = PythonNamedType(type_)
        existing = self.named_types.get(full_name)
        if existing is not None and existing != owner:
            raise AvroSchemaGenerationError(
                f"Field '{path}' reuses Avro name '{full_name}' for multiple types"
            )
        self.named_types[full_name] = owner

    def _claim_literal_enum(self, spec: LiteralEnumSpec, path: str) -> None:
        owner = LiteralEnumNamedType(spec.symbols)
        existing = self.named_types.get(spec.full_name)
        if existing is not None and existing != owner:
            raise AvroSchemaGenerationError(
                f"Field '{path}' reuses Avro name '{spec.full_name}' for multiple types"
            )
        self.named_types[spec.full_name] = owner

    def _ensure_avro_model(self, model_cls: type[Any], path: str) -> None:
        if not is_avro_model(model_cls):
            raise AvroSchemaGenerationError(
                f"Field '{path}' uses a Pydantic model that does not inherit AvroBaseModel"
            )


def avro_field_default(field_info: Any, *, path: str) -> Any:
    if field_info.default_factory is None:
        return PydanticUndefined if field_info.is_required() else field_info.default
    if field_info.default_factory is list:
        return []
    if field_info.default_factory is dict:
        return {}
    raise AvroSchemaGenerationError(
        f"Unsupported default_factory for field '{path}'; "
        "only built-in list and dict are supported in v0"
    )


def avro_field_name(python_name: str, field_info: Any) -> str:
    name = field_info.serialization_alias or field_info.alias or python_name
    if not isinstance(name, str):
        raise AvroSchemaGenerationError(
            f"Field '{python_name}' has a non-string alias, which Avro does not support"
        )
    validate_avro_name(name, f"Avro field name for field '{python_name}'")
    return name


def record_names(model_cls: type[Any]) -> tuple[str, str, str]:
    raw_name = model_cls.model_config.get("avro_name") or model_cls.__name__
    raw_namespace = model_cls.model_config.get("avro_namespace") or sanitize_module(
        model_cls.__module__
    )
    name = sanitize_name(raw_name)
    namespace = sanitize_namespace(raw_namespace)
    return name, namespace, combine_full_name(namespace, name)


def sanitize_module(module: str) -> str:
    if module == "__main__":
        return "main"
    return sanitize_namespace(module)


def sanitize_namespace(namespace: str) -> str:
    return ".".join(sanitize_name(part) for part in namespace.split(".") if part)


def sanitize_name(name: str) -> str:
    sanitized = _INVALID_NAME_CHAR_RE.sub("_", name)
    if not sanitized:
        return "_"
    if sanitized[0].isdigit():
        sanitized = f"_{sanitized}"
    return sanitized


def validate_avro_name(name: str, context: str) -> None:
    if not _NAME_RE.match(name):
        raise AvroSchemaGenerationError(f"{context} '{name}' is not a valid Avro name")


def combine_full_name(namespace: str, name: str) -> str:
    return f"{namespace}.{name}" if namespace else name


def parse_literal_enum(
    annotation: Any, *, enum_name: str, namespace: str, path: str
) -> LiteralEnumSpec:
    validate_avro_name(enum_name, f"Literal enum name for field '{path}'")
    symbols = dedupe_literal_symbols(get_args(annotation), path=path)
    if not symbols:
        raise AvroSchemaGenerationError(
            f"Field '{path}' uses an empty Literal, which is not supported in v0"
        )
    for symbol in symbols:
        validate_avro_name(symbol, f"Literal enum symbol for field '{path}'")
    return LiteralEnumSpec(
        full_name=combine_full_name(namespace, enum_name),
        name=enum_name,
        namespace=namespace,
        symbols=tuple(symbols),
    )


def dedupe_literal_symbols(values: tuple[Any, ...], *, path: str) -> list[str]:
    symbols: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise AvroSchemaGenerationError(
                f"Field '{path}' uses a non-string Literal value, which is not supported in v0"
            )
        if value not in seen:
            symbols.append(value)
            seen.add(value)
    return symbols


def own_doc(model_cls: type[Any]) -> str | None:
    if model_cls.__doc__ is None:
        return None
    return inspect.getdoc(model_cls)


def unwrap_annotated(annotation: Any) -> Any:
    while get_origin(annotation) is Annotated:
        annotation = get_args(annotation)[0]
    return annotation


def is_avro_model(type_: type[Any]) -> bool:
    return any(
        base.__module__ == "pydantic_avro.base" and base.__name__ == "AvroBaseModel"
        for base in type_.__mro__
    )


def enum_values_are_symbols(enum_cls: type[Enum]) -> bool:
    return all(isinstance(member.value, str) and _NAME_RE.match(member.value) for member in enum_cls)


def enum_value_symbol(value: Enum) -> str:
    if not isinstance(value.value, str):
        return value.name
    return value.value


def enum_symbols(enum_cls: type[Enum], *, path: str) -> list[str]:
    if enum_values_are_symbols(enum_cls):
        symbols = [str(member.value) for member in enum_cls]
    else:
        symbols = [member.name for member in enum_cls]
    for symbol in symbols:
        validate_avro_name(symbol, f"Enum symbol for field '{path}'")
    return symbols
