"""
vis_asm: Visualize the control-flow graph (CFG) of a function in an
assembly file.

Given an assembly file produced by Go (``go tool objdump -gnu``), Julia,
OCaml (``ocamlopt -S``), or Rust (``rustc --emit asm``), and the function
name as it appears in the source code, ``vis_asm`` writes a DOT file and
renders an SVG showing the CFG of that function.

Usage in a Jupyter notebook::

    from vis_asm import vis_asm_fun, vis_asm_file
    vis_asm_fun("go/template.s", "Collatz")   # one function
    vis_asm_file("go/template.s")             # every function in the file
"""

import re
import shutil
import subprocess
from pathlib import Path


# ---------------------------------------------------------------------------
# Regexes shared across formats
# ---------------------------------------------------------------------------

# A jump mnemonic followed by its target.  Any mnemonic starting with "j"
# (e.g. j, jmp, jmpq, je, jne, jae, jbe, jg, jge, jl, jle, jp, jnp, ...)
_JUMP_RE = re.compile(r'^\s*(j\w+)\s+(.+?)\s*$', re.IGNORECASE)

# Return mnemonic
_RET_RE = re.compile(r'^\s*(retq|ret)\b', re.IGNORECASE)

# Go's objdump line: "  src:line<TAB>0xaddr<TAB>bytes<TAB>INSTR<TAB>// gnu"
_GO_INSN_RE = re.compile(r'^\s+\S+\s+(0x[0-9a-f]+)\s+[0-9a-f]+\s+(.+?)\s*$')
_GO_TEXT_RE = re.compile(r'^TEXT\s+(.+?)\(SB\)')

# A GAS label: token followed by ':' at the start of a line, optionally
# followed by a trailing comment ('#', '//', or ';').
_GAS_LABEL_RE = re.compile(r'^([^\s:#]+):\s*(?:(?:#|//|;).*)?$')

# ANSI SGR escape sequences (Julia's `code_native` colourises its output by
# default; stripping these lets us parse such files unchanged).
_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------

# OCaml's ocamlopt emits ``caml<ModuleName>.<symbol>``; the module name is
# the source file's basename with its first letter capitalised.
_OCAML_PREFIX_RE = re.compile(r'^(caml[A-Z][A-Za-z0-9_]*)\.')


def _detect_format(lines):
    for line in lines[:400]:
        if line.startswith('TEXT '):
            return 'go'
        if _OCAML_PREFIX_RE.match(line):
            return 'ocaml'
        if re.match(r'^julia_\w+_\d+:', line):
            return 'julia'
    return 'gas'  # rust / generic GAS


def _ocaml_module_prefix(lines):
    """Return the ``caml<ModuleName>`` prefix used in this OCaml asm file."""
    for line in lines[:400]:
        m = _OCAML_PREFIX_RE.match(line)
        if m:
            return m.group(1)
    return 'camlTemplate'


# ---------------------------------------------------------------------------
# Function location
# ---------------------------------------------------------------------------

def _find_go_function(lines, fun_name):
    """Return (start, end, label) for a Go function, or (None, None, None)."""
    for i, line in enumerate(lines):
        m = _GO_TEXT_RE.match(line)
        if not m:
            continue
        full = m.group(1)
        short = full.rsplit('.', 1)[-1]
        if short == fun_name or full == fun_name:
            end = len(lines)
            for j in range(i + 1, len(lines)):
                if lines[j].startswith('TEXT '):
                    end = j
                    break
            return i, end, full
    return None, None, None


def _find_gas_function(lines, fun_name, fmt):
    """Return (start, end, label) for a GAS-style function."""
    if fmt == 'ocaml':
        prefix = _ocaml_module_prefix(lines)
        patterns = [re.compile(
            r'^(' + re.escape(prefix) + r'\.' + re.escape(fun_name) + r'_\d+):')]
    elif fmt == 'julia':
        patterns = [re.compile(r'^(julia_' + re.escape(fun_name) + r'_\d+):')]
    else:
        patterns = [re.compile(r'^(' + re.escape(fun_name) + r'):')]

    size_re_tpl = r'^\s*\.size\s+{}\b'
    end_label_re = re.compile(r'^\.Lfunc_end\d+:')
    for pat in patterns:
        for i, line in enumerate(lines):
            m = pat.match(line)
            if not m:
                continue
            label = m.group(1)
            size_re = re.compile(size_re_tpl.format(re.escape(label)))
            end = len(lines)
            for j in range(i + 1, len(lines)):
                # Stop before the closing marker label or .size directive.
                if end_label_re.match(lines[j]) or size_re.match(lines[j]):
                    end = j
                    break
            return i, end, label
    return None, None, None


