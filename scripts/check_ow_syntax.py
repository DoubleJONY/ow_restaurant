"""Read-only syntax checks for English Workshop text exports (stdlib only)."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import glob
from pathlib import Path
import re
import sys


class SyntaxFailure(ValueError):
    pass


@dataclass
class Token:
    value: str
    kind: str
    offset: int


LEX = re.compile(
    r'(?P<space>\s+)|(?P<comment>//[^\n]*|/\*[\s\S]*?\*/)|'
    r'(?P<string>"(?:\\[^\r\n]|[^"\\\r\n])*")|'
    r'(?P<number>\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)|'
    r'(?P<name>(?:Arrow:[ \t]+\w+|Soldier:[ \t]+76(?:[ \t]+\w+)*|[^\W\d]\w*(?:[ \t]+(?!(?:\d+|global|player)[ \t]*:)\w+)*))|'
    r'(?P<symbol>==|!=|<=|>=|&&|\|\||\+=|-=|\*=|/=|%=|\^=|[{}()\[\],;:.?+*/%\^!<>=-])'
)


class Parser:
    def __init__(self, source: str, strict_control_flow: bool = False):
        self.source = source
        self.strict_control_flow = strict_control_flow
        self.tokens: list[Token] = []
        self.index = 0
        pos = 0
        while pos < len(source):
            match = LEX.match(source, pos)
            if not match:
                self.fail("invalid character or unterminated string/comment", pos)
            kind = match.lastgroup
            if kind not in {"space", "comment"}:
                value = match.group()
                if kind == "name":
                    value = re.sub(r"[ \t]+", " ", value)
                self.tokens.append(Token(value, kind, pos))
            pos = match.end()
        self.tokens.append(Token("<EOF>", "eof", len(source)))

    @property
    def token(self) -> Token:
        return self.tokens[self.index]

    def fail(self, message: str, offset: int | None = None):
        pos = self.token.offset if offset is None else offset
        line = self.source.count("\n", 0, pos) + 1
        column = pos - self.source.rfind("\n", 0, pos)
        raise SyntaxFailure(f"{line}:{column}: {message}")

    def take(self) -> Token:
        token = self.token
        self.index += 1
        return token

    def accept(self, value: str) -> bool:
        if self.token.value == value:
            self.take()
            return True
        return False

    def expect(self, value: str):
        if not self.accept(value):
            self.fail(f"expected {value!r}, found {self.token.value!r}")

    def kind(self, kind: str) -> Token:
        if self.token.kind != kind:
            self.fail(f"expected {kind}, found {self.token.value!r}")
        return self.take()

    def declarations(self, variables: bool):
        self.expect("{")
        scopes = set()
        if not variables:
            self.entries()
        while variables and self.token.value != "}":
            scope = self.kind("name").value
            if scope not in {"global", "player"} or scope in scopes:
                self.fail(f"invalid or duplicate variable scope {scope!r}")
            scopes.add(scope)
            self.expect(":")
            self.entries()
        self.expect("}")

    def entries(self):
        indexes, names = set(), set()
        while self.token.kind == "number":
            number = self.take()
            if not number.value.isdecimal():
                self.fail("declaration index must be an integer", number.offset)
            self.expect(":")
            name = self.kind("name")
            if " " in name.value:
                self.fail("declaration name must be a single identifier", name.offset)
            index = int(number.value)
            if index in indexes or name.value in names:
                self.fail("duplicate declaration index or name", number.offset)
            indexes.add(index)
            names.add(name.value)

    PRECEDENCE = {"||": 1, "&&": 2, "==": 3, "!=": 3, "<": 4,
                  ">": 4, "<=": 4, ">=": 4, "+": 5, "-": 5,
                  "*": 6, "/": 6, "%": 6, "^": 7}

    def expression(self, minimum: int = 0):
        if self.token.value in {"!", "-", "+"}:
            self.take()
            self.expression(8)
        elif self.accept("("):
            self.expression()
            self.expect(")")
        elif self.token.kind in {"name", "number", "string"}:
            self.take()
        else:
            self.fail(f"expected expression, found {self.token.value!r}")
        while True:
            if self.accept("("):
                if not self.accept(")"):
                    self.expression()
                    while self.accept(","):
                        self.expression()
                    self.expect(")")
            elif self.accept("["):
                self.expression()
                self.expect("]")
            elif self.accept("."):
                self.kind("name")
            elif self.token.value in self.PRECEDENCE and self.PRECEDENCE[self.token.value] >= minimum:
                precedence = self.PRECEDENCE[self.take().value]
                self.expression(precedence + 1)
            elif minimum == 0 and self.accept("?"):
                self.expression()
                self.expect(":")
                self.expression()
            else:
                break

    def statements(self, section: str):
        self.expect("{")
        flow: list[tuple[str, bool]] = []
        count = 0
        while self.token.value != "}":
            # Workshop comments are quoted labels preceding an action/condition.
            while self.token.kind == "string":
                self.take()
            disabled = self.accept("disabled")
            # The lexer folds spaces in multi-word names, including this prefix.
            if self.token.value.startswith("disabled "):
                disabled = True
                self.token.value = self.token.value[len("disabled "):]
            start = self.token
            self.expression()
            if section == "actions" and self.token.value in {"=", "+=", "-=", "*=", "/=", "%=", "^="}:
                self.take()
                self.expression()
            self.expect(";")
            count += 1
            if section != "actions" or disabled or not self.strict_control_flow:
                continue
            name = start.value
            if name in {"If", "While", "For Global Variable", "For Player Variable"}:
                flow.append((name, False))
            elif name in {"Else", "Else If"}:
                if not flow or flow[-1][0] != "If" or flow[-1][1]:
                    self.fail(f"{name} without an open If, or after Else", start.offset)
                flow[-1] = ("If", name == "Else")
            elif name == "End":
                if not flow:
                    self.fail("End without an open control block", start.offset)
                flow.pop()
        # Workshop permits control blocks to run to the end of the action list.
        self.expect("}")
        if section == "event" and count == 0:
            self.fail("event must not be empty")

    def parse(self):
        blocks = set()
        rules = 0
        while self.token.kind != "eof":
            self.accept("disabled")
            if self.token.value == "disabled rule":
                self.token.value = "rule"
            block = self.kind("name")
            if block.value in {"variables", "subroutines"}:
                if block.value in blocks:
                    self.fail(f"duplicate {block.value} block", block.offset)
                blocks.add(block.value)
                self.declarations(block.value == "variables")
            elif block.value == "rule":
                rules += 1
                self.expect("(")
                self.kind("string")
                self.expect(")")
                self.expect("{")
                sections = set()
                while self.token.value != "}":
                    section = self.kind("name")
                    if section.value not in {"event", "conditions", "actions"} or section.value in sections:
                        self.fail("unknown or duplicate rule section", section.offset)
                    sections.add(section.value)
                    self.statements(section.value)
                self.expect("}")
                if "event" not in sections:
                    self.fail("rule requires an event section", block.offset)
            else:
                self.fail(f"unsupported top-level block {block.value!r}", block.offset)
        if not blocks and not rules:
            self.fail("empty Workshop source")


def check(source: str, strict_control_flow: bool = False):
    Parser(source, strict_control_flow).parse()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="files, directories (recursive), or quoted glob patterns")
    parser.add_argument("--strict-control-flow", action="store_true", help="also reject orphan End/Else actions (optional lint)")
    args = parser.parse_args()
    files: set[Path] = set()
    errors = []
    for value in args.paths:
        path = Path(value)
        matches = list(path.rglob("*.ow")) if path.is_dir() else [Path(p) for p in glob.glob(value, recursive=True)]
        matches = [p for p in matches if p.is_file()]
        if not matches:
            errors.append(f"{value}: no input files matched")
        files.update(p.resolve() for p in matches)
    for path in sorted(files):
        try:
            check(path.read_text(encoding="utf-8-sig"), args.strict_control_flow)
            print(f"PASS {path}")
        except (OSError, UnicodeError, SyntaxFailure) as exc:
            errors.append(f"{path}:{exc}")
    for error in errors:
        print(error, file=sys.stderr)
    print(f"Checked {len(files)} file(s); {len(errors)} failure(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
