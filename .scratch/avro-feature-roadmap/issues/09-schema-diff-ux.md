# Schema diff UX

Status: needs-triage

## What to build

Add a human-readable schema diff/report that explains meaningful Avro schema changes and highlights compatibility-impacting changes.

## Acceptance criteria

- [ ] Diff output identifies added, removed, renamed, and type-changed fields.
- [ ] Diff output identifies enum symbol additions/removals and default changes.
- [ ] Compatibility checker findings can be rendered as actionable text.
- [ ] CLI or public function output is stable enough for review/CI logs.
- [ ] Tests cover both compatible and breaking schema changes.

## Blocked by

- `.scratch/avro-feature-roadmap/issues/03-schema-compatibility-checker.md`
