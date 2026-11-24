#!/usr/bin/env python3
"""
probe — nucleo do kit. Esconde um payload de teste em caracteres invisiveis
dentro de uma frase de isco, deteta e decifra.

Objetivo: QA / seguranca. Medir se um modelo "apanha" instrucoes ocultas e
inspecionar qualquer texto (input ou resposta) em busca de chars invisiveis.

Esquemas:
  tags  -> espelho ASCII em U+E0000..U+E007F (o que modelos por vezes leem)
  zw    -> binario com zero-widths U+200B (0) / U+200C (1)

CLI:
  python probe.py encode "frase isco" "payload"  [--scheme tags|zw]
  python probe.py decode "<texto com invisiveis>"
  python probe.py scan   "<texto>"
  python probe.py strip  "<texto>"
"""
import sys
import json
import argparse
import unicodedata

TAG_BASE = 0xE0000
ZW0, ZW1 = "​", "‌"

SUSPECT_CATS = {"Cf", "Cc", "Cs", "Co"}
OK_WHITESPACE = {" ", "\t", "\n", "\r"}


# ---------- codificar ----------
def encode_tags(decoy: str, secret: str) -> str:
    hidden = "".join(chr(ord(c) + TAG_BASE) for c in secret if ord(c) < 0x80)
    return decoy + hidden


def encode_zw(decoy: str, secret: str) -> str:
    bits = "".join(f"{b:08b}" for b in secret.encode("utf-8"))
    return decoy + "".join(ZW1 if x == "1" else ZW0 for x in bits)


def encode(decoy: str, secret: str, scheme: str = "tags") -> str:
    return encode_tags(decoy, secret) if scheme == "tags" else encode_zw(decoy, secret)


# ---------- decifrar ----------
def decode_tags(text: str) -> str:
    return "".join(
        chr(ord(c) - TAG_BASE) for c in text if TAG_BASE <= ord(c) <= TAG_BASE + 0x7F
    )


def decode_zw(text: str) -> str:
    bits = "".join("1" if c == ZW1 else "0" for c in text if c in (ZW0, ZW1))
    if len(bits) < 8:
        return ""
    bits = bits[: len(bits) // 8 * 8]
    try:
        return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8)).decode("utf-8")
    except UnicodeDecodeError:
        return "<bytes invalidos>"


def auto_decode(text: str) -> dict:
    return {"tags": decode_tags(text) or None, "zw": decode_zw(text) or None}


# ---------- detetar / sanitizar ----------
def scan(text: str) -> list:
    found = []
    for i, c in enumerate(text):
        if c in OK_WHITESPACE:
            continue
        cp, cat = ord(c), unicodedata.category(c)
        if cat in SUSPECT_CATS or TAG_BASE <= cp <= TAG_BASE + 0x7F:
            found.append({"idx": i, "cp": f"U+{cp:04X}", "cat": cat,
                          "name": unicodedata.name(c, "?")})
    return found


def strip_invisibles(text: str) -> str:
    return "".join(
        c for c in text
        if c in OK_WHITESPACE or (
            unicodedata.category(c) not in SUSPECT_CATS
            and not (TAG_BASE <= ord(c) <= TAG_BASE + 0x7F)
        )
    )


def _main():
    ap = argparse.ArgumentParser(description="esconde/deteta/decifra chars invisiveis")
    sub = ap.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("encode")
    e.add_argument("decoy")
    e.add_argument("secret")
    e.add_argument("--scheme", choices=["tags", "zw"], default="tags")

    for name in ("decode", "scan", "strip"):
        p = sub.add_parser(name)
        p.add_argument("text")

    a = ap.parse_args()
    if a.cmd == "encode":
        out = encode(a.decoy, a.secret, a.scheme)
        sys.stdout.write(out + "\n")
        sys.stderr.write(f"[info] {len(out)} chars, {len(scan(out))} invisiveis\n")
    elif a.cmd == "decode":
        print(json.dumps(auto_decode(a.text), ensure_ascii=False))
    elif a.cmd == "scan":
        print(json.dumps(scan(a.text), ensure_ascii=False, indent=2))
    elif a.cmd == "strip":
        print(strip_invisibles(a.text))


if __name__ == "__main__":
    _main()
