# Build-order drops transitive recipe options

This reproduces a mismatch between a node returned by `conan graph build-order` and the node recreated from its generated `build_args`.

The official [`graph build-order` documentation](https://docs.conan.io/2/reference/commands/graph/build_order.html) describes `build_args` as the "arguments needed for a `conan install <args>` to fire the build of this package". Conan also supports setting options of requirements through [`default_options`](https://docs.conan.io/2/reference/conanfile/attributes.html#default-options).

The graph is intentionally empty of build logic:

```text
app -> middle -> leaf
```

`app` sets both `middle/*:shared=True` and `leaf/*:shared=True`. The full build order therefore selects a `middle` package ID that depends on shared `leaf`. However, the generated `build_args` for `middle` only preserve `middle/*:shared=True`. Running them with the same host and build profiles changes `leaf` back to its default `shared=False` and produces a different `middle` package ID.

This is a bug because the generated command does not recreate the package node it belongs to.

## Run

Install Conan and run:

```bash
python build-order-transitive-options/reproduce.py
```

The script uses a temporary Conan home and prints:

```text
leaf shared: True -> False
middle package_id: <full graph id> -> <isolated id>
BUG REPRODUCED
```

GitHub Actions runs the same repro with Conan `2.32.0` and the current Conan 2 `develop2` branch.
