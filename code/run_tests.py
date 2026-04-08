#!/usr/bin/env python3
"""
Nexora Test Runner
==================
Runs all tests using Python's built-in importlib + inspect.
Works without pytest installed, supports fixture-of-fixture dependencies,
tmp_path, monkeypatch, and pytest.importorskip.
"""

import importlib
import importlib.util
import inspect
import os
import pathlib
import sys
import tempfile
import time
import traceback
import unittest
from typing import Any, Dict, List, Tuple

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

# ─────────────────────────────────────────────────────────
# pytest shim
# ─────────────────────────────────────────────────────────
_NOTSET = object()


class _ImportSkip(unittest.SkipTest):
    pass


def _importorskip(modname, reason=None, minversion=None):
    try:
        return importlib.import_module(modname)
    except ImportError:
        msg = reason or f"{modname} not installed"
        raise _ImportSkip(msg)


class _RaisesCtx:
    def __init__(self, exc_type, *extra):
        self.exc_type = exc_type
        self.value = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, tb):
        if exc_type is None:
            raise AssertionError(
                f"Expected {self.exc_type.__name__} but no exception raised"
            )
        if not issubclass(exc_type, self.exc_type):
            return False
        self.value = exc_val
        return True


class _FixtureDecorator:
    """@pytest.fixture shim that simply tags the function."""

    def __call__(self, fn=None, *, scope="function", params=None, autouse=False):
        if fn is None:
            # called as @pytest.fixture(scope=...)
            def wrapper(f):
                f._is_fixture = True
                return f

            return wrapper
        fn._is_fixture = True
        return fn

    def __init__(self):
        pass


class _Mark:
    @staticmethod
    def parametrize(*a, **kw):
        def d(f):
            return f

        return d

    @staticmethod
    def skip(reason=""):
        def d(f):
            f._skip_reason = reason
            return f

        return d

    @staticmethod
    def xfail(reason="", strict=False):
        def d(f):
            return f

        return d

    @staticmethod
    def skipif(condition, reason=""):
        def d(f):
            if condition:
                f._skip_reason = reason
            return f

        return d


class _PytestShim:
    fixture = _FixtureDecorator()
    mark = _Mark()
    SkipTest = unittest.SkipTest
    raises = _RaisesCtx
    importorskip = staticmethod(_importorskip)

    @staticmethod
    def skip(reason=""):
        raise unittest.SkipTest(reason)

    @staticmethod
    def fail(msg=""):
        raise AssertionError(msg)


sys.modules.setdefault("pytest", _PytestShim())  # type: ignore


# ─────────────────────────────────────────────────────────
# Monkeypatch fixture
# ─────────────────────────────────────────────────────────
class _MonkeyPatch:
    def __init__(self):
        self._patches: list = []

    def setattr(self, obj_or_target, name=_NOTSET, value=_NOTSET, raising=True):
        if name is _NOTSET:
            # setattr("module.attr", value) form
            parts = obj_or_target.rsplit(".", 1)
            mod = importlib.import_module(parts[0])
            name = parts[1]
            obj_or_target = mod
        old = getattr(obj_or_target, name, _NOTSET)
        if old is _NOTSET and raising:
            raise AttributeError(f"{obj_or_target!r} has no attribute {name!r}")
        setattr(obj_or_target, name, value)
        self._patches.append((obj_or_target, name, old))

    def chdir(self, path):
        old = os.getcwd()
        os.chdir(path)
        self._patches.append(("_chdir", old))

    def undo(self):
        for patch in reversed(self._patches):
            if patch[0] == "_chdir":
                try:
                    os.chdir(patch[1])
                except Exception:
                    pass
            else:
                obj, name, old = patch
                if old is _NOTSET:
                    try:
                        delattr(obj, name)
                    except AttributeError:
                        pass
                else:
                    setattr(obj, name, old)


# ─────────────────────────────────────────────────────────
# Fixture resolver
# ─────────────────────────────────────────────────────────
def _resolve_fixture(name: str, registry: Dict[str, Any], cache: Dict[str, Any]) -> Any:
    """Recursively resolve a fixture, caching results within one test."""
    if name in cache:
        return cache[name]

    if name == "tmp_path":
        val = pathlib.Path(tempfile.mkdtemp())
        cache[name] = val
        return val

    if name == "monkeypatch":
        val = _MonkeyPatch()
        cache[name] = val
        return val

    if name not in registry:
        raise RuntimeError(f"Unknown fixture: '{name}'")

    fixture_fn = registry[name]
    sig = inspect.signature(fixture_fn)
    kwargs = {}
    for param in sig.parameters.values():
        if param.name == "self":
            continue
        kwargs[param.name] = _resolve_fixture(param.name, registry, cache)

    val = fixture_fn(**kwargs)
    cache[name] = val
    return val


def _resolve_test_args(test_fn, registry: Dict[str, Any]) -> Dict[str, Any]:
    sig = inspect.signature(test_fn)
    cache: Dict[str, Any] = {}
    args = {}
    for param in sig.parameters.values():
        if param.name == "self":
            continue
        args[param.name] = _resolve_fixture(param.name, registry, cache)
    return args, cache


