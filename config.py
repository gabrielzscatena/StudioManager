"""Configurações gerais do projeto (edite os dados dos desenvolvedores aqui)."""

APP_NOME = "StudioManager"
TEMA = "Gestão de Estúdio de Produção Musical"
OBJETIVO = (
    "Gerenciar as operações de um estúdio de produção musical: cadastro de "
    "artistas/clientes, salas e equipamentos, agendamento de sessões de "
    "gravação com cálculo automático de valores, relatórios de faturamento, "
    "exportação completa dos dados em JSON compactado (ZIP) e importação de "
    "referências musicais a partir de um endereço da web."
)

# >>> PREENCHA com os dados reais (nome completo e código de matrícula) <<<
DESENVOLVEDORES = [
    ("Tulio Purcineli Fusco", "2840482411020"),
    ("Gabriel Zuchi Scatena", "2840482411023"),
]

INSTITUICAO = "Fatec Ribeirão Preto - Análise e Desenvolvimento de Sistemas"
DISCIPLINA = "Tópicos Especiais em Informática - Prova B2 (2/2026)"

# Importação web
URL_ITUNES = "https://itunes.apple.com/search?media=music&entity=song&limit=25&term={termo}"
PORTA_SERVIDOR_LOCAL = 8765