# ---------------------------------------------------------------------------
# Parsing into a stream of ('label', name) / ('insn', addr, text) items
# ---------------------------------------------------------------------------

def _parse_go_items(fun_lines):
    """Parse Go function lines.

    Go's objdump output has no source-level labels; instead each instruction
    carries an address.  We synthesise labels by treating every hex jump
    target (and the function entry) as a label.
    """
    insns = []  # list of (addr, text)
    # Strip a trailing relocation comment like "[1:5]R_CALL:runtime.foo".
    reloc_tail = re.compile(r'\s*\[\d+:\d+\]R_\S+.*$')
    for line in fun_lines:
        m = _GO_INSN_RE.match(line)
        if not m:
            continue
        addr, rest = m.group(1), m.group(2)
        # Use the native (GNU/AT&T) instruction after "//", which objdump
        # emits as a translation of Go's Plan 9 form.  Falling back to the
        # Plan 9 form if no "//" is present.  Also resolves tail-call jumps
        # to their target addresses (Plan 9 names them symbolically).
        if '//' in rest:
            text = rest.split('//', 1)[1]
        else:
            text = rest
        text = reloc_tail.sub('', text).strip()
        insns.append((addr, text))

    if not insns:
        return []

    func_addrs = {a for a, _ in insns}
    targets = set()
    for _, text in insns:
        jm = _JUMP_RE.match(text)
        if not jm:
            continue
        tok = jm.group(2).split()[0].rstrip(',')
        if tok.startswith('0x') and tok in func_addrs:
            targets.add(tok)
    targets.add(insns[0][0])  # function entry is always a leader

    items = []
    for addr, text in insns:
        if addr in targets:
            items.append(('label', addr))
        items.append(('insn', addr, text))
    return items


_TRAIL_SLASH_COMMENT = re.compile(r'\s*//.*$')
_TRAIL_HASH_COMMENT = re.compile(r'\s+#(?:\s.*)?$')
_TRAIL_SEMI_COMMENT = re.compile(r'\s+;.*$')


def _parse_gas_items(fun_lines):
    """Parse GAS-style function lines.  Skip directives, keep labels & insns."""
    items = []
    for line in fun_lines:
        s = line.rstrip()
        if not s.strip():
            continue
        stripped = s.lstrip()
        # Full-line comments: '#' / ';' / '//' at column 0.
        if (stripped.startswith('#') or stripped.startswith(';')
                or stripped.startswith('//')):
            continue
        m = _GAS_LABEL_RE.match(s)
        if m:
            items.append(('label', m.group(1)))
            continue
        if stripped.startswith('.'):
            continue  # directive
        # Strip trailing comments.  AArch64 uses '#' to introduce immediates
        # (e.g. "[sp, #-16]", "add x0, x8, #123"), so we only treat '#' as a
        # comment marker when preceded by whitespace AND followed by either
        # whitespace or end-of-line — never when glued to its operand.
        text = _TRAIL_SLASH_COMMENT.sub('', stripped)
        text = _TRAIL_HASH_COMMENT.sub('', text)
        text = _TRAIL_SEMI_COMMENT.sub('', text)
        text = text.rstrip()
        if text:
            items.append(('insn', None, text))
    return items


# ---------------------------------------------------------------------------
# Block construction
# ---------------------------------------------------------------------------

def _ends_block(instr):
    """True if ``instr`` is a control-transfer that ends a basic block:
    any jump (conditional or unconditional) or a return."""
    if instr is None:
        return False
    return bool(_JUMP_RE.match(instr) or _RET_RE.match(instr))


