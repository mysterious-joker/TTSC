"""Collect runtime states without translating or modifying corpus expectations."""

import argparse
import dataclasses
import enum
import hashlib
import json
from pathlib import Path
import sys
import traceback


def json_default(value):
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    if isinstance(value, enum.Enum):
        return value.value
    raise TypeError(f"Unsupported state value: {type(value).__name__}")


parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True)
parser.add_argument("--label", required=True)
parser.add_argument("--corpus", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()
root = Path(args.root).resolve()
sys.path.insert(0, str(root))

import conversational_search.intent as intent

module_path = Path(intent.__file__).resolve()
assert module_path == root / "conversational_search" / "intent.py", module_path
corpus_bytes = Path(args.corpus).read_bytes()
corpus = json.loads(corpus_bytes)
result = {
    "version": "1.0-runtime-state-collection",
    "label": args.label,
    "runtime_root": str(root),
    "interpreter": sys.executable,
    "module_path": str(module_path),
    "module_sha256": hashlib.sha256(module_path.read_bytes()).hexdigest(),
    "corpus_sha256": hashlib.sha256(corpus_bytes).hexdigest(),
    "method": "Fresh IntentState per case; apply_user_message with successive messages and one-based turns; default parsing policy; no question context injected.",
    "cases": [],
}
for case in corpus["cases"]:
    state = intent.IntentState()
    collected = {"id": case["id"], "initial_state": dataclasses.asdict(state), "turns": [], "error": None}
    for turn, message in enumerate(case["messages"], 1):
        try:
            state = intent.apply_user_message(state, message, turn)
            collected["turns"].append({"turn": turn, "message": message, "state": dataclasses.asdict(state)})
        except Exception as exc:
            collected["error"] = {"turn": turn, "type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
            break
    collected["final_state"] = dataclasses.asdict(state)
    result["cases"].append(collected)
Path(args.output).write_text(json.dumps(result, default=json_default, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"label": args.label, "output": args.output, "cases": len(result["cases"]), "errors": sum(c["error"] is not None for c in result["cases"]), "module_sha256": result["module_sha256"], "corpus_sha256": result["corpus_sha256"]}))
