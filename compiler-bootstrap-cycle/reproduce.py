import json
import os
from pathlib import Path
import subprocess
import tempfile


root = Path(__file__).resolve().parent


def run(env, *args, expect_loop=False):
    result = subprocess.run(
        ["conan", *args], cwd=root, env=env, text=True, capture_output=True
    )
    if expect_loop:
        if result.returncode == 0 or "ERROR: There is a loop in the graph" not in result.stderr:
            raise SystemExit(f"Expected a dependency loop error:\n{result.stdout}\n{result.stderr}")
    elif result.returncode:
        raise SystemExit(result.stderr)
    return result


with tempfile.TemporaryDirectory(prefix="conan-compiler-cycle-repro-") as home:
    env = os.environ | {"CONAN_HOME": home, "PYTHONDONTWRITEBYTECODE": "1"}
    print(run(env, "--version").stdout.strip())
    for recipe in ("clang-bootstrap", "z3", "clang-hybrid"):
        run(env, "export", str(root / recipe))

    common = (
        ".", "--build=missing", "-nr",
        "-pr:b=profiles/bootstrap", "-pr:h=profiles/hybrid",
    )
    result = run(
        env, "graph", "build-order", *common,
        "--order-by=configuration", "--format=json",
    )
    levels = json.loads(result.stdout)["order"]
    nodes = [node for level in levels for node in level]
    assert len(nodes) == 4, nodes
    seen = set()
    for level in levels:
        for node in level:
            assert set(node["depends"]) <= seen, node
            settings = node["info"]["settings"]
            print(
                f"{node['ref'].split('#')[0]} [{node['context']}, "
                f"compiler.version={settings.get('compiler.version', '-')}]: "
                f"{node['package_id']}"
            )
        seen.update(node["pref"] for node in level)

    z3 = [node for node in nodes if node["ref"].startswith("z3/")]
    assert len(z3) == 2
    assert z3[0]["ref"] == z3[1]["ref"]
    assert z3[0]["package_id"] != z3[1]["package_id"]
    assert {node["context"] for node in z3} == {"build", "host"}
    print("graph build-order --order-by=configuration: OK")

    run(env, "graph", "build-order", *common, "--order-by=recipe", expect_loop=True)
    print("graph build-order --order-by=recipe: LOOP")
    result = run(env, "graph", "info", *common, expect_loop=True)
    print("graph info: LOOP")
    print(result.stderr[result.stderr.rfind("ERROR:"):].strip())
    print("BUG REPRODUCED without building any packages")
