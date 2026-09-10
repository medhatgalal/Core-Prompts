#!/usr/bin/env python3
"""Generate a deterministic installer capsule accepted by historical updaters.

Canonical Python sources remain in scripts/core_install. The existing allowed
deploy-profile.py path carries their compressed bytes, avoiding changes to old
updater allowlists. Runtime imports stay in memory and never extract files.
"""
from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import json
from pathlib import Path
import re
import textwrap
import zlib

RUNTIME = '''\
#!/usr/bin/env python3
"""Generated portable installer. Edit scripts/core_install; regenerate with
python3 scripts/build-install-runtime.py. Historical profile APIs are preserved.
"""
import base64 as _capsule_base64
import importlib.abc as _capsule_abc
import importlib.util as _capsule_util
import importlib as _capsule_importlib
import json as _capsule_json
import sys as _capsule_sys
import uuid as _capsule_uuid
import zlib as _capsule_zlib

_CAPSULE_SOURCE_SHA256 = "@@DIGEST@@"
_CAPSULE_PAYLOAD = (
@@PAYLOAD@@
)
_capsule_sources = _capsule_json.loads(_capsule_zlib.decompress(
    _capsule_base64.b85decode(_CAPSULE_PAYLOAD)))
# Fresh namespace for EVERY loaded capsule, including identical versions. Do
# not import disk core_install or reuse an older capsule's cached module state.
_capsule_namespace = "_core_prompts_install_" + _capsule_uuid.uuid4().hex


class _CapsuleImporter(_capsule_abc.MetaPathFinder, _capsule_abc.Loader):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == _capsule_namespace:
            return _capsule_util.spec_from_loader(fullname, self, is_package=True)
        if fullname.startswith(_capsule_namespace + "."):
            short = fullname[len(_capsule_namespace) + 1:]
            if short in _capsule_sources:
                return _capsule_util.spec_from_loader(fullname, self)
        return None

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        key = "__init__" if module.__name__ == _capsule_namespace else module.__name__[len(_capsule_namespace) + 1:]
        module.__file__ = __file__
        if key == "__init__":
            module.__path__ = []
        exec(compile(_capsule_sources[key], __file__ + "::" + key, "exec"), module.__dict__)


_capsule_sys.meta_path.insert(0, _CapsuleImporter())


def _capsule_module(name):
    return _capsule_importlib.import_module(_capsule_namespace + "." + name)


# Execute the legacy body in THIS module's globals: callers can still patch
# snapshot/atomic_write, and __file__ retains the deployed script location.
exec(compile(_capsule_sources["profile_v1"], __file__, "exec"), globals())


def installation_plan(repo, target, request):
    return _capsule_module("planner").plan(repo, target, request)


def installation_apply(repo, target, approved, replan):
    return _capsule_module("transaction").apply(repo, target, approved, replan)


def installation_rollback(target, tx, dry_run=False):
    return _capsule_module("transaction").rollback(target, tx, dry_run=dry_run)


def installation_cli(argv):
    return _capsule_module("cli").main(argv)


if __name__ == "__main__":
    if "--install" in _capsule_sys.argv[1:]:
        _capsule_args = list(_capsule_sys.argv[1:])
        _capsule_args.remove("--install")
        raise SystemExit(installation_cli(_capsule_args))
    raise SystemExit(main())
'''


def sources(repo: Path) -> dict[str, str]:
    root = repo / "scripts/core_install"
    found = {}
    for path in sorted(root.glob("*.py")):
        if path.is_symlink() or not re.fullmatch(r"[a-z_][a-z_0-9]*", path.stem):
            raise ValueError(f"unsupported capsule source: {path}")
        found[path.stem] = path.read_text()
    if not {"__init__", "profile_v1"} <= found.keys():
        raise ValueError("capsule requires __init__.py and profile_v1.py")
    return found


def legacy_body(source: str) -> str:
    """Omit only the module's terminal main guard; its functions are unchanged."""
    parsed = ast.parse(source)
    if not parsed.body:
        return source
    last = parsed.body[-1]
    if isinstance(last, ast.If) and ast.dump(last.test) == ast.dump(ast.parse("__name__ == '__main__'", mode="eval").body):
        if last.orelse or ast.dump(last.body[0]) != ast.dump(ast.parse("raise SystemExit(main())").body[0]) or len(last.body) != 1:
            raise ValueError("unsupported legacy main guard")
        return "".join(source.splitlines(keepends=True)[:last.lineno - 1])
    return source


def render(modules: dict[str, str]) -> str:
    embedded = dict(modules)
    embedded["profile_v1"] = legacy_body(embedded["profile_v1"])
    for name, source in embedded.items():
        compile(source, name + ".py", "exec")
    raw = json.dumps(embedded, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    payload = base64.b85encode(zlib.compress(raw, level=9)).decode()
    literals = "\n".join("    " + repr(line) for line in textwrap.wrap(payload, width=100, break_on_hyphens=False))
    return RUNTIME.replace("@@DIGEST@@", hashlib.sha256(raw).hexdigest()).replace("@@PAYLOAD@@", literals)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = args.repo / "scripts/deploy-profile.py"
    rendered = render(sources(args.repo))
    if args.check:
        if output.read_text() != rendered:
            raise SystemExit("installer capsule is stale; run scripts/build-install-runtime.py")
    else:
        output.write_text(rendered)
    print("installer capsule: " + ("verified" if args.check else "generated"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
