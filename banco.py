"""Camada de persistência - SQLite (SGBD embutido no Python)."""
import hashlib
import secrets
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "estudio.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT NOT NULL,
    usuario     TEXT NOT NULL UNIQUE,
    senha_hash  TEXT NOT NULL,
    perfil      TEXT NOT NULL DEFAULT 'Operador'
);

CREATE TABLE IF NOT EXISTS artistas (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nome           TEXT NOT NULL,
    nome_artistico TEXT,
    genero         TEXT,
    telefone       TEXT,
    email          TEXT
);

CREATE TABLE IF NOT EXISTS salas (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT NOT NULL UNIQUE,
    tipo          TEXT NOT NULL,
    valor_hora    REAL NOT NULL,
    equipamentos  TEXT
);

CREATE TABLE IF NOT EXISTS sessoes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    artista_id     INTEGER NOT NULL REFERENCES artistas(id) ON DELETE RESTRICT,
    sala_id        INTEGER NOT NULL REFERENCES salas(id) ON DELETE RESTRICT,
    data           TEXT NOT NULL,
    hora_inicio    TEXT NOT NULL,
    duracao_horas  REAL NOT NULL,
    status         TEXT NOT NULL DEFAULT 'Agendada',
    valor_total    REAL NOT NULL DEFAULT 0,
    observacoes    TEXT
);

CREATE TABLE IF NOT EXISTS referencias (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    faixa        TEXT NOT NULL,
    artista      TEXT,
    album        TEXT,
    genero       TEXT,
    duracao      TEXT,
    preview_url  TEXT,
    origem       TEXT,
    importado_em TEXT DEFAULT (datetime('now','localtime')),
    UNIQUE(faixa, artista, album)
);
"""

TABELAS = ["usuarios", "artistas", "salas", "sessoes", "referencias"]


def conectar():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def executar(sql, params=()):
    """INSERT / UPDATE / DELETE. Retorna o id gerado (lastrowid)."""
    con = conectar()
    try:
        with con:  # commit/rollback automático
            return con.execute(sql, params).lastrowid
    finally:
        con.close()


def executar_varios(sql, lista_params):
    con = conectar()
    try:
        with con:
            return con.executemany(sql, lista_params).rowcount
    finally:
        con.close()


def consultar(sql, params=()):
    """SELECT. Retorna lista de dicionários."""
    con = conectar()
    try:
        return [dict(r) for r in con.execute(sql, params).fetchall()]
    finally:
        con.close()


# ---------------------------------------------------------------- senhas
def hash_senha(senha, sal=None):
    sal = sal or secrets.token_hex(8)
    h = hashlib.pbkdf2_hmac("sha256", senha.encode(), sal.encode(), 100_000).hex()
    return f"{sal}${h}"


def conferir_senha(senha, armazenado):
    sal, _ = armazenado.split("$", 1)
    return secrets.compare_digest(hash_senha(senha, sal), armazenado)


def autenticar(usuario, senha):
    linhas = consultar("SELECT * FROM usuarios WHERE usuario = ?", (usuario.strip(),))
    if linhas and conferir_senha(senha, linhas[0]["senha_hash"]):
        u = linhas[0]
        u.pop("senha_hash")
        return u
    return None


# ---------------------------------------------------------------- inicialização
def inicializar():
    novo = not DB_PATH.exists()
    con = conectar()
    con.executescript(SCHEMA)
    con.close()
    if novo or not consultar("SELECT id FROM usuarios LIMIT 1"):
        _popular_exemplo()


def _popular_exemplo():
    executar(
        "INSERT INTO usuarios (nome, usuario, senha_hash, perfil) VALUES (?,?,?,?)",
        ("Administrador", "admin", hash_senha("admin123"), "Administrador"),
    )
    executar_varios(
        "INSERT INTO salas (nome, tipo, valor_hora, equipamentos) VALUES (?,?,?,?)",
        [
            ("Sala A - Gravação", "Gravação", 150.0, "Mesa SSL, Neumann U87, Pré Neve 1073"),
            ("Sala B - Ensaio", "Ensaio", 60.0, "Bateria Pearl, amplificadores Marshall/Ampeg"),
            ("Sala C - Mixagem", "Mixagem/Masterização", 200.0, "Pro Tools HDX, monitores Genelec"),
        ],
    )
    executar_varios(
        "INSERT INTO artistas (nome, nome_artistico, genero, telefone, email) VALUES (?,?,?,?,?)",
        [
            ("Ana Souza", "Ana S.", "MPB", "(16) 99999-1111", "ana@exemplo.com"),
            ("Banda Os Ruídos", "Os Ruídos", "Rock", "(16) 98888-2222", "contato@osruidos.com"),
            ("Carlos Lima", "MC Lima", "Rap", "(16) 97777-3333", "mclima@exemplo.com"),
        ],
    )
    executar_varios(
        "INSERT INTO sessoes (artista_id, sala_id, data, hora_inicio, duracao_horas, status, valor_total, observacoes)"
        " VALUES (?,?,?,?,?,?,?,?)",
        [
            (1, 1, "2026-11-25", "14:00", 3, "Agendada", 450.0, "Voz e violão - single"),
            (2, 2, "2026-11-26", "19:00", 2, "Agendada", 120.0, "Ensaio para show"),
            (3, 3, "2026-11-10", "10:00", 4, "Concluída", 800.0, "Mixagem do EP"),
        ],
    )
