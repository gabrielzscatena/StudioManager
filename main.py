"""StudioManager - Gestão de Estúdio de Produção Musical.

Executar:  python main.py
Login padrão: admin / admin123
"""
import tkinter as tk

import banco
import config
from ui_base import COR_FUNDO, configurar_estilos


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{config.APP_NOME} - {config.TEMA}")
        self.geometry("1150x700")
        self.minsize(1000, 620)
        self.configure(bg=COR_FUNDO)
        configurar_estilos(self)
        self.usuario = None
        self.tela_atual = None
        from telas import TelaLogin
        self.mostrar(TelaLogin)

    def mostrar(self, classe_tela):
        if self.tela_atual is not None:
            self.tela_atual.destroy()
        self.tela_atual = classe_tela(self, self)
        self.tela_atual.pack(fill="both", expand=True)

    def mostrar_menu(self):
        from telas import TelaMenu
        self.mostrar(TelaMenu)

    def logout(self):
        from telas import TelaLogin
        self.usuario = None
        self.mostrar(TelaLogin)


if __name__ == "__main__":
    banco.inicializar()
    App().mainloop()
