"""Análises salvas por usuário, guardadas em SQLite local (mesma pasta das contas).

No Streamlit Cloud o arquivo some quando o site reinicia; salvar serve para não repetir a análise durante o uso.
"""
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

CAMINHO = Path(__file__).resolve().parent.parent / "dados_locais" / "analises.db"


def _abrir() -> sqlite3.Connection:
    CAMINHO.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(CAMINHO)
    con.execute(
        "CREATE TABLE IF NOT EXISTS analises ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT NOT NULL, titulo TEXT NOT NULL, "
        "conteudo TEXT NOT NULL, criado_em TEXT NOT NULL)"
    )
    return con


def salvar(usuario: str, analise: dict, avisos: list) -> int:
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conteudo = json.dumps({"analise": analise, "avisos": avisos}, ensure_ascii=False)
    with closing(_abrir()) as con, con:
        cur = con.execute(
            "INSERT INTO analises (usuario, titulo, conteudo, criado_em) VALUES (?, ?, ?, ?)",
            (usuario.strip().lower(), str(analise.get("titulo") or "Análise sem título"), conteudo, agora),
        )
        return cur.lastrowid


def listar(usuario: str) -> list[dict]:
    """Mais recentes primeiro: [{'id', 'titulo', 'criado_em'}]."""
    with closing(_abrir()) as con:
        linhas = con.execute(
            "SELECT id, titulo, criado_em FROM analises WHERE usuario = ? ORDER BY id DESC",
            (usuario.strip().lower(),),
        ).fetchall()
    return [{"id": i, "titulo": t, "criado_em": c} for i, t, c in linhas]


def carregar(usuario: str, id_: int) -> tuple[dict, list] | None:
    with closing(_abrir()) as con:
        linha = con.execute(
            "SELECT conteudo FROM analises WHERE id = ? AND usuario = ?", (id_, usuario.strip().lower())
        ).fetchone()
    if not linha:
        return None
    dados = json.loads(linha[0])
    return dados["analise"], dados.get("avisos", [])


def excluir(usuario: str, id_: int) -> None:
    with closing(_abrir()) as con, con:
        con.execute("DELETE FROM analises WHERE id = ? AND usuario = ?", (id_, usuario.strip().lower()))
