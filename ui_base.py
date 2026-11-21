"""Componentes reutilizáveis de interface (Tkinter): Tela base e Tela CRUD genérica."""
import sqlite3
import tkinter as tk
from dataclasses import dataclass, field
from tkinter import messagebox, ttk
from typing import Callable, Optional

import banco

COR_FUNDO = "#1e1e2e"
COR_PAINEL = "#2a2a3d"
COR_TEXTO = "#e6e6f0"
COR_DESTAQUE = "#f5a623"


def configurar_estilos(root):
    st = ttk.Style(root)
    st.theme_use("clam")
    st.configure(".", background=COR_FUNDO, foreground=COR_TEXTO, fieldbackground="#ffffff",
                 font=("Segoe UI", 10))
    st.configure("TLabel", background=COR_FUNDO, foreground=COR_TEXTO)
    st.configure("Titulo.TLabel", font=("Segoe UI", 18, "bold"), foreground=COR_DESTAQUE)
    st.configure("Sub.TLabel", font=("Segoe UI", 11), foreground="#b8b8c8")
    st.configure("Painel.TFrame", background=COR_PAINEL)
    st.configure("Painel.TLabel", background=COR_PAINEL, foreground=COR_TEXTO)
    st.configure("TLabelframe", background=COR_FUNDO, foreground=COR_DESTAQUE)
    st.configure("TLabelframe.Label", background=COR_FUNDO, foreground=COR_DESTAQUE,
                 font=("Segoe UI", 10, "bold"))
    st.configure("TButton", padding=6, background="#3b3b55", foreground=COR_TEXTO)
    st.map("TButton", background=[("active", "#50506e")])
    st.configure("Destaque.TButton", background=COR_DESTAQUE, foreground="#1e1e2e",
                 font=("Segoe UI", 10, "bold"))
    st.map("Destaque.TButton", background=[("active", "#ffbf4d")])
    st.configure("Menu.TButton", padding=14, font=("Segoe UI", 11, "bold"))
    st.configure("Treeview", background="#ffffff", foreground="#222", rowheight=24,
                 fieldbackground="#ffffff")
    st.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
    st.configure("TEntry", foreground="#222")
    st.configure("TCombobox", foreground="#222")
    st.map("TCombobox", fieldbackground=[("readonly", "#ffffff")], foreground=[("readonly", "#222")])


class Tela(ttk.Frame):
    """Tela base: cabeçalho com título e botão de voltar ao menu."""
    titulo = "Tela"
    mostra_voltar = True

    def __init__(self, master, app):
        super().__init__(master, padding=16)
        self.app = app
        topo = ttk.Frame(self)
        topo.pack(fill="x", pady=(0, 10))
        ttk.Label(topo, text=self.titulo, style="Titulo.TLabel").pack(side="left")
        if self.mostra_voltar:
            ttk.Button(topo, text="⟵ Menu", command=app.mostrar_menu).pack(side="right")
        if app.usuario:
            ttk.Label(topo, text=f"👤 {app.usuario['nome']}  ", style="Sub.TLabel").pack(side="right")
        self.corpo = ttk.Frame(self)
        self.corpo.pack(fill="both", expand=True)
        self.montar(self.corpo)

    def montar(self, corpo):
        raise NotImplementedError


def criar_tabela(parent, colunas, altura=12):
    """Cria um Treeview com barra de rolagem. colunas = [(chave, título, largura)]."""
    frame = ttk.Frame(parent)
    tree = ttk.Treeview(frame, columns=[c[0] for c in colunas], show="headings", height=altura)
    for chave, titulo, largura in colunas:
        tree.heading(chave, text=titulo)
        tree.column(chave, width=largura, anchor="w")
    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    return frame, tree


@dataclass
class Campo:
    nome: str
    rotulo: str
    tipo: str = "texto"           # texto | numero | inteiro | combo | fk | senha
    opcoes: object = None          # lista (combo) ou função -> [(id, rótulo)] (fk)
    obrigatorio: bool = False


