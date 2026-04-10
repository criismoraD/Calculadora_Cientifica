## 2025-02-14 - RCE via Insecure `eval()`
**Vulnerability:** Arbitrary Code Execution (RCE) via Python's `eval()` in `_calcular_resultado`.
**Learning:** Even though `eval` was sandboxed with `{"__builtins__": {}}` and a specific execution context, standard Python AST allows attribute and object introspection (e.g., `__class__`, `__subclasses__`). An attacker could inject a payload escaping the sandbox using these properties.
**Prevention:** Implement strict AST-based validation checking whitelist of allowed `ast` node types (preventing `Attribute` nodes) and limiting variable names to the explicitly whitelisted evaluation context *before* evaluating the expression.