def _build_blocks(items):
    """Group items into basic blocks.

    A block starts at every label.  In addition, the instruction immediately
    following a jump/return starts a new block even if no source-level label
    precedes it (compilers sometimes omit such labels for fall-throughs).
    Consecutive labels with no instructions between them collapse into a
    single block whose ``aliases`` list all of them.
    """
    blocks = []
    current = None
    synth_counter = [0]

    def new_block(name, synthetic=False):
        blk = {
            'id': name,
            'aliases': [name],
            'instrs': [],
            'last_insn': None,
            'synthetic': synthetic,
        }
        blocks.append(blk)
        return blk

    for item in items:
        if item[0] == 'label':
            name = item[1]
            if current is not None and not current['instrs']:
                current['aliases'].append(name)
                current['synthetic'] = False
                if current['id'].startswith('__bb_synth_'):
                    current['id'] = name
            else:
                current = new_block(name)
        else:  # ('insn', addr, text)
            _, addr, text = item
            if current is None:
                current = new_block(addr if addr is not None else '_entry')
            elif _ends_block(current['last_insn']):
                if addr is not None:
                    current = new_block(addr)
                else:
                    synth_counter[0] += 1
                    current = new_block(
                        '__bb_synth_{}'.format(synth_counter[0]),
                        synthetic=True,
                    )
            current['instrs'].append(text)
            current['last_insn'] = text
    return blocks


# ---------------------------------------------------------------------------
# Edge construction
# ---------------------------------------------------------------------------

def _is_return(instr):
    return instr is not None and _RET_RE.match(instr) is not None


def _get_jump(instr):
    """Return (is_conditional, target) if ``instr`` is a jump."""
    if instr is None:
        return None
    m = _JUMP_RE.match(instr)
    if not m:
        return None
    mnemonic = m.group(1).lower()
    target = m.group(2).split(None, 1)[0].rstrip(',')
    is_uncond = mnemonic in ('jmp', 'jmpq')
    is_cond = mnemonic.startswith('j') and not is_uncond
    if not (is_cond or is_uncond):
        return None
    return (is_cond, target)


def _build_edges(blocks):
    """Return a list of (src_id, dst_id, edge_label)."""
    alias_to_id = {}
    for b in blocks:
        for a in b['aliases']:
            alias_to_id[a] = b['id']

    edges = []
    for i, b in enumerate(blocks):
        last = b['last_insn']
        if _is_return(last):
            continue
        jinfo = _get_jump(last)
        if jinfo is None:
            if i + 1 < len(blocks):
                edges.append((b['id'], blocks[i + 1]['id'], None))
            continue
        is_cond, target = jinfo
        dst = alias_to_id.get(target)
        if dst is not None:
            edges.append((b['id'], dst, 'T' if is_cond else None))
        # else: jump leaves the function (tail call / external) — no edge
        if is_cond and i + 1 < len(blocks):
            edges.append((b['id'], blocks[i + 1]['id'], 'F'))
    return edges


# ---------------------------------------------------------------------------
# DOT emission
# ---------------------------------------------------------------------------

def _safe_id(name):
    return '"' + name.replace('\\', '\\\\').replace('"', '\\"') + '"'


def _escape(s):
    # Escape for DOT string labels: backslash, quote, and the literal
    # characters that DOT treats specially in record labels.
    return (s.replace('\\', '\\\\')
             .replace('"', '\\"')
             .replace('<', '\\<')
             .replace('>', '\\>')
             .replace('|', '\\|')
             .replace('{', '\\{')
             .replace('}', '\\}'))


def _emit_block(b, prefix=''):
    parts = []
    if not b.get('synthetic'):
        for alias in b['aliases']:
            parts.append(_escape(alias) + ':')
    for ins in b['instrs']:
        parts.append(_escape(ins))
    # Join with the DOT left-justified-newline separator `\l`.  Each part
    # is already escaped, so we splice the literal two-char `\l` in here
    # unescaped.
    label = '\\l'.join(parts)
    if parts:
        label += '\\l'
    return '{nid} [label="{lab}"];'.format(
        nid=_safe_id(prefix + b['id']), lab=label,
    )


def _emit_edge(src, dst, lab, prefix=''):
    s = _safe_id(prefix + src)
    d = _safe_id(prefix + dst)
    if lab:
        return '{} -> {} [label={}];'.format(s, d, _safe_id(lab))
    return '{} -> {};'.format(s, d)


