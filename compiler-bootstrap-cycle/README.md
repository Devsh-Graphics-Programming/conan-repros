# Compiler bootstrap graph rejected as a cycle

Conan rejects a compiler bootstrap graph even though its package configurations have a valid build order.

## Toolchain setup

Consider the following compiler setup:

1. A bootstrap package downloads prebuilt compiler and tool archives, verifies their checksums, and assembles a usable toolchain. It does not compile LLVM or Clang.
2. That bootstrap toolchain builds LLVM, Clang, and their dependencies, including Z3, from source.
3. The resulting compiler, called `clang-hybrid` here, builds consumer libraries.

The build profile selects the bootstrap, and the host profile selects the hybrid. The hybrid compiler and its Z3 dependency belong to the build context. A consumer library can also require LLVM as a host-context SDK, bringing in a second Z3 configuration built with the hybrid.

## Minimal reproduction

The repro starts at the consumer's Z3 dependency, omitting the outer consumer and SDK packages. Three metadata-only recipes retain the relevant dependencies:

- `clang-bootstrap/1.0` has no dependencies.
- `z3/1.0` is a library with compiler settings.
- `clang-hybrid/1.0` is an application that requires `z3/1.0`.

The profiles use Conan's built-in Clang 21 settings for build and Clang 22 for host. Both supply their compiler through `[tool_requires]` with default visibility. The consumer requires only `z3/1.0`.

Arrows below mean "requires":

```text
z3 [host, Clang 22]
  -> clang-hybrid [build, Clang 21]
     -> z3 [build, Clang 21]
        -> clang-bootstrap [build]
```

`clang-hybrid` also directly requires `clang-bootstrap` as a build tool.

## Why this is a bug

The two Z3 nodes have the same recipe revision but different package IDs. The compiler's Z3 uses the bootstrap and does not need the hybrid. Only the consumer's Z3 needs the hybrid, so every dependency can be satisfied in this order:

```text
clang-bootstrap -> z3 [Clang 21] -> clang-hybrid -> z3 [Clang 22]
```

**Conan already computes a valid order for this exact set of package configurations.** With the same recipes, profiles, and empty binary cache, `graph build-order --order-by=configuration` succeeds. The repro verifies the two distinct Z3 package IDs and checks that every dependency precedes its consumer.

Grouping both Z3 configurations into one recipe node produces `z3 -> clang-hybrid -> z3`. The compiler must be processed between the two Z3 configurations, so failure of `--order-by=recipe` alone is expected.

The bug is the inconsistency between that valid order and `graph info` rejecting the same dependency setup as ill-formed and impossible to install. In Conan 2.32.0, [`InstallGraph` defaults to recipe grouping](https://github.com/conan-io/conan/blob/2.32.0/conan/internal/graph/install_graph.py), and [`install_binaries()` uses that default](https://github.com/conan-io/conan/blob/2.32.0/conan/api/subapi/install.py).

Expected behavior: `graph info` accepts the graph, and one `conan install --build=missing` processes packages in the order above, reusing available binaries or building missing packages. Installation ordering should preserve dependencies between package configurations, allowing configurations of the same recipe to be processed at different stages. This would handle this class of graphs without compiler-specific rules or changes to these recipe dependencies.

## Run

With Conan 2.32.0 installed and `conan` on PATH, run from the repository root:

```bash
python compiler-bootstrap-cycle/reproduce.py
```

The script exports the recipes into a temporary Conan home and runs graph commands with remotes disabled. No packages are downloaded or built. No compiler installation is needed, and temporary Conan state is removed on exit.

Expected output when the bug is present:

```text
graph build-order --order-by=configuration: OK
graph build-order --order-by=recipe: LOOP
graph info: LOOP
BUG REPRODUCED without building any packages
```

The script succeeds only when it finds the valid configuration order and both failing commands report a dependency loop.

## Validation

This standalone repro produced the result above on Windows with Conan `2.32.0` and `develop2` commit `22d18a3e4f478f4def5cba238c320dc5ddf1193d` (`2.33.0-dev`). The same failure was also reproduced in a compiler bootstrap graph on Linux with Conan `2.32.0`.

The [GitHub Actions workflow](../.github/workflows/compiler-bootstrap-cycle.yml) is configured to run this repro on Ubuntu with Conan `2.32.0` and the current `develop2` branch, on push or manual dispatch.
