# vis_asm

Visualize the control-flow graph (CFG) of a function in an assembly file
produced by the Go, Julia, OCaml, or Rust compiler.

Given the function name as it appears in the source code, `vis_asm` writes a
DOT file and renders an SVG of the CFG.

## Requirements

- Python ≥ 3.8
- [Graphviz](https://graphviz.org/) — the `dot` binary must be on `PATH`
- *(optional)* `ipython`, for inline rendering inside a Jupyter notebook

## Install

```bash
pip install .
```

With inline Jupyter support:

```bash
pip install '.[notebook]'
```

## Usage

From the shell:

```bash
vis-asm path/to/template.s Collatz
```

This writes `template_Collatz.dot` and `template_Collatz.svg` next to the
assembly file. Use `-o DIR` to direct the output elsewhere.

From Python, or inside a Jupyter notebook:

```python
from vis_asm import vis_asm
vis_asm("go/template.s", "Collatz")
```

In Jupyter the returned `IPython.display.SVG` renders inline.

## Producing the input assembly

| Compiler | Command                                  |
|----------|------------------------------------------|
| Go       | `go tool objdump -gnu <binary>`          |
| Julia    | `code_native(io, f, types)`              |
| OCaml    | `ocamlopt -S source.ml`                  |
| Rust     | `rustc --emit asm source.rs`             |

## License

MIT — see [LICENSE](LICENSE).
