# StudioManager: Gestão de Estúdio de Produção Musical

Integrantes: Gabriel Scatena e Tulio Fusco
Projeto prático da disciplina Tópicos Especiais em Informática (Fatec Ribeirão Preto, Prova B2).

Usa **somente a biblioteca padrão do Python 3**. Não precisa de `pip install` nem de banco de dados externo.

## Como executar

```bash
python main.py
```

**Login padrão:** `admin` / `admin123`

O banco `estudio.db` (SQLite) é criado automaticamente na primeira execução, já com dados de exemplo.

## Atendimento aos requisitos

| Requisito | Onde está |
|---|---|
| **≥ 10 UIs** (formulários Tkinter) | 11 telas em `telas.py`: Login, Menu, Sobre, Usuários, Artistas, Salas, Sessões, Relatórios, Exportar, Importar da Web, Referências Musicais |
| **Login** com usuário e senha cadastrados | `TelaLogin`. Senhas guardadas com hash PBKDF2-SHA256 (`banco.py`) |
| **Sobre** (tema, objetivo, nome e matrícula) | `TelaSobre`. Os dados ficam em `config.py` |
| **Menu** | `TelaMenu` |
| **SGBD com ≥ 3 tabelas** | SQLite com 5 tabelas: `usuarios`, `artistas`, `salas`, `sessoes`, `referencias` |
| **≥ 3 operações por tabela** | Todas as tabelas têm **Insert, Update, Delete e Select (com busca)** pela UI (`TelaCrud` em `ui_base.py`) |
| **Exportação JSON compactada em ZIP** | Tela *Exportar*, `servicos.exportar_zip()` (`json` + `zipfile`). Salva em `exportacoes/` ou no local escolhido |
| **Importação de endereço web com urllib** | Tela *Importar da Web*, `servicos.baixar_json()` (`urllib.request`) |
| Dados importados **gravados em tabela** | Tabela `referencias` |
| Dados importados **exibidos numa UI** | Tela *Referências Musicais* |

### Fontes da importação

1. **API pública do iTunes** (precisa de internet):
   `https://itunes.apple.com/search?media=music&entity=song&limit=25&term={termo}`
2. **Servidor web local** (funciona sem internet): o app sobe um servidor HTTP embutido (`http.server`) em
   `http://127.0.0.1:8765/referencias.json`, que publica o arquivo `dados_web/referencias.json`.
   Use essa opção na apresentação caso a rede da sala falhe.

## Regras de negócio

- O valor da sessão é calculado automaticamente (valor/hora da sala × duração).
- O sistema bloqueia conflito de horário na mesma sala, exceto para sessões canceladas.
- Não é possível excluir um artista ou sala que tenha sessões vinculadas (integridade referencial).
- Ninguém consegue excluir o próprio usuário logado. Ao editar um usuário, deixar a senha em branco mantém a senha atual.
- O hash das senhas nunca vai para o arquivo exportado.

## Estrutura

```
main.py        # inicialização e navegação entre telas
config.py      # tema, objetivo, desenvolvedores, URLs
banco.py       # SQLite: schema, conexão, autenticação, dados de exemplo
servicos.py    # exportação JSON/ZIP, importação via urllib, servidor web local
ui_base.py     # estilos, tela base e tela CRUD genérica
telas.py       # as 11 interfaces
dados_web/     # JSON publicado pelo servidor local
```
