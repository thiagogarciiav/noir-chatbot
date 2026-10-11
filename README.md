# Noir

Assistente de programação para o terminal, com tema noturno minimalista e
respostas via API da OpenAI. Direto, preciso, sem rodeios — o Noir prefere
as sombras do terminal à luz do dia.

> "resolvendo bugs nas sombras, uma linha de cada vez"

## Recursos

- **Tema noturno minimalista**: paleta discreta (ciano, roxo suave, cinza-azulado),
  pensada para terminais escuros.
- **Streaming de respostas**: o texto vai aparecendo em tempo real, com blocos
  de código já formatados via Markdown.
- **Apelido personalizável**: você escolhe como o Noir te chama, a qualquer momento.
- **Modelo configurável**: troque entre `gpt-4o`, `gpt-4o-mini` etc. sem editar código.
- **Histórico exportável**: salve qualquer conversa em `.md` com um comando.
- **Configuração persistente**: suas preferências ficam salvas localmente entre execuções.

## Estrutura do projeto

```
noir/
├── noir.py             # entrada CLI — loop do chat no terminal
├── noir_gui.py          # entrada GUI — janela de desktop flutuante (sem terminal)
├── config.py            # carregamento/gravação da configuração (apelido, modelo)
├── ui.py                 # tema visual, banner e painéis do modo CLI (rich)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Modo janela flutuante (GUI)

Além do terminal, o Noir também roda como uma janela de desktop flutuante,
sem barra de título do sistema — nos moldes de um widget:

```bash
python noir_gui.py
```

- **Arrastar**: clique e arraste pela barra escura no topo (onde está "NOIR").
- **📌 fixar/soltar**: alterna se a janela fica sempre por cima das outras.
- **✕**: fecha a janela.
- Os mesmos comandos do terminal funcionam na caixa de mensagem: `/apelido`,
  `/modelo`, `/limpar`, `/salvar`, `/ajuda`.
- Compartilha o mesmo `noir_config.json` do modo CLI — o apelido e o modelo
  valem para os dois.

Por não ter barra de título nativa, essa janela não aparece na barra de
tarefas do Windows; se ela ficar "perdida" atrás de outra janela, use o
📌 para garantir que fique sempre visível.

## Instalação

1. Clone ou copie a pasta do projeto e entre nela:

   ```bash
   cd noir
   ```

2. Crie e ative um ambiente virtual (recomendado):

   ```bash
   python -m venv venv
   source venv/bin/activate      # Linux/macOS
   venv\Scripts\activate         # Windows
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure sua chave da OpenAI:

   ```bash
   cp .env.example .env
   ```

   Abra o `.env` e substitua pelo valor real:

   ```
   OPENAI_API_KEY=sk-...
   ```

## Uso

```bash
python noir.py
```

Na primeira execução, o Noir pergunta como você quer ser chamado. Essa
preferência (e o modelo escolhido) fica salva em `noir_config.json`, na
mesma pasta do projeto — não é preciso repetir a cada execução.

## Comandos disponíveis no chat

| Comando         | O que faz                                              |
|-----------------|---------------------------------------------------------|
| `/ajuda`        | mostra a lista de comandos                              |
| `/apelido X`    | muda como o Noir te chama para "X"                       |
| `/modelo X`     | troca o modelo da OpenAI usado (ex: `gpt-4o`, `gpt-4o-mini`) |
| `/tokens X`     | define o máximo de tokens de resposta (padrão: 6000)     |
| `/limpar`       | limpa o histórico da conversa atual                      |
| `/salvar`       | salva a conversa atual em `conversas_noir/*.md`          |
| `/sair`         | encerra o Noir                                           |

## Personalização

- **Cores do tema**: edite o dicionário `NOIR_THEME` em `ui.py`.
- **Banner**: a arte ASCII fica em `BANNER`, também em `ui.py`.
- **Personalidade / idioma das respostas**: ajuste `SYSTEM_PROMPT_TEMPLATE`
  em `noir.py` — é o prompt de sistema enviado à API a cada conversa.
- **Modelo, temperatura e máximo de tokens padrão**: em `config.py`, no dicionário `DEFAULTS`.

## Observações

- `noir_config.json` e `.env` ficam de fora do controle de versão
  (veja `.gitignore`) porque guardam preferências e segredos locais.
- O comando `/salvar` cria a pasta `conversas_noir/` na primeira vez que é usado.

## Contribuição

- Se você quiser contribuir para este projeto, fique à vontade para fazer um fork, criar um branch e enviar um pull request com suas melhorias.

## Autor

Este projeto foi desenvolvido por **Thiago Garcia**.