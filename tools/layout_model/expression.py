"""Indication expressions (the owner, 2026-10-28): what a desk lamp's ``Indication`` and a lever pin's ``Indication.<pin>``
state. A boolean expression over full tokens, K included: ``|`` or, ``&`` and, ``!`` not, parentheses; a token may be
qualified ``Interlocking:TOKEN``. One token is the simplest expression. During the transition a comma also means or.

    expr   := term (('|' | ',') term)*
    term   := factor ('&' factor)*
    factor := '!' factor | '(' expr ')' | TOKEN
    TOKEN  := one or more characters that are none of whitespace | , & ! ( )

``parse`` gives a tree of tuples; ``tokens`` the tokens it consumes, in first-use order; ``text`` the normalized form
(`` | `` and `` & `` with spaces, ``!`` tight, parentheses only where precedence needs them, a comma written as ``|``);
``mapped`` the same tree with every token replaced (to qualify them in a scope). The token's spelling is never checked
here: what a token means is the derivation's business. Studio reads and writes the same grammar.
"""
from __future__ import annotations

import re
from typing import Callable, Union

# A tree: ("token", name) | ("not", tree) | ("and", (tree, ...)) | ("or", (tree, ...)); and/or hold two or more.
Expr = tuple
_LEX = re.compile(r"\s*(?:([|,&!()])|([^\s|,&!()]+))")


class ExpressionError(ValueError):
    """An expression that does not parse: the message names what was expected and the character position."""


def _lex(text: str) -> list[tuple[str, str, int]]:
    out, i = [], 0
    while i < len(text):
        if text[i:].strip() == "":
            break
        m = _LEX.match(text, i)
        if not m:                                          # unreachable: every character is an operator or a token's
            raise ExpressionError(f"unexpected character at {i}")
        op, tok = m.groups()
        out.append(("op", op, m.start(1)) if op else ("token", tok, m.start(2)))
        i = m.end()
    return out


def _join(op: str, parts: list) -> Expr:
    """One operand alone; else the operator over its operands, a nested one of the same operator flattened."""
    flat = [y for x in parts for y in (x[1] if x[0] == op else (x,))]
    return flat[0] if len(flat) == 1 else (op, tuple(flat))


def parse(text: str) -> Expr:
    """The tree of one expression; ExpressionError when it is empty or malformed."""
    items = _lex(text)
    pos = 0

    def peek() -> tuple[str, str, int] | None:
        return items[pos] if pos < len(items) else None

    def fail(what: str) -> ExpressionError:
        at = peek()
        return ExpressionError(f"{what} expected at {at[2] if at else len(text)}"
                               + (f", found {at[1]!r}" if at else ", found the end") + f" in {text!r}")

    def expr() -> Expr:
        nonlocal pos
        parts = [term()]
        while (p := peek()) and p[0] == "op" and p[1] in "|,":
            pos += 1
            parts.append(term())
        return _join("or", parts)

    def term() -> Expr:
        nonlocal pos
        parts = [factor()]
        while (p := peek()) and p[:2] == ("op", "&"):
            pos += 1
            parts.append(factor())
        return _join("and", parts)

    def factor() -> Expr:
        nonlocal pos
        p = peek()
        if p is None or (p[0] == "op" and p[1] not in "!("):
            raise fail("a token, ! or (")
        pos += 1
        if p[0] == "token":
            return ("token", p[1])
        if p[1] == "!":
            return ("not", factor())
        inner = expr()
        if peek() is None or peek()[:2] != ("op", ")"):
            raise fail(")")
        pos += 1
        return inner

    tree = expr()
    if peek() is not None:
        raise fail("an operator or the end")
    return tree


def tokens(tree: Expr) -> list[str]:
    """Every token the expression consumes, once each, in first-use order."""
    out: list[str] = []

    def walk(t: Expr) -> None:
        if t[0] == "token":
            if t[1] not in out:
                out.append(t[1])
        elif t[0] == "not":
            walk(t[1])
        else:
            for x in t[1]:
                walk(x)
    walk(tree)
    return out


_RANK = {"or": 1, "and": 2, "not": 3, "token": 4}


def text(tree: Expr) -> str:
    """The normalized text: `` | `` and `` & ``, ``!`` tight, parentheses only where a lower-ranked operator sits
    inside a higher-ranked one."""
    def show(t: Expr, outer: int) -> str:
        if t[0] == "token":
            s = t[1]
        elif t[0] == "not":
            s = "!" + show(t[1], _RANK["not"])
        else:
            s = (" | " if t[0] == "or" else " & ").join(show(x, _RANK[t[0]] + (t[0] == "or")) for x in t[1])
        return f"({s})" if _RANK[t[0]] < outer else s
    return show(tree, 0)


def mapped(tree: Expr, fn: Callable[[str], str]) -> Expr:
    """The same tree with every token replaced by ``fn(token)``."""
    if tree[0] == "token":
        return ("token", fn(tree[1]))
    if tree[0] == "not":
        return ("not", mapped(tree[1], fn))
    return (tree[0], tuple(mapped(x, fn) for x in tree[1]))


def normalize(source: Union[str, Expr], fn: Callable[[str], str] = lambda t: t) -> tuple[str, list[str]]:
    """(normalized text, tokens) of an expression, each token passed through ``fn``."""
    tree = mapped(parse(source) if isinstance(source, str) else source, fn)
    return text(tree), tokens(tree)
