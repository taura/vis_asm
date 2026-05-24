"""
vis_asm: Visualize the control-flow graph (CFG) of a function in an
assembly file.

Given an assembly file produced by Go (``go tool objdump -gnu``), Julia,
OCaml (``ocamlopt -S``), or Rust (``rustc --emit asm``), and the function
name as it appears in the source code, ``vis_asm`` writes a DOT file and
renders an SVG showing the CFG of that function.

Usage in a Jupyter notebook::

    from vis_asm import vis_asm
    vis_asm("go/template.s", "Collatz")
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

# A GAS label: token followed by ':' at the start of a line.
_GAS_LABEL_RE = re.compile(r'^([^\s:#]+):\s*(?:#.*)?$')


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------

def _detect_format(lines):
    for line in lines[:400]:
        if line.startswith('TEXT '):
            return 'go'
        if line.startswith('camlTemplate.'):
            return 'ocaml'
        if re.match(r'^julia_\w+_\d+:', line):
            return 'julia'
    return 'gas'  # rust / generic GAS


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
        patterns = [re.compile(r'^(camlTemplate\.' + re.escape(fun_name) + r'_\d+):')]
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


def _parse_gas_items(fun_lines):
    """Parse GAS-style function lines.  Skip directives, keep labels & insns."""
    items = []
    for line in fun_lines:
        s = line.rstrip()
        if not s.strip():
            continue
        stripped = s.lstrip()
        if stripped.startswith('#') or stripped.startswith(';'):
            continue
        m = _GAS_LABEL_RE.match(s)
        if m:
            items.append(('label', m.group(1)))
            continue
        if stripped.startswith('.'):
            continue  # directive
        text = stripped
        # Strip trailing "# ..." or "; ..." comments
        for sep in ('#', ';'):
            if sep in text:
                text = text.split(sep, 1)[0].rstrip()
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


def _write_dot(blocks, edges, dot_path, title=''):
    out = []
    out.append('digraph CFG {')
    if title:
        out.append('  label=' + _safe_id(title) + ';')
        out.append('  labelloc=t;')
    out.append('  node [shape=box, fontname="monospace", fontsize=10];')
    out.append('  edge [fontname="monospace", fontsize=10];')

    for b in blocks:
        parts = []
        if not b.get('synthetic'):
            for alias in b['aliases']:
                parts.append(_escape(alias) + ':')
        for ins in b['instrs']:
            parts.append(_escape(ins))
        # Join with the DOT left-justified-newline separator `\l`.  Each
        # part is already escaped, so we splice the literal two-char `\l`
        # in here unescaped.
        label = '\\l'.join(parts)
        if parts:
            label += '\\l'
        out.append('  {nid} [label="{lab}"];'.format(
            nid=_safe_id(b['id']), lab=label,
        ))

    for src, dst, lab in edges:
        if lab:
            out.append('  {s} -> {d} [label={l}];'.format(
                s=_safe_id(src), d=_safe_id(dst), l=_safe_id(lab),
            ))
        else:
            out.append('  {s} -> {d};'.format(s=_safe_id(src), d=_safe_id(dst)))

    out.append('}')
    Path(dot_path).write_text('\n'.join(out) + '\n')


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def vis_asm(a_asm, fun_name, output_dir=None):
    """Render the CFG of ``fun_name`` from assembly file ``a_asm``.

    Writes ``<stem>_<fun_name>.dot`` and ``<stem>_<fun_name>.svg`` next to
    the assembly file (or in ``output_dir`` if given).

    Returns an ``IPython.display.SVG`` instance when IPython is available,
    so the SVG renders inline in a Jupyter notebook.  Otherwise returns the
    path to the SVG file as a string.
    """
    a_asm = Path(a_asm)
    out_dir = Path(output_dir) if output_dir is not None else a_asm.parent

    lines = a_asm.read_text().splitlines(keepends=False)
    fmt = _detect_format(lines)

    if fmt == 'go':
        start, end, label = _find_go_function(lines, fun_name)
    else:
        start, end, label = _find_gas_function(lines, fun_name, fmt)

    if start is None:
        raise ValueError(
            "Function {!r} not found in {} (format={})".format(
                fun_name, a_asm, fmt))

    fun_lines = lines[start:end]
    items = _parse_go_items(fun_lines) if fmt == 'go' else _parse_gas_items(fun_lines)
    blocks = _build_blocks(items)
    edges = _build_edges(blocks)

    dot_path = out_dir / "{}_{}.dot".format(a_asm.stem, fun_name)
    svg_path = out_dir / "{}_{}.svg".format(a_asm.stem, fun_name)
    _write_dot(blocks, edges, dot_path, title=label)

    if shutil.which('dot') is None:
        raise RuntimeError("graphviz 'dot' not found in PATH")
    subprocess.run(
        ['dot', '-Tsvg', str(dot_path), '-o', str(svg_path)],
        check=True,
    )

    try:
        from IPython.display import SVG  # type: ignore
        return SVG(filename=str(svg_path))
    except ImportError:
        return str(svg_path)


# ---------------------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------------------

def main(argv=None):
    """CLI entry point: ``vis-asm <asm_file> <function> [-o DIR]``."""
    import argparse

    parser = argparse.ArgumentParser(
        prog='vis-asm',
        description='Visualize the control-flow graph of a function '
                    'in an assembly file.',
    )
    parser.add_argument(
        'asm_file',
        help='assembly file (Go `objdump -gnu`, OCaml `-S`, Julia, '
             'or Rust `--emit asm`)',
    )
    parser.add_argument(
        'function',
        help='function name as it appears in the source code',
    )
    parser.add_argument(
        '-o', '--output-dir', default=None,
        help='directory for the .dot and .svg output '
             '(default: alongside the assembly file)',
    )
    args = parser.parse_args(argv)

    result = vis_asm(args.asm_file, args.function, output_dir=args.output_dir)
    if isinstance(result, str):
        print(result)


if __name__ == '__main__':
    main()
