import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile


root = Path(__file__).resolve().parent


def run(env, *args, expect_missing=False):
    result = subprocess.run(["conan", *args], cwd=root, env=env, text=True, capture_output=True)
    if expect_missing:
        if result.returncode == 0 or "ERROR: Missing binary: compiler-wrapper/1.0:" not in result.stderr:
            raise SystemExit(f"Expected a missing wrapper binary:\n{result.stdout}\n{result.stderr}")
    elif result.returncode:
        raise SystemExit(result.stderr)
    return result


with tempfile.TemporaryDirectory(prefix="conan-build-order-profile-tools-") as temporary:
    env = os.environ | {"CONAN_HOME": str(Path(temporary) / "home"), "PYTHONDONTWRITEBYTECODE": "1"}
    print(run(env, "--version").stdout.strip())
    for recipe in ("compiler", "compiler-wrapper"):
        run(env, "export", str(root / recipe))

    profiles = ("-pr:h=profiles/host", "-pr:b=profiles/bootstrap")
    requested = "--tool-requires=compiler-wrapper/1.0"
    result = run(env, "graph", "build-order", requested, *profiles, "--build=missing", "--order-by=configuration", "--format=json", "-nr")
    order = json.loads(result.stdout)
    nodes = [node for level in order["order"] for node in level]
    assert [node["ref"].split("#")[0] for node in nodes] == ["compiler/1.0", "compiler-wrapper/1.0"]
    compiler, wrapper = nodes
    assert compiler["depends"] == []
    assert wrapper["depends"] == [compiler["pref"]]
    assert compiler["context"] == wrapper["context"] == "build"
    assert compiler["info"]["settings"]["compiler.version"] == "21"
    print("planned order: compiler/1.0 -> compiler-wrapper/1.0")

    args = (*shlex.split(compiler["build_args"]), *shlex.split(order["profiles"]["self"]["args"]))
    print(f"generated command: conan install {shlex.join(args)}")
    result = run(env, "graph", "info", *args, "--format=json", "-nr")
    isolated = list(json.loads(result.stdout)["graph"]["nodes"].values())
    isolated_compiler = next(node for node in isolated if node.get("ref") == compiler["ref"])
    isolated_wrapper = next(node for node in isolated if node.get("ref") == wrapper["ref"])
    assert isolated_compiler["package_id"] == compiler["package_id"]
    assert isolated_wrapper["binary"] == "Missing"
    print("compiler package_id: unchanged")
    print("isolated command also requires compiler-wrapper/1.0")

    result = run(env, "install", *args, "-nr", f"-of={temporary}/isolated", expect_missing=True)
    print(next(line for line in result.stderr.splitlines() if line.startswith("ERROR: Missing binary:")))
    result = run(env, "install", requested, *profiles, "--build=missing", "-nr", f"-of={temporary}/complete", "--format=json")
    complete = {node["ref"]: node for node in json.loads(result.stdout)["graph"]["nodes"].values() if node.get("ref")}
    for node in nodes:
        assert complete[node["ref"]]["package_id"] == node["package_id"]
        assert complete[node["ref"]]["binary"] == "Build"
    print("install complete graph: OK")
    print("BUG REPRODUCED")