# ─────────────────────────────────────────────────────────
# Module runner
# ─────────────────────────────────────────────────────────
def _collect_fixtures(mod) -> Dict[str, Any]:
    registry = {}
    for name, obj in inspect.getmembers(mod, predicate=callable):
        if getattr(obj, "_is_fixture", False):
            registry[name] = obj
    return registry


def _run_module(modname: str, filepath: str) -> Tuple[int, int, int, List[str]]:
    passed = failed = skipped = 0
    errors: List[str] = []

    spec = importlib.util.spec_from_file_location(modname, filepath)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except (unittest.SkipTest, _ImportSkip) as e:
        print(f"  SKIP (module) — {e}")
        return 0, 0, 1, []
    except Exception as e:
        print(f"  LOAD ERROR: {e}")
        return 0, 1, 0, [f"ERROR loading {modname}:\n{traceback.format_exc()}"]

    # Collect fixtures from module + conftest
    registry = {}
    for conf_path in [
        os.path.join(ROOT, "tests", "conftest.py"),
        os.path.join(os.path.dirname(filepath), "conftest.py"),
    ]:
        if os.path.exists(conf_path):
            try:
                conf_spec = importlib.util.spec_from_file_location(
                    f"conftest_{os.path.dirname(filepath)}", conf_path
                )
                conf_mod = importlib.util.module_from_spec(conf_spec)
                conf_spec.loader.exec_module(conf_mod)
                registry.update(_collect_fixtures(conf_mod))
            except Exception:
                pass
    registry.update(_collect_fixtures(mod))

    # Collect test functions
    test_fns = [
        (name, obj)
        for name, obj in inspect.getmembers(mod, predicate=inspect.isfunction)
        if name.startswith("test_")
    ]

    for test_name, test_fn in test_fns:
        sys.stdout.write(f"    {test_name} ... ")
        sys.stdout.flush()

        skip_reason = getattr(test_fn, "_skip_reason", None)
        if skip_reason is not None:
            print(f"SKIP ({skip_reason})")
            skipped += 1
            continue

        mp = None
        try:
            args, cache = _resolve_test_args(test_fn, registry)
            mp = cache.get("monkeypatch")
            test_fn(**args)
            print("PASS")
            passed += 1
        except (unittest.SkipTest, _ImportSkip) as e:
            print(f"SKIP ({e})")
            skipped += 1
        except AssertionError as e:
            tb = traceback.format_exc()
            print(f"FAIL — {str(e) or '(assertion failed)'}")
            failed += 1
            errors.append(f"FAIL {modname}::{test_name}\n{tb}")
        except Exception as e:
            tb = traceback.format_exc()
            print(f"ERROR — {type(e).__name__}: {e}")
            failed += 1
            errors.append(f"ERROR {modname}::{test_name}\n{tb}")
        finally:
            if mp is not None:
                try:
                    mp.undo()
                except Exception:
                    pass

    return passed, failed, skipped, errors


# ─────────────────────────────────────────────────────────
# Test discovery
# ─────────────────────────────────────────────────────────
def _collect_test_modules() -> List[Tuple[str, str]]:
    test_specs = [
        ("tests.compliance.test_phi_audit", "tests/compliance/test_phi_audit.py"),
        (
            "tests.monitoring.test_adverse_event_reporting",
            "tests/monitoring/test_adverse_event_reporting.py",
        ),
        (
            "tests.clinical_tests.test_data_validation",
            "tests/clinical_tests/test_data_validation.py",
        ),
        (
            "tests.clinical_tests.test_fhir_ingest",
            "tests/clinical_tests/test_fhir_ingest.py",
        ),
        (
            "tests.data_pipeline.test_clinical_etl",
            "tests/data_pipeline/test_clinical_etl.py",
        ),
        (
            "tests.model_factory.test_model_registry",
            "tests/model_factory/test_model_registry.py",
        ),
        ("tests.model_tests.test_calibration", "tests/model_tests/test_calibration.py"),
        (
            "tests.model_tests.test_predictive_equality",
            "tests/model_tests/test_predictive_equality.py",
        ),
        ("tests.api.test_rest_api", "tests/api/test_rest_api.py"),
    ]
    return [
        (mn, os.path.join(ROOT, fp))
        for mn, fp in test_specs
        if os.path.exists(os.path.join(ROOT, fp))
    ]


# ─────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("Nexora Test Suite")
    print("=" * 70)

    modules = _collect_test_modules()
    total_p = total_f = total_s = 0
    all_errors: List[str] = []
    t0 = time.time()

    for modname, filepath in modules:
        relpath = os.path.relpath(filepath, ROOT)
        print(f"\n{relpath}")
        p, f, s, errs = _run_module(modname, filepath)
        total_p += p
        total_f += f
        total_s += s
        all_errors.extend(errs)

    elapsed = time.time() - t0
    print("\n" + "=" * 70)
    if all_errors:
        print("\nFAILURES / ERRORS DETAIL:")
        for err in all_errors:
            print(err)
        print("=" * 70)

    status = "PASSED" if total_f == 0 else "FAILED"
    print(
        f"\n{status} — {total_p} passed, {total_f} failed, "
        f"{total_s} skipped in {elapsed:.2f}s"
    )
    return 0 if total_f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
