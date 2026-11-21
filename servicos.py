"""Exportação (JSON + ZIP) e importação de dados da web (urllib)."""
import functools
import json
import threading
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import banco
from config import PORTA_SERVIDOR_LOCAL

EXPORT_DIR = banco.BASE_DIR / "exportacoes"
DADOS_WEB_DIR = banco.BASE_DIR / "dados_web"


# ================================================================ EXPORTAÇÃO
def exportar_zip(destino=None):
    """Exporta todas as tabelas para um JSON e compacta em .zip.
    Retorna (caminho_zip, {tabela: quantidade})."""
    dados = {}
    for tabela in banco.TABELAS:
        linhas = banco.consultar(f"SELECT * FROM {tabela}")
        if tabela == "usuarios":  # nunca exporta o hash da senha
            for l in linhas:
                l.pop("senha_hash", None)
        dados[tabela] = linhas

    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    documento = {
        "aplicacao": "StudioManager - Gestão de Estúdio de Produção Musical",
        "exportado_em": datetime.now().isoformat(timespec="seconds"),
        "tabelas": dados,
    }
    if destino is None:
        EXPORT_DIR.mkdir(exist_ok=True)
        destino = EXPORT_DIR / f"backup_estudio_{carimbo}.zip"

    with zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"estudio_{carimbo}.json", json.dumps(documento, ensure_ascii=False, indent=2))
    return str(destino), {t: len(v) for t, v in dados.items()}


# ================================================================ IMPORTAÇÃO
def montar_url(url, termo=""):
    return url.replace("{termo}", urllib.parse.quote_plus(termo or "music"))


def baixar_json(url, timeout=15):
    """Baixa um JSON de um endereço web usando urllib."""
    req = urllib.request.Request(url, headers={"User-Agent": "StudioManager/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _ms_para_min(ms):
    try:
        s = int(ms) // 1000
        return f"{s // 60}:{s % 60:02d}"
    except (TypeError, ValueError):
        return ""


def normalizar(dados, origem):
    """Aceita o formato da API do iTunes ({results:[...]}) ou uma lista simples."""
    itens = dados.get("results", dados.get("referencias", [])) if isinstance(dados, dict) else dados
    saida = []
    for i in itens:
        faixa = i.get("trackName") or i.get("faixa")
        if not faixa:
            continue
        saida.append({
            "faixa": faixa,
            "artista": i.get("artistName") or i.get("artista", ""),
            "album": i.get("collectionName") or i.get("album", ""),
            "genero": i.get("primaryGenreName") or i.get("genero", ""),
            "duracao": _ms_para_min(i["trackTimeMillis"]) if "trackTimeMillis" in i else i.get("duracao", ""),
            "preview_url": i.get("previewUrl") or i.get("preview_url", ""),
            "origem": origem,
        })
    return saida


def salvar_referencias(itens):
    """Grava os itens importados na tabela 'referencias' (ignora duplicados)."""
    antes = banco.consultar("SELECT COUNT(*) n FROM referencias")[0]["n"]
    banco.executar_varios(
        "INSERT OR IGNORE INTO referencias (faixa, artista, album, genero, duracao, preview_url, origem)"
        " VALUES (:faixa, :artista, :album, :genero, :duracao, :preview_url, :origem)",
        itens,
    )
    depois = banco.consultar("SELECT COUNT(*) n FROM referencias")[0]["n"]
    return depois - antes


# ================================================================ SERVIDOR WEB LOCAL
_servidor = None


class _HandlerSilencioso(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def iniciar_servidor_local():
    """Publica a pasta dados_web/ em http://127.0.0.1:PORTA (alternativa offline)."""
    global _servidor
    if _servidor is None:
        handler = functools.partial(_HandlerSilencioso, directory=str(DADOS_WEB_DIR))
        _servidor = ThreadingHTTPServer(("127.0.0.1", PORTA_SERVIDOR_LOCAL), handler)
        threading.Thread(target=_servidor.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{PORTA_SERVIDOR_LOCAL}/referencias.json"