def _write_dot(blocks, edges, dot_path, title=''):
    out = []
    out.append('digraph CFG {')
    if title:
        out.append('  label=' + _safe_id(title) + ';')
        out.append('  labelloc=t;')
    out.append('  node [shape=box, fontname="monospace", fontsize=10];')
    out.append('  edge [fontname="monospace", fontsize=10];')
    for b in blocks:
        out.append('  ' + _emit_block(b))
    for src, dst, lab in edges:
        out.append('  ' + _emit_edge(src, dst, lab))
    out.append('}')
    Path(dot_path).write_text('\n'.join(out) + '\n')


def _write_dot_multi(funs, dot_path, title=''):
    """Write a single DOT with every function as its own cluster.

    ``funs`` is a list of ``(name, blocks, edges, label)``.  Each function's
    node ids are namespaced with ``f<i>_`` so labels can repeat freely
    across functions without colliding.
    """
    out = []
    out.append('digraph CFG {')
    if title:
        out.append('  label=' + _safe_id(title) + ';')
        out.append('  labelloc=t;')
    out.append('  node [shape=box, fontname="monospace", fontsize=10];')
    out.append('  edge [fontname="monospace", fontsize=10];')
    for i, (name, blocks, edges, label) in enumerate(funs):
        prefix = 'f{}_'.format(i)
        out.append('  subgraph cluster_{} {{'.format(i))
        out.append('    label=' + _safe_id(label or name) + ';')
        out.append('    labelloc=t;')
        out.append('    style=rounded;')
        for b in blocks:
            out.append('    ' + _emit_block(b, prefix=prefix))
        for src, dst, lab in edges:
            out.append('    ' + _emit_edge(src, dst, lab, prefix=prefix))
        out.append('  }')
    out.append('}')
    Path(dot_path).write_text('\n'.join(out) + '\n')


def _render_svg(dot_path, svg_path):
    if shutil.which('dot') is None:
        raise RuntimeError("graphviz 'dot' not found in PATH")
    subprocess.run(
        ['dot', '-Tsvg', str(dot_path), '-o', str(svg_path)],
        check=True,
    )


def _svg_result(svg_path):
    try:
        from IPython.display import SVG  # type: ignore
        return SVG(filename=str(svg_path))
    except ImportError:
        return str(svg_path)


# ---------------------------------------------------------------------------
# Function enumeration (used by vis_asm_file)
# ---------------------------------------------------------------------------

def _list_functions(lines, fmt):
    """Return source-level function names found in ``lines``, in file order.

    The names returned are exactly those that can be passed to
    ``vis_asm_fun`` for this file (i.e. source-level names for Go / OCaml /
    Julia, and the symbol as it appears at column 0 for generic GAS / Rust).
    """
    names = []
    seen = set()
    if fmt == 'go':
        for line in lines:
            m = _GO_TEXT_RE.match(line)
            if not m:
                continue
            full = m.group(1)
            short = full.rsplit('.', 1)[-1]
            if short not in seen:
                seen.add(short)
                names.append(short)
    elif fmt == 'ocaml':
        prefix = _ocaml_module_prefix(lines)
        pat = re.compile(
            r'^' + re.escape(prefix) + r'\.([A-Za-z_][A-Za-z0-9_]*)_\d+:')
        for line in lines:
            m = pat.match(line)
            if m and m.group(1) not in seen:
                seen.add(m.group(1))
                names.append(m.group(1))
    elif fmt == 'julia':
        pat = re.compile(r'^julia_([A-Za-z_][A-Za-z0-9_]*)_\d+:')
        for line in lines:
            m = pat.match(line)
            if m and m.group(1) not in seen:
                seen.add(m.group(1))
                names.append(m.group(1))
    else:
        # GAS / Rust: trust ``.type <name>, @function`` directives.
        type_pat = re.compile(
            r'^\s*\.type\s+([^\s,]+)\s*,\s*[@%]function\b')
        for line in lines:
            m = type_pat.match(line)
            if m and m.group(1) not in seen:
                seen.add(m.group(1))
                names.append(m.group(1))
    return names


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def _read_asm(a_asm):
    lines = Path(a_asm).read_text().splitlines(keepends=False)
    lines = [_ANSI_RE.sub('', line) for line in lines]
    return lines, _detect_format(lines)


