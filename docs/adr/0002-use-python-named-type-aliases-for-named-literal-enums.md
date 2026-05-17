# Use Python named type aliases for named Literal Enums

Status: Accepted

When a string `Literal[...]` needs a stable Avro enum name, users should write a Python named type alias such as `type OpType = Literal["A", "B"]`. The declared alias name becomes the Avro enum name in the containing record namespace; plain assignment aliases like `OpType = Literal[...]` remain anonymous field-local Literal Enums because their binding name is not reliably available at runtime.

Named Literal Enums may be reused directly, through nullable fields, and inside containers; repeated uses emit the Avro enum once and then reference it by full name. Import aliases do not rename the Avro enum, outer named aliases win for explicit renames, generic aliases are deferred, and colliding Avro full names with different symbols are hard schema errors rather than auto-disambiguated.

An `Annotated` escape hatch for explicit enum namespace/name overrides is deferred until there is real demand; for now the containing record namespace keeps schemas aligned with existing Avro record naming rather than leaking Python module layout into wire schema names.
