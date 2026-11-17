"""Contas de usuário do site, guardadas em um arquivo SQLite local.

A senha nunca é guardada: o arquivo guarda só um resumo (PBKDF2-SHA256 com sal aleatório por conta).
No Streamlit Cloud o arquivo some quando o site reinicia; o login do avaliador, nos Secrets, não depende dele.
"""
import hashlib
import hmac
import re
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

CAMINHO = Path(__file__).resolve().parent.parent / "dados_locais" / "contas.db"
ITERACOES = 200_000
PADRAO_USUARIO = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")
MIN_SENHA = 8


class ErroConta(Exception):
    """Erro de conta com mensagem pronta para mostrar na tela."""


def _abrir() -> sqlite3.Connection:
    CAMINHO.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(CAMINHO)
    con.execute(
        "CREATE TABLE IF NOT EXISTS usuarios ("
        "usuario TEXT PRIMARY KEY, sal BLOB NOT NULL, resumo BLOB NOT NULL, criado_em TEXT NOT NULL)"
    )
    return con


def _resumo(senha: str, sal: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), sal, ITERACOES)


def validar(usuario: str, senha: str, confirmacao: str) -> None:
    if not PADRAO_USUARIO.match(usuario):
        raise ErroConta("O usuário deve ter de 3 a 30 caracteres: letras, números, ponto, hífen ou sublinhado.")
    if len(senha) < MIN_SENHA:
        raise ErroConta(f"A senha deve ter pelo menos {MIN_SENHA} caracteres.")
    if senha != confirmacao:
        raise ErroConta("As senhas não são iguais.")


def criar_conta(usuario: str, senha: str, confirmacao: str, reservados: tuple = ()) -> str:
    """Cria a conta e devolve o nome do usuário. Levanta ErroConta com a mensagem para a tela."""
    usuario = usuario.strip()
    validar(usuario, senha, confirmacao)
    chave = usuario.lower()
    if chave in {r.lower() for r in reservados if r}:
        raise ErroConta("Esse usuário já existe.")
    sal = secrets.token_bytes(16)
    try:
        with closing(_abrir()) as con:
            con.execute(
                "INSERT INTO usuarios (usuario, sal, resumo, criado_em) VALUES (?, ?, ?, ?)",
                (chave, sal, _resumo(senha, sal), datetime.now(timezone.utc).isoformat()),
            )
            con.commit()
    except sqlite3.IntegrityError as erro:
        raise ErroConta("Esse usuário já existe.") from erro
    except (sqlite3.Error, OSError) as erro:
        raise ErroConta("Não foi possível salvar a conta neste servidor. Tente de novo.") from erro
    return usuario


def conferir(usuario: str, senha: str) -> bool:
    """Confere usuário e senha. O tempo de resposta não revela se o usuário existe."""
    chave = usuario.strip().lower()
    try:
        with closing(_abrir()) as con:
            linha = con.execute("SELECT sal, resumo FROM usuarios WHERE usuario = ?", (chave,)).fetchone()
    except (sqlite3.Error, OSError):
        return False
    sal, esperado = linha if linha else (b"\0" * 16, b"\0" * 32)
    ok = hmac.compare_digest(_resumo(senha, sal), esperado)
    return bool(linha) and ok
