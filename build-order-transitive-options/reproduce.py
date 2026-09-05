import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

root = Path(__file__).parent

def run(env, *args):
    result = subprocess.run(["conan", *args], env=env, text=True, capture_output=True)
    if result.returncode:
        raise SystemExit(result.stderr)
    return result.stdout

with tempfile.TemporaryDirectory(prefix="conan-build-order-repro-") as home:
    env = os.environ | {"CONAN_HOME": home}
    version = run(env, "--version").strip()
    run(env, "profile", "detect", "--force")
    run(env, "remote", "disable", "conancenter")
    for recipe in ("leaf", "middle", "app"):
        run(env, "export", str(root / recipe))

    order = json.loads(run(env, "graph", "build-order", "--requires=app/1.0", "--build=missing", "--order-by=configuration", "-pr:h=default", "-pr:b=default", "--format=json"))
    nodes = [node for level in order["order"] for node in level]
    planned_leaf = next(node for node in nodes if node["ref"].startswith("leaf/"))
    planned_middle = next(node for node in nodes if node["ref"].startswith("middle/"))

    isolated = json.loads(run(env, "graph", "info", *shlex.split(planned_middle["build_args"]), "-pr:h=default", "-pr:b=default", "--format=json"))
    nodes = isolated["graph"]["nodes"].values()
    isolated_leaf = next(node for node in nodes if node.get("ref", "").startswith("leaf/"))
    isolated_middle = next(node for node in nodes if node.get("ref", "").startswith("middle/"))

    print(version)
    print(f"build_args: {planned_middle['build_args']}")
    print(f"leaf shared: {planned_leaf['info']['options']['shared']} -> {isolated_leaf['options']['shared']}")
    print(f"middle package_id: {planned_middle['package_id']} -> {isolated_middle['package_id']}")
    assert str(planned_leaf["info"]["options"]["shared"]) == "True"
    assert str(isolated_leaf["options"]["shared"]) == "False"
    assert planned_middle["package_id"] != isolated_middle["package_id"]
    print("BUG REPRODUCED")
