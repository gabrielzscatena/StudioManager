"""As 11 interfaces gráficas (UI) do StudioManager."""
import os
import re
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

import banco
import config
import servicos
from ui_base import Campo, Tela, TelaCrud, criar_tabela, COR_DESTAQUE


def brl(v):
    return f"R$ {v or 0:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ============================================================ UI 1 - LOGIN
class TelaLogin(Tela):
    titulo = "🎚  StudioManager"
    mostra_voltar = False

    def montar(self, corpo):
        caixa = ttk.Frame(corpo, style="Painel.TFrame", padding=30)
        caixa.place(relx=0.5, rely=0.45, anchor="center")
        ttk.Label(caixa, text="Acesso ao sistema", style="Painel.TLabel",
                  font=("Segoe UI", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 4))
        ttk.Label(caixa, text=config.TEMA, style="Painel.TLabel").grid(
            row=1, column=0, columnspan=2, pady=(0, 16))
        ttk.Label(caixa, text="Usuário", style="Painel.TLabel").grid(row=2, column=0, sticky="w")
        self.ent_user = ttk.Entry(caixa, width=28)
        self.ent_user.grid(row=2, column=1, pady=5)
        ttk.Label(caixa, text="Senha", style="Painel.TLabel").grid(row=3, column=0, sticky="w")
        self.ent_senha = ttk.Entry(caixa, width=28, show="•")
        self.ent_senha.grid(row=3, column=1, pady=5)
        ttk.Button(caixa, text="Entrar", style="Destaque.TButton", command=self.entrar).grid(
            row=4, column=0, columnspan=2, sticky="we", pady=(14, 0))
        ttk.Label(caixa, text="Padrão: admin / admin123", style="Painel.TLabel",
                  foreground="#9a9ab0").grid(row=5, column=0, columnspan=2, pady=(10, 0))
        self.ent_user.focus_set()
        self.ent_senha.bind("<Return>", lambda e: self.entrar())
        self.ent_user.bind("<Return>", lambda e: self.ent_senha.focus_set())

    def entrar(self):
        u, s = self.ent_user.get(), self.ent_senha.get()
        if not u or not s:
            messagebox.showwarning("Login", "Informe usuário e senha.", parent=self)
            return
        usuario = banco.autenticar(u, s)
        if not usuario:
            messagebox.showerror("Login", "Usuário ou senha inválidos.", parent=self)
            self.ent_senha.delete(0, "end")
            return
        self.app.usuario = usuario
        self.app.mostrar_menu()


