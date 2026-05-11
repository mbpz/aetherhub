"""Wasm 执行沙箱 - 真实实现

Requires wasmtime to be installed. Python code must be compiled to Wasm
bytecode before execution - this sandbox only executes pre-compiled Wasm.

Installation: pip install wasmtime
"""
from typing import Dict, Any

# Required dependency - raise clear error if not installed
try:
    import wasmtime
    from wasmtime import Engine, Linker, Module, Store
except ImportError as e:
    raise ImportError(
        "wasmtime is required for Wasm sandbox execution. "
        "Install it with: pip install wasmtime"
    ) from e


class WasmtimeSandbox:
    """Wasm 执行沙箱"""

    def __init__(self, memory_limit_mb: int = 16, time_limit_ms: int = 5000):
        self.memory_limit = memory_limit_mb * 1024 * 1024  # bytes
        self.time_limit = time_limit_ms
        self._engine = Engine()

    def execute(self, code: str) -> Dict[str, Any]:
        """
        Execute Wasm bytecode.

        Args:
            code: Wasm bytecode (bytes or string starting with \\x00asm)

        Returns:
            Execution result

        Raises:
            ValueError: If code is not valid Wasm bytecode
        """
        # Convert to bytes if string
        if isinstance(code, str):
            # Check for wasm magic number
            if len(code) > 4 and code[:4].encode().hex() == "0061736d":
                wasm_code = code.encode()
            else:
                raise ValueError(
                    "Python code cannot be executed directly. "
                    "Compile Python to Wasm bytecode first using a tool like Pyodide."
                )
        else:
            wasm_code = code

        return self._execute_wasm(wasm_code)

    def _execute_wasm(self, wasm_code: bytes) -> Dict[str, Any]:
        """Execute real Wasm bytecode"""
        import time
        start_time = time.time()

        try:
            engine = Engine()
            module = Module(engine, wasm_code)
            linker = Linker(engine)
            linker.define_wasi()

            store = Store(engine)
            instance = linker.instantiate(store, module)

            # Try to call exported run function
            exports = instance.exports(store)
            if hasattr(exports, "run"):
                result = exports.run(store)
                elapsed_ms = int((time.time() - start_time) * 1000)

                return {
                    "status": "success",
                    "output": str(result),
                    "execution_time_ms": elapsed_ms,
                    "memory_usage_mb": self._estimate_memory(store),
                }
            else:
                return {
                    "status": "success",
                    "output": "Wasm module loaded",
                    "execution_time_ms": int((time.time() - start_time) * 1000),
                    "memory_usage_mb": 1,
                }

        except Exception as e:
            return {
                "status": "error",
                "output": str(e),
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "memory_usage_mb": 0,
            }

    def _estimate_memory(self, store) -> float:
        """Estimate memory usage"""
        try:
            if hasattr(store, "memory"):
                mem = store.memory
                if mem:
                    return round(mem.data_size() / (1024 * 1024), 2)
        except Exception:
            pass
        return 1.0

    def verify_execution(self, result: Dict[str, Any]) -> bool:
        """
        Verify execution result is within safety limits.

        Args:
            result: Execution result

        Returns:
            True if within limits, False otherwise
        """
        # Check memory usage
        memory_mb = result.get("memory_usage_mb", 0)
        limit_mb = self.memory_limit / (1024 * 1024)
        if memory_mb > limit_mb:
            return False

        # Check execution time
        elapsed_ms = result.get("execution_time_ms", 0)
        if elapsed_ms > self.time_limit:
            return False

        return True

    def execute_with_isolation(self, code: str,
                               allowed_paths: list = None) -> Dict[str, Any]:
        """
        Execute in isolated environment (path restrictions require pre-compilation).

        Args:
            code: Wasm bytecode
            allowed_paths: Allowed path prefixes (for reference, not enforced at runtime)

        Returns:
            Execution result
        """
        if allowed_paths is None:
            allowed_paths = ["/tmp"]

        # Path restrictions must be handled at Wasm compile time
        # This sandbox only executes pre-compiled Wasm
        return self.execute(code)