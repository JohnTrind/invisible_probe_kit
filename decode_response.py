#!/usr/bin/env python3
"""
decode_response — cola aqui a resposta de QUALQUER modelo (Claude, ChatGPT,
Ollama...) e ve se trazia caracteres invisiveis escondidos.

Uso:
  python decode_response.py           # modo interativo (cola e Ctrl-D)
  python decode_response.py < ficheiro.txt
  echo "texto" | python decode_response.py
"""
import sys
import json
import probe


def main():
    text = sys.stdin.read()
    if not text:
        print("cola o texto no stdin (Ctrl-D para terminar).")
        return
    inv = probe.scan(text)
    print(f"caracteres invisiveis/suspeitos encontrados: {len(inv)}")
    if inv:
        print(json.dumps(inv[:40], ensure_ascii=False, indent=2))
    dec = {k: v for k, v in probe.auto_decode(text).items() if v}
    print("\ndecifrado:", json.dumps(dec, ensure_ascii=False) if dec else "(nada)")
    print("\ntexto sanitizado:")
    print(probe.strip_invisibles(text))


if __name__ == "__main__":
    main()