class TelaCrud(Tela):
    """Tela genérica com formulário + tabela: Inserir, Atualizar, Excluir e Consultar."""
    tabela = ""
    campos: list = []
    colunas: list = []             # [(chave, título, largura)]
    sql_lista = ""                 # SELECT usado na listagem (pode ter JOIN)
    colunas_busca: list = []       # colunas usadas no filtro de busca (LIKE)
    ordem = "id DESC"

    def montar(self, corpo):
        self.id_atual = None
        self.widgets = {}

        form = self.form = ttk.LabelFrame(corpo, text="Cadastro", padding=10)
        form.pack(side="left", fill="y", padx=(0, 12))
        for i, c in enumerate(self.campos):
            ttk.Label(form, text=c.rotulo + (" *" if c.obrigatorio else "")).grid(
                row=i, column=0, sticky="w", pady=3)
            if c.tipo in ("combo", "fk"):
                w = ttk.Combobox(form, width=30, state="readonly")
            else:
                w = ttk.Entry(form, width=33, show="•" if c.tipo == "senha" else "")
            w.grid(row=i, column=1, sticky="we", pady=3, padx=(6, 0))
            self.widgets[c.nome] = w
        self._recarregar_opcoes()

        bts = ttk.Frame(form)
        bts.grid(row=len(self.campos), column=0, columnspan=2, pady=(12, 0), sticky="we")
        ttk.Button(bts, text="Novo", command=self.limpar).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(bts, text="Salvar", style="Destaque.TButton", command=self.salvar).pack(
            side="left", expand=True, fill="x", padx=2)
        ttk.Button(bts, text="Excluir", command=self.excluir).pack(side="left", expand=True, fill="x", padx=2)
        self.lbl_modo = ttk.Label(form, text="Modo: inclusão", style="Sub.TLabel")
        self.lbl_modo.grid(row=len(self.campos) + 1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        direita = ttk.Frame(corpo)
        direita.pack(side="left", fill="both", expand=True)
        busca = ttk.Frame(direita)
        busca.pack(fill="x", pady=(0, 6))
        ttk.Label(busca, text="Buscar:").pack(side="left")
        self.ent_busca = ttk.Entry(busca)
        self.ent_busca.pack(side="left", fill="x", expand=True, padx=6)
        self.ent_busca.bind("<Return>", lambda e: self.listar())
        ttk.Button(busca, text="Consultar", command=self.listar).pack(side="left")
        ttk.Button(busca, text="Limpar", command=lambda: (self.ent_busca.delete(0, "end"), self.listar())
                   ).pack(side="left", padx=(4, 0))

        frame_tab, self.tree = criar_tabela(direita, self.colunas, altura=18)
        frame_tab.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.selecionar)
        self.lbl_total = ttk.Label(direita, text="", style="Sub.TLabel")
        self.lbl_total.pack(anchor="w", pady=(4, 0))
        self.listar()

    # ------------------------------------------------------------ helpers
    def _recarregar_opcoes(self):
        for c in self.campos:
            w = self.widgets[c.nome]
            if c.tipo == "combo":
                w["values"] = c.opcoes
            elif c.tipo == "fk":
                w["values"] = [f"{i} - {r}" for i, r in c.opcoes()]

    def _ler_form(self):
        valores = {}
        for c in self.campos:
            bruto = self.widgets[c.nome].get().strip()
            if c.obrigatorio and not bruto:
                raise ValueError(f"O campo '{c.rotulo}' é obrigatório.")
            if c.tipo == "fk":
                valores[c.nome] = int(bruto.split(" - ")[0]) if bruto else None
            elif c.tipo == "numero":
                try:
                    valores[c.nome] = float(bruto.replace(",", ".")) if bruto else None
                except ValueError:
                    raise ValueError(f"'{c.rotulo}' deve ser numérico.")
            elif c.tipo == "inteiro":
                try:
                    valores[c.nome] = int(bruto) if bruto else None
                except ValueError:
                    raise ValueError(f"'{c.rotulo}' deve ser um número inteiro.")
            else:
                valores[c.nome] = bruto
        return valores

    def antes_salvar(self, valores):
        """Gancho para validações / campos calculados. Retorna o dict final."""
        return valores

    def antes_excluir(self, id_):
        return True

    # ------------------------------------------------------------ operações
    def listar(self):  # SELECT
        termo = self.ent_busca.get().strip()
        sql, params = self.sql_lista, []
        if termo and self.colunas_busca:
            filtro = " OR ".join(f"CAST({c} AS TEXT) LIKE ?" for c in self.colunas_busca)
            sql = f"SELECT * FROM ({sql}) WHERE {filtro}"
            params = [f"%{termo}%"] * len(self.colunas_busca)
        sql += f" ORDER BY {self.ordem}"
        self.tree.delete(*self.tree.get_children())
        linhas = banco.consultar(sql, params)
        for l in linhas:
            self.tree.insert("", "end", iid=str(l["id"]),
                             values=[self.formatar(k, l.get(k)) for k, _, _ in self.colunas])
        self.lbl_total.config(text=f"{len(linhas)} registro(s)")

    def formatar(self, chave, valor):
        if valor is None:
            return ""
        if isinstance(valor, float) and chave.startswith("valor"):
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return valor

    def selecionar(self, _=None):
        sel = self.tree.selection()
        if not sel:
            return
        self.id_atual = int(sel[0])
        reg = banco.consultar(f"SELECT * FROM {self.tabela} WHERE id = ?", (self.id_atual,))[0]
        for c in self.campos:
            w = self.widgets[c.nome]
            v = reg.get(c.nome)
            if c.tipo == "fk":
                opc = [x for x in w["values"] if x.split(" - ")[0] == str(v)]
                w.set(opc[0] if opc else "")
            elif c.tipo == "combo":
                w.set(v or "")
            else:
                w.delete(0, "end")
                w.insert(0, "" if v is None else str(v))
        self.lbl_modo.config(text=f"Modo: edição (ID {self.id_atual})")

    def limpar(self):
        self.id_atual = None
        for w in self.widgets.values():
            if isinstance(w, ttk.Combobox):
                w.set("")
            else:
                w.delete(0, "end")
        self.tree.selection_remove(self.tree.selection())
        self._recarregar_opcoes()
        self.lbl_modo.config(text="Modo: inclusão")

    def salvar(self):  # INSERT / UPDATE
        try:
            valores = self.antes_salvar(self._ler_form())
            cols = list(valores.keys())
            if self.id_atual is None:
                sql = (f"INSERT INTO {self.tabela} ({', '.join(cols)}) "
                       f"VALUES ({', '.join('?' * len(cols))})")
                banco.executar(sql, [valores[c] for c in cols])
                msg = "Registro incluído com sucesso."
            else:
                sql = f"UPDATE {self.tabela} SET {', '.join(f'{c} = ?' for c in cols)} WHERE id = ?"
                banco.executar(sql, [valores[c] for c in cols] + [self.id_atual])
                msg = "Registro atualizado com sucesso."
        except ValueError as e:
            messagebox.showwarning("Validação", str(e), parent=self)
            return
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Erro de integridade", f"Não foi possível salvar:\n{e}", parent=self)
            return
        messagebox.showinfo("Sucesso", msg, parent=self)
        self.limpar()
        self.listar()

    def excluir(self):  # DELETE
        if self.id_atual is None:
            messagebox.showwarning("Excluir", "Selecione um registro na tabela.", parent=self)
            return
        if not self.antes_excluir(self.id_atual):
            return
        if not messagebox.askyesno("Confirmar", f"Excluir o registro ID {self.id_atual}?", parent=self):
            return
        try:
            banco.executar(f"DELETE FROM {self.tabela} WHERE id = ?", (self.id_atual,))
        except sqlite3.IntegrityError:
            messagebox.showerror("Não permitido",
                                 "Este registro está vinculado a outros dados (ex.: sessões) "
                                 "e não pode ser excluído.", parent=self)
            return
        self.limpar()
        self.listar()
