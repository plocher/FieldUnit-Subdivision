"""Text-level edits on KiCad 10 .kicad_sym symbol blocks (scripted library passes).

Each function takes and returns the text of one top-level `(symbol "Name" ...)` block,
as KiCad's symbol editor writes it (tab-indented). Graphics are never touched.
"""
import re


def end_of(t, i):
    d, j = 0, i
    while True:
        d += (t[j] == "(") - (t[j] == ")")
        j += 1
        if d == 0:
            return j


def split(lib):
    """Return (head, [(name, block)], tail) for a library text."""
    out, pos, head = [], None, None
    for m in re.finditer(r'\n\t\(symbol "([^"]+)"\n', lib):
        s = m.start() + 2
        if head is None:
            head = lib[:s]
        e = end_of(lib, s)
        out.append((m.group(1), lib[s:e]))
        pos = e
    return head, out, lib[pos:]


def join(head, blocks, tail):
    return head + "\n\t".join(b for _, b in blocks) + tail


def rename(b, old, new):
    b = b.replace(f'(symbol "{old}"', f'(symbol "{new}"', 1)
    return re.sub(r'\(symbol "' + re.escape(old) + r'_(\d+_\d+)"', lambda m: f'(symbol "{new}_{m.group(1)}"', b)


def _prop_span(b, key):
    m = re.search(r'\n\t\t\(property "' + re.escape(key) + r'" "', b)
    if not m:
        return None
    s = m.start() + 3
    return m.start(), end_of(b, s)


def get_prop(b, key):
    m = re.search(r'\n\t\t\(property "' + re.escape(key) + r'" "([^"]*)"', b)
    return m.group(1) if m else None


def set_prop(b, key, value):
    m = re.search(r'(\n\t\t\(property "' + re.escape(key) + r'" ")([^"]*)"', b)
    assert m, key
    return b[:m.start(2)] + value + b[m.end(2):]


def del_prop(b, key):
    sp = _prop_span(b, key)
    return b if sp is None else b[:sp[0]] + b[sp[1]:]


def add_prop(b, key, value, at="0 0 0"):
    """Append a hidden property after the last top-level property."""
    assert get_prop(b, key) is None, key
    last = list(re.finditer(r'\n\t\t\(property "', b))[-1]
    e = end_of(b, last.start() + 3)
    p = (f'\n\t\t(property "{key}" "{value}"\n\t\t\t(at {at})\n\t\t\t(show_name no)\n'
         f'\t\t\t(do_not_autoplace no)\n\t\t\t(hide yes)\n\t\t\t(effects\n\t\t\t\t(font\n'
         f'\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)')
    return b[:e] + p + b[e:]


def _pins(b):
    return [(m.start(), end_of(b, m.start())) for m in re.finditer(r'\(pin \w+ \w+\n', b)]


def _pin_at(b, number):
    for s, e in _pins(b):
        if re.search(r'\(number "' + re.escape(number) + r'"', b[s:e]):
            return s, e
    raise KeyError(number)


def pin_names(b):
    return [re.search(r'\(name "([^"]*)"', b[s:e]).group(1) for s, e in _pins(b)]


def edit_pin(b, number, name=None, new_number=None, etype=None):
    s, e = _pin_at(b, number)
    p = b[s:e]
    if name is not None:
        p = re.sub(r'\(name "[^"]*"', f'(name "{name}"', p, count=1)
    if new_number is not None:
        p = re.sub(r'\(number "[^"]*"', f'(number "{new_number}"', p, count=1)
    if etype is not None:
        p = re.sub(r'^\(pin \w+', f'(pin {etype}', p)
    return b[:s] + p + b[e:]


def del_pin(b, number):
    s, e = _pin_at(b, number)
    # drop the pin and its leading newline+indent
    ls = b.rfind("\n", 0, s)
    return b[:ls] + b[e:]


def set_text(b, old, new):
    assert f'(text "{old}"' in b, old
    return b.replace(f'(text "{old}"', f'(text "{new}"')