def _analyze(lines, fmt, fun_name, src=None):
    """Locate ``fun_name`` in ``lines`` and return (blocks, edges, label)."""
    if fmt == 'go':
        start, end, label = _find_go_function(lines, fun_name)
    else:
        start, end, label = _find_gas_function(lines, fun_name, fmt)
    if start is None:
        raise ValueError(
            "Function {!r} not found in {} (format={})".format(
                fun_name, src if src is not None else '<input>', fmt))
    fun_lines = lines[start:end]
    items = _parse_go_items(fun_lines) if fmt == 'go' else _parse_gas_items(fun_lines)
    blocks = _build_blocks(items)
    edges = _build_edges(blocks)
    return blocks, edges, label


def vis_asm_fun(a_asm, fun_name, output_dir=None):
    """Render the CFG of ``fun_name`` from assembly file ``a_asm``.

    Writes ``<stem>_<fun_name>.dot`` and ``<stem>_<fun_name>.svg`` next to
    the assembly file (or in ``output_dir`` if given).

    Returns an ``IPython.display.SVG`` instance when IPython is available,
    so the SVG renders inline in a Jupyter notebook.  Otherwise returns the
    path to the SVG file as a string.
    """
    a_asm = Path(a_asm)
    out_dir = Path(output_dir) if output_dir is not None else a_asm.parent

    lines, fmt = _read_asm(a_asm)
    blocks, edges, label = _analyze(lines, fmt, fun_name, src=a_asm)

    dot_path = out_dir / "{}_{}.dot".format(a_asm.stem, fun_name)
    svg_path = out_dir / "{}_{}.svg".format(a_asm.stem, fun_name)
    _write_dot(blocks, edges, dot_path, title=label)
    _render_svg(dot_path, svg_path)
    return _svg_result(svg_path)


def vis_asm_file(a_asm, output_dir=None):
    """Render every function in ``a_asm`` into a single combined CFG.

    Discovers every function defined in the file and emits one DOT file
    (``<stem>.dot``) and one SVG (``<stem>.svg``) in which each function is
    drawn as its own labelled cluster.

    Returns an ``IPython.display.SVG`` instance when IPython is available,
    so the SVG renders inline in a Jupyter notebook.  Otherwise returns the
    path to the SVG file as a string.
    """
    a_asm = Path(a_asm)
    out_dir = Path(output_dir) if output_dir is not None else a_asm.parent

    lines, fmt = _read_asm(a_asm)
    names = _list_functions(lines, fmt)
    funs = []
    for name in names:
        blocks, edges, label = _analyze(lines, fmt, name, src=a_asm)
        funs.append((name, blocks, edges, label))

    dot_path = out_dir / "{}.dot".format(a_asm.stem)
    svg_path = out_dir / "{}.svg".format(a_asm.stem)
    _write_dot_multi(funs, dot_path, title=a_asm.stem)
    _render_svg(dot_path, svg_path)
    return _svg_result(svg_path)


# ---------------------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------------------

def main(argv=None):
    """CLI entry point: ``vis-asm <asm_file> [<function>] [-o DIR]``.

    If ``<function>`` is omitted, every function in the file is visualized.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog='vis-asm',
        description='Visualize the control-flow graph of one function '
                    '(or every function) in an assembly file.',
    )
    parser.add_argument(
        'asm_file',
        help='assembly file (Go `objdump -gnu`, OCaml `-S`, Julia, '
             'or Rust `--emit asm`)',
    )
    parser.add_argument(
        'function', nargs='?', default=None,
        help='function name as it appears in the source code; '
             'if omitted, every function in the file is visualized',
    )
    parser.add_argument(
        '-o', '--output-dir', default=None,
        help='directory for the .dot and .svg output '
             '(default: alongside the assembly file)',
    )
    args = parser.parse_args(argv)

    if args.function is None:
        result = vis_asm_file(args.asm_file, output_dir=args.output_dir)
    else:
        result = vis_asm_fun(
            args.asm_file, args.function, output_dir=args.output_dir)
    if isinstance(result, str):
        print(result)


if __name__ == '__main__':
    main()
