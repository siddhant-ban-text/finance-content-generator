# Foundation runtime compatibility

Task 1 tested runtime: CPython 3.12.15 on macOS arm64. Initially supported Python
range: >=3.12,<3.13. Wider support is deliberately not asserted. uv.lock fixes exact
resolved packages/hashes; .python-version pins the exercised interpreter.

Primary documentation consulted 2026-11-10:
- [uv Python selection](https://docs.astral.sh/uv/concepts/python-versions/)
- [uv locking/sync](https://docs.astral.sh/uv/concepts/projects/sync/)
- [Pydantic strict validation](https://docs.pydantic.dev/latest/concepts/strict_mode/)
- [Pydantic serialization](https://docs.pydantic.dev/latest/concepts/serialization/)

Resolved initial dependencies: Pydantic 2.14.3, pydantic-core 2.50.4, pytest 9.2.0.
Strict Python validation forbids coercion; the explicit JSON boundary allows typed
UUID/date parsing and decimal strings. Extra fields and incompatible schema
versions are rejected. Do not serialize arbitrary provider responses into these
contracts. Phoenix/OTel/OAuth dependencies are not installed by Task 1.
