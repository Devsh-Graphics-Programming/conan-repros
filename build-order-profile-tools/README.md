# Build-order commands require a later toolchain package

Conan orders `compiler` before `compiler-wrapper`, but its generated command for `compiler` fails because the wrapper has not been built yet.

## Reproduction

`compiler` has no dependencies and `compiler-wrapper` tool-requires it. The host profile selects Clang 22 and adds the wrapper through `[tool_requires]`. A separate build profile selects Clang 21 without the wrapper. Both recipes contain only package metadata.

The full build order is valid:

```text
compiler/1.0 [build, Clang 21] -> compiler-wrapper/1.0 [build]
```

The script runs the compiler's `build_args` with `profiles.self.args` unchanged from Conan's JSON, with remotes disabled and an empty binary cache.

That command applies the host profile's `[tool_requires]` to the new graph, adding the wrapper alongside the requested compiler:

```text
conan install --tool-requires=compiler/1.0 --build=compiler/1.0 ...
├── compiler/1.0                 Build
└── compiler-wrapper/1.0         Missing
    └── compiler/1.0
```

The compiler keeps its planned package ID, but the command fails with `ERROR: Missing binary: compiler-wrapper/1.0:<package_id>`. Installing the complete graph with `--build=missing` succeeds and builds both planned package IDs.

## Why this is a bug

The [documentation](https://docs.conan.io/2/reference/commands/graph/build_order.html) says `build_args` supplies the arguments for building each package with `conan install`. Conan's [serializer](https://github.com/conan-io/conan/blob/c6e27e773a013dd9288dd6c19720f515b42760d7/conan/internal/graph/install_graph.py#L374-L386) returns the dependencies and command from the same planned node:

```python
"depends": [d.repr_notime() for d in self.depends],
"overrides": self.overrides.serialize(),
"build_args": self._build_args(),
```

For `compiler`, that node has `depends: []`. Its [command generator](https://github.com/conan-io/conan/blob/c6e27e773a013dd9288dd6c19720f515b42760d7/conan/internal/graph/install_graph.py#L361-L372) selects `--tool-requires` because the node is in the build context and emits `--build=compiler/1.0`.

Executing that command creates a [host-context root](https://github.com/conan-io/conan/blob/c6e27e773a013dd9288dd6c19720f515b42760d7/conan/api/subapi/graph.py#L87-L99). The [profile application](https://github.com/conan-io/conan/blob/c6e27e773a013dd9288dd6c19720f515b42760d7/conan/internal/graph/graph_builder.py#L190-L215) adds the wrapper to that root. Then [`install_binaries()`](https://github.com/conan-io/conan/blob/c6e27e773a013dd9288dd6c19720f515b42760d7/conan/api/subapi/install.py#L43-L48) rejects the missing wrapper before any build starts:

```python
install_graph.raise_errors()
install_order = install_graph.install_order()
```

The generated command therefore needs a binary from a later level, although the plan marks this node as having no prerequisites. The script checks that contradiction using Conan's output unchanged, then builds the complete graph successfully with the same profiles and package IDs.

Applying profile requirements to command-line installs is [intentional](https://github.com/conan-io/conan/issues/19699#issuecomment-3989755727). The inconsistency is between the build order and its generated command. Host and build profiles are separate, no versions or options are overridden, and no dependency cycle is reported.

## Run

```bash
python build-order-profile-tools/reproduce.py
```

Run from the repository root with Conan on `PATH`. Expected final output is `BUG REPRODUCED`. The script uses a temporary cache and runs offline without compiling anything.

Reproduced on Windows with Python 3.13 using Conan 2.32.0, 2.33.0 and `develop2` at `c6e27e773a013dd9288dd6c19720f515b42760d7` (2.34.0-dev). The profiles' Linux settings are metadata only.