# ============================================================ UI 2 - MENU
class TelaMenu(Tela):
    titulo = "Menu Principal"
    mostra_voltar = False

    def montar(self, corpo):
        ttk.Label(corpo, text=f"Bem-vindo(a), {self.app.usuario['nome']}! Escolha uma opção:",
                  style="Sub.TLabel").pack(anchor="w", pady=(0, 14))
        grade = ttk.Frame(corpo)
        grade.pack(fill="both", expand=True)
        opcoes = [
            ("🎤  Artistas / Clientes", TelaArtistas),
            ("🎛  Salas e Equipamentos", TelaSalas),
            ("📅  Sessões de Gravação", TelaSessoes),
            ("📊  Relatórios", TelaRelatorios),
            ("🌐  Importar da Web", TelaImportar),
            ("🎵  Referências Musicais", TelaReferencias),
            ("📦  Exportar Dados (JSON/ZIP)", TelaExportar),
            ("👥  Usuários", TelaUsuarios),
            ("ℹ  Sobre", TelaSobre),
        ]
        for i, (texto, classe) in enumerate(opcoes):
            ttk.Button(grade, text=texto, style="Menu.TButton",
                       command=lambda c=classe: self.app.mostrar(c)).grid(
                row=i // 3, column=i % 3, sticky="nsew", padx=6, pady=6)
        for c in range(3):
            grade.columnconfigure(c, weight=1)
        for r in range(3):
            grade.rowconfigure(r, weight=1)
        ttk.Button(corpo, text="Sair (logout)", command=self.app.logout).pack(anchor="e", pady=(12, 0))


# ============================================================ UI 3 - SOBRE
class TelaSobre(Tela):
    titulo = "Sobre"

    def montar(self, corpo):
        def bloco(titulo, texto):
            lf = ttk.LabelFrame(corpo, text=titulo, padding=12)
            lf.pack(fill="x", pady=6)
            ttk.Label(lf, text=texto, wraplength=820, justify="left").pack(anchor="w")

        bloco("Projeto", f"{config.APP_NOME}\n{config.INSTITUICAO}\n{config.DISCIPLINA}")
        bloco("Tema escolhido", config.TEMA)
        bloco("Objetivo", config.OBJETIVO)
        devs = ttk.LabelFrame(corpo, text="Desenvolvedores", padding=12)
        devs.pack(fill="x", pady=6)
        for nome, matricula in config.DESENVOLVEDORES:
            ttk.Label(devs, text=f"• {nome}   —   Matrícula: {matricula}",
                      font=("Segoe UI", 11, "bold")).pack(anchor="w")
        bloco("Tecnologias", "Python 3 • Tkinter (UI) • SQLite (SGBD) • urllib (importação web) "
                             "• json + zipfile (exportação)")


# ============================================================ UI 4 - USUÁRIOS
class TelaUsuarios(TelaCrud):
    titulo = "Usuários do Sistema"
    tabela = "usuarios"
    campos = [
        Campo("nome", "Nome completo", obrigatorio=True),
        Campo("usuario", "Login", obrigatorio=True),
        Campo("senha", "Senha", tipo="senha"),
        Campo("perfil", "Perfil", tipo="combo", opcoes=["Administrador", "Operador"], obrigatorio=True),
    ]
    colunas = [("id", "ID", 50), ("nome", "Nome", 220), ("usuario", "Login", 140), ("perfil", "Perfil", 120)]
    sql_lista = "SELECT id, nome, usuario, perfil FROM usuarios"
    colunas_busca = ["nome", "usuario", "perfil"]

    def antes_salvar(self, v):
        senha = v.pop("senha")
        if self.id_atual is None and len(senha) < 4:
            raise ValueError("Informe uma senha com pelo menos 4 caracteres.")
        if senha:
            if len(senha) < 4:
                raise ValueError("A senha deve ter pelo menos 4 caracteres.")
            v["senha_hash"] = banco.hash_senha(senha)  # em edição, senha vazia mantém a atual
        return v

    def antes_excluir(self, id_):
        if id_ == self.app.usuario["id"]:
            messagebox.showwarning("Excluir", "Você não pode excluir o próprio usuário logado.", parent=self)
            return False
        return True


# ============================================================ UI 5 - ARTISTAS
class TelaArtistas(TelaCrud):
    titulo = "Artistas / Clientes"
    tabela = "artistas"
    campos = [
        Campo("nome", "Nome", obrigatorio=True),
        Campo("nome_artistico", "Nome artístico"),
        Campo("genero", "Gênero musical", tipo="combo",
              opcoes=["MPB", "Rock", "Pop", "Rap", "Sertanejo", "Samba", "Eletrônica", "Gospel", "Jazz", "Outro"]),
        Campo("telefone", "Telefone"),
        Campo("email", "E-mail"),
    ]
    colunas = [("id", "ID", 45), ("nome", "Nome", 170), ("nome_artistico", "Nome artístico", 140),
               ("genero", "Gênero", 90), ("telefone", "Telefone", 120), ("email", "E-mail", 180)]
    sql_lista = "SELECT * FROM artistas"
    colunas_busca = ["nome", "nome_artistico", "genero", "email"]

    def antes_salvar(self, v):
        if v["email"] and not re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+$", v["email"]):
            raise ValueError("E-mail inválido.")
        return v


# ============================================================ UI 6 - SALAS
class TelaSalas(TelaCrud):
    titulo = "Salas e Equipamentos"
    tabela = "salas"
    campos = [
        Campo("nome", "Nome da sala", obrigatorio=True),
        Campo("tipo", "Tipo", tipo="combo", obrigatorio=True,
              opcoes=["Gravação", "Ensaio", "Mixagem/Masterização", "Podcast"]),
        Campo("valor_hora", "Valor/hora (R$)", tipo="numero", obrigatorio=True),
        Campo("equipamentos", "Equipamentos"),
    ]
    colunas = [("id", "ID", 45), ("nome", "Sala", 180), ("tipo", "Tipo", 150),
               ("valor_hora", "Valor/hora", 100), ("equipamentos", "Equipamentos", 300)]
    sql_lista = "SELECT * FROM salas"
    colunas_busca = ["nome", "tipo", "equipamentos"]

    def antes_salvar(self, v):
        if v["valor_hora"] <= 0:
            raise ValueError("O valor/hora deve ser maior que zero.")
        return v


# ============================================================ UI 7 - SESSÕES
def _opcoes_artistas():
    return [(r["id"], r["nome_artistico"] or r["nome"]) for r in banco.consultar(
        "SELECT id, nome, nome_artistico FROM artistas ORDER BY nome")]


def _opcoes_salas():
    return [(r["id"], f"{r['nome']} ({brl(r['valor_hora'])}/h)") for r in banco.consultar(
        "SELECT id, nome, valor_hora FROM salas ORDER BY nome")]


def _minutos(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


class TelaSessoes(TelaCrud):
    titulo = "Sessões de Gravação"
    tabela = "sessoes"
    campos = [
        Campo("artista_id", "Artista", tipo="fk", opcoes=_opcoes_artistas, obrigatorio=True),
        Campo("sala_id", "Sala", tipo="fk", opcoes=_opcoes_salas, obrigatorio=True),
        Campo("data", "Data (AAAA-MM-DD)", obrigatorio=True),
        Campo("hora_inicio", "Hora início (HH:MM)", obrigatorio=True),
        Campo("duracao_horas", "Duração (horas)", tipo="numero", obrigatorio=True),
        Campo("status", "Status", tipo="combo", obrigatorio=True,
              opcoes=["Agendada", "Em andamento", "Concluída", "Cancelada"]),
        Campo("observacoes", "Observações"),
    ]
    colunas = [("id", "ID", 40), ("data", "Data", 90), ("hora_inicio", "Início", 60),
               ("artista", "Artista", 130), ("sala", "Sala", 150), ("duracao_horas", "Horas", 50),
               ("status", "Status", 90), ("valor_total", "Valor", 95), ("observacoes", "Obs.", 160)]
    sql_lista = ("SELECT s.*, COALESCE(a.nome_artistico, a.nome) AS artista, sa.nome AS sala "
                 "FROM sessoes s JOIN artistas a ON a.id = s.artista_id JOIN salas sa ON sa.id = s.sala_id")
    colunas_busca = ["artista", "sala", "status", "data", "observacoes"]
    ordem = "data DESC, hora_inicio DESC"

    def antes_salvar(self, v):
        try:
            datetime.strptime(v["data"], "%Y-%m-%d")
            datetime.strptime(v["hora_inicio"], "%H:%M")
        except ValueError:
            raise ValueError("Data deve estar no formato AAAA-MM-DD e hora no formato HH:MM.")
        if not 0 < v["duracao_horas"] <= 24:
            raise ValueError("A duração deve estar entre 0 e 24 horas.")
        # conflito de horário na mesma sala
        ini = _minutos(v["hora_inicio"])
        fim = ini + v["duracao_horas"] * 60
        if v["status"] != "Cancelada":
            outras = banco.consultar(
                "SELECT id, hora_inicio, duracao_horas FROM sessoes "
                "WHERE sala_id = ? AND data = ? AND status <> 'Cancelada' AND id <> ?",
                (v["sala_id"], v["data"], self.id_atual or -1))
            for o in outras:
                oi = _minutos(o["hora_inicio"])
                if ini < oi + o["duracao_horas"] * 60 and oi < fim:
                    raise ValueError(f"Conflito de horário com a sessão ID {o['id']} nesta sala.")
        # valor calculado automaticamente
        valor_hora = banco.consultar("SELECT valor_hora FROM salas WHERE id = ?", (v["sala_id"],))[0]["valor_hora"]
        v["valor_total"] = round(valor_hora * v["duracao_horas"], 2)
        return v


# ============================================================ UI 8 - RELATÓRIOS
class TelaRelatorios(Tela):
    titulo = "Relatórios e Indicadores"

    def montar(self, corpo):
        r = banco.consultar("""
            SELECT (SELECT COUNT(*) FROM artistas) artistas,
                   (SELECT COUNT(*) FROM salas) salas,
                   (SELECT COUNT(*) FROM sessoes WHERE status = 'Agendada') agendadas,
                   (SELECT COALESCE(SUM(valor_total),0) FROM sessoes WHERE status = 'Concluída') faturado,
                   (SELECT COALESCE(SUM(valor_total),0) FROM sessoes WHERE status IN ('Agendada','Em andamento')) previsto
        """)[0]
        cards = ttk.Frame(corpo)
        cards.pack(fill="x", pady=(0, 12))
        for i, (rot, val) in enumerate([("Artistas", r["artistas"]), ("Salas", r["salas"]),
                                        ("Sessões agendadas", r["agendadas"]),
                                        ("Faturado (concluídas)", brl(r["faturado"])),
                                        ("Receita prevista", brl(r["previsto"]))]):
            c = ttk.Frame(cards, style="Painel.TFrame", padding=12)
            c.grid(row=0, column=i, sticky="nsew", padx=4)
            cards.columnconfigure(i, weight=1)
            ttk.Label(c, text=rot, style="Painel.TLabel").pack(anchor="w")
            ttk.Label(c, text=str(val), style="Painel.TLabel", foreground=COR_DESTAQUE,
                      font=("Segoe UI", 16, "bold")).pack(anchor="w")

        meio = ttk.Frame(corpo)
        meio.pack(fill="both", expand=True)
        lf1 = ttk.LabelFrame(meio, text="Receita por sala (exceto canceladas)", padding=8)
        lf1.pack(side="left", fill="both", expand=True, padx=(0, 6))
        f, t = criar_tabela(lf1, [("sala", "Sala", 180), ("qtd", "Sessões", 70),
                                  ("horas", "Horas", 60), ("total", "Total", 110)], altura=8)
        f.pack(fill="both", expand=True)
        for l in banco.consultar(
                "SELECT sa.nome sala, COUNT(s.id) qtd, COALESCE(SUM(s.duracao_horas),0) horas, "
                "COALESCE(SUM(s.valor_total),0) total FROM salas sa LEFT JOIN sessoes s "
                "ON s.sala_id = sa.id AND s.status <> 'Cancelada' GROUP BY sa.id ORDER BY total DESC"):
            t.insert("", "end", values=(l["sala"], l["qtd"], l["horas"], brl(l["total"])))

        lf2 = ttk.LabelFrame(meio, text="Ranking de artistas", padding=8)
        lf2.pack(side="left", fill="both", expand=True, padx=(6, 0))
        f, t = criar_tabela(lf2, [("artista", "Artista", 180), ("qtd", "Sessões", 70),
                                  ("total", "Total", 110)], altura=8)
        f.pack(fill="both", expand=True)
        for l in banco.consultar(
                "SELECT COALESCE(a.nome_artistico, a.nome) artista, COUNT(s.id) qtd, "
                "COALESCE(SUM(s.valor_total),0) total FROM artistas a LEFT JOIN sessoes s "
                "ON s.artista_id = a.id AND s.status <> 'Cancelada' GROUP BY a.id ORDER BY total DESC"):
            t.insert("", "end", values=(l["artista"], l["qtd"], brl(l["total"])))

        lf3 = ttk.LabelFrame(corpo, text="Próximas sessões", padding=8)
        lf3.pack(fill="both", expand=True, pady=(12, 0))
        f, t = criar_tabela(lf3, [("data", "Data", 100), ("hora", "Início", 70), ("artista", "Artista", 180),
                                  ("sala", "Sala", 180), ("horas", "Horas", 60)], altura=6)
        f.pack(fill="both", expand=True)
        for l in banco.consultar(
                "SELECT s.data, s.hora_inicio, COALESCE(a.nome_artistico,a.nome) artista, sa.nome sala, "
                "s.duracao_horas FROM sessoes s JOIN artistas a ON a.id=s.artista_id "
                "JOIN salas sa ON sa.id=s.sala_id WHERE s.status='Agendada' AND s.data >= date('now','localtime') "
                "ORDER BY s.data, s.hora_inicio LIMIT 20"):
            t.insert("", "end", values=(l["data"], l["hora_inicio"], l["artista"], l["sala"], l["duracao_horas"]))


# ============================================================ UI 9 - EXPORTAR
class TelaExportar(Tela):
    titulo = "Exportar Dados (JSON compactado em ZIP)"

    def montar(self, corpo):
        ttk.Label(corpo, text="Exporta TODAS as tabelas do sistema para um único arquivo JSON, "
                              "compactado no formato .zip.", style="Sub.TLabel").pack(anchor="w")
        bts = ttk.Frame(corpo)
        bts.pack(anchor="w", pady=12)
        ttk.Button(bts, text="Exportar para a pasta 'exportacoes'", style="Destaque.TButton",
                   command=lambda: self.exportar(None)).pack(side="left")
        ttk.Button(bts, text="Exportar e escolher local…", command=self.escolher).pack(side="left", padx=8)
        self.btn_abrir = ttk.Button(bts, text="Abrir pasta", command=self.abrir_pasta, state="disabled")
        self.btn_abrir.pack(side="left")
        self.saida = tk.Text(corpo, height=18, bg="#11111b", fg="#e6e6f0", font=("Consolas", 10),
                             relief="flat", padx=10, pady=10)
        self.saida.pack(fill="both", expand=True)
        self.ultimo = None

    def escolher(self):
        caminho = filedialog.asksaveasfilename(
            parent=self, defaultextension=".zip", filetypes=[("Arquivo ZIP", "*.zip")],
            initialfile=f"backup_estudio_{datetime.now():%Y%m%d_%H%M%S}.zip")
        if caminho:
            self.exportar(caminho)

    def exportar(self, destino):
        try:
            caminho, contagem = servicos.exportar_zip(destino)
        except OSError as e:
            messagebox.showerror("Exportar", f"Falha ao exportar:\n{e}", parent=self)
            return
        self.ultimo = caminho
        self.btn_abrir.config(state="normal")
        linhas = [f"✔ Exportação concluída em {datetime.now():%d/%m/%Y %H:%M:%S}",
                  f"Arquivo: {caminho}", ""] + [f"  {t:<12} {n:>5} registro(s)" for t, n in contagem.items()]
        self.saida.insert("end", "\n".join(linhas) + "\n\n")
        self.saida.see("end")

    def abrir_pasta(self):
        if self.ultimo:
            os.startfile(os.path.dirname(self.ultimo))


# ============================================================ UI 10 - IMPORTAR DA WEB
class TelaImportar(Tela):
    titulo = "Importar Referências Musicais da Web"

    def montar(self, corpo):
        lf = ttk.LabelFrame(corpo, text="Origem dos dados (urllib)", padding=10)
        lf.pack(fill="x")
        self.origem = tk.StringVar(value="itunes")
        ttk.Radiobutton(lf, text="API pública do iTunes (internet)", variable=self.origem, value="itunes",
                        command=self.trocar_origem).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(lf, text="Servidor web local do projeto (offline)", variable=self.origem,
                        value="local", command=self.trocar_origem).grid(row=0, column=1, sticky="w", padx=20)
        ttk.Label(lf, text="URL:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.ent_url = ttk.Entry(lf, width=100)
        self.ent_url.grid(row=2, column=0, columnspan=3, sticky="we")
        ttk.Label(lf, text="Termo de busca ({termo}):").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.ent_termo = ttk.Entry(lf, width=40)
        self.ent_termo.insert(0, "bossa nova")
        self.ent_termo.grid(row=4, column=0, sticky="w")
        bts = ttk.Frame(lf)
        bts.grid(row=4, column=1, columnspan=2, sticky="e")
        ttk.Button(bts, text="1. Buscar dados", command=self.buscar).pack(side="left", padx=4)
        ttk.Button(bts, text="2. Salvar no banco", style="Destaque.TButton",
                   command=self.salvar).pack(side="left")
        lf.columnconfigure(2, weight=1)
        self.trocar_origem()

        self.lbl = ttk.Label(corpo, text="Nenhum dado carregado.", style="Sub.TLabel")
        self.lbl.pack(anchor="w", pady=(10, 4))
        f, self.tree = criar_tabela(corpo, [("faixa", "Faixa", 220), ("artista", "Artista", 180),
                                            ("album", "Álbum", 200), ("genero", "Gênero", 100),
                                            ("duracao", "Duração", 70)], altura=14)
        f.pack(fill="both", expand=True)
        self.itens = []

    def trocar_origem(self):
        self.ent_url.delete(0, "end")
        if self.origem.get() == "itunes":
            self.ent_url.insert(0, config.URL_ITUNES)
        else:
            self.ent_url.insert(0, servicos.iniciar_servidor_local())

    def buscar(self):
        url = servicos.montar_url(self.ent_url.get().strip(), self.ent_termo.get().strip())
        self.config(cursor="watch")
        self.update_idletasks()
        try:
            dados = servicos.baixar_json(url)
            self.itens = servicos.normalizar(dados, origem=url.split("?")[0])
        except Exception as e:
            messagebox.showerror("Importar", f"Não foi possível obter os dados de:\n{url}\n\n{e}", parent=self)
            return
        finally:
            self.config(cursor="")
        self.tree.delete(*self.tree.get_children())
        for i in self.itens:
            self.tree.insert("", "end", values=(i["faixa"], i["artista"], i["album"], i["genero"], i["duracao"]))
        self.lbl.config(text=f"{len(self.itens)} item(ns) obtido(s) de {url}")

    def salvar(self):
        if not self.itens:
            messagebox.showwarning("Importar", "Busque os dados primeiro.", parent=self)
            return
        novos = servicos.salvar_referencias(self.itens)
        if messagebox.askyesno("Importar", f"{novos} nova(s) referência(s) gravada(s) na tabela "
                                           f"'referencias' ({len(self.itens) - novos} já existiam).\n\n"
                                           "Abrir a tela de Referências Musicais?", parent=self):
            self.app.mostrar(TelaReferencias)


# ============================================================ UI 11 - REFERÊNCIAS (dados importados)
class TelaReferencias(TelaCrud):
    titulo = "Referências Musicais (dados importados)"
    tabela = "referencias"
    campos = [
        Campo("faixa", "Faixa", obrigatorio=True),
        Campo("artista", "Artista"),
        Campo("album", "Álbum"),
        Campo("genero", "Gênero"),
        Campo("duracao", "Duração"),
        Campo("preview_url", "URL de prévia"),
        Campo("origem", "Origem"),
    ]
    colunas = [("id", "ID", 40), ("faixa", "Faixa", 190), ("artista", "Artista", 150), ("album", "Álbum", 160),
               ("genero", "Gênero", 90), ("duracao", "Dur.", 50), ("importado_em", "Importado em", 130)]
    sql_lista = "SELECT * FROM referencias"
    colunas_busca = ["faixa", "artista", "album", "genero"]

    def montar(self, corpo):
        super().montar(corpo)
        ttk.Button(self.form, text="▶ Ouvir prévia", command=self.ouvir).grid(
            row=len(self.campos) + 2, column=0, columnspan=2, sticky="we", pady=(10, 0))

    def ouvir(self):
        url = self.widgets["preview_url"].get().strip()
        if url.startswith("http"):
            webbrowser.open(url)
        else:
            messagebox.showinfo("Prévia", "Selecione uma referência que tenha URL de prévia.", parent=self)
