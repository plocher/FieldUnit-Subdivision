"""Minimal KiCad s-expression reader/writer (tokens preserved as strings)."""
from __future__ import annotations


_UNESCAPE = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\', '"': '"'}
_ESCAPE = {'\\': '\\\\', '"': '\\"', '\n': '\\n', '\t': '\\t', '\r': '\\r'}


def parse(text: str):
    """Return nested lists; atoms are str (quoted strings keep a \x00 prefix marker)."""
    i = 0
    n = len(text)
    stack = []
    cur = None
    while i < n:
        c = text[i]
        if c == '(':
            new = []
            if cur is not None:
                cur.append(new)
                stack.append(cur)
            cur = new
            i += 1
        elif c == ')':
            if stack:
                cur = stack.pop()
            else:
                return cur
            i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while j < n:
                if text[j] == '\\':
                    buf.append(_UNESCAPE.get(text[j + 1], text[j + 1]))
                    j += 2
                elif text[j] == '"':
                    break
                else:
                    buf.append(text[j])
                    j += 1
            cur.append('"' + ''.join(buf))  # leading quote marks "was quoted"
            i = j + 1
        elif c in ' \t\r\n':
            i += 1
        else:
            j = i
            while j < n and text[j] not in ' \t\r\n()"':
                j += 1
            cur.append(text[i:j])
            i = j
    return cur


def val(atom: str) -> str:
    """Unquoted value of an atom."""
    return atom[1:] if atom.startswith('"') else atom


def q(s: str) -> str:
    """Quote a string for output. Newlines MUST be escaped: a literal newline
    inside a quoted string makes KiCad reject the whole file silently."""
    return '"' + ''.join(_ESCAPE.get(ch, ch) for ch in s) + '"'


def dump(node, indent=0) -> str:
    """Write s-expression text, KiCad-ish formatting (tabs)."""
    if isinstance(node, str):
        return q(val(node)) if node.startswith('"') else node
    parts = []
    head = node[0] if node and isinstance(node[0], str) else None
    simple = all(isinstance(x, str) for x in node)
    if simple:
        return '(' + ' '.join(dump(x) for x in node) + ')'
    pad = '\t' * (indent + 1)
    out = ['(' + (dump(node[0]) if node else '')]
    rest = node[1:]
    # keep leading atoms on the head line
    k = 0
    while k < len(rest) and isinstance(rest[k], str):
        out.append(' ' + dump(rest[k]))
        k += 1
    for child in rest[k:]:
        out.append('\n' + pad + dump(child, indent + 1))
    out.append('\n' + '\t' * indent + ')')
    return ''.join(out)


def find(node, name):
    """First child list whose head is name."""
    for c in node:
        if isinstance(c, list) and c and val(c[0]) == name:
            return c
    return None


def findall(node, name):
    return [c for c in node if isinstance(c, list) and c and val(c[0]) == name]


def prop(node, name):
    """Value of a (property "name" "value") child."""
    for c in findall(node, 'property'):
        if val(c[1]) == name:
            return val(c[2])
    return None
