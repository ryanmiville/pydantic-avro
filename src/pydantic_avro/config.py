from pydantic import ConfigDict


class AvroConfigDict(ConfigDict, total=False):
    """Pydantic config with Avro-specific model settings."""

    avro_name: str
    avro_namespace: str
