#!/usr/bin/env python3
"""
Noir — assistente de programação para o terminal, com tema noturno minimalista.

Uso:
    python noir.py
"""

import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
import os

from openai import OpenAI, APIError, APIConnectionError, RateLimitError
from rich import box
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from config import NoirConfig, CONFIG_PATH
from ui import console, mostrar_banner, painel_erro, painel_sistema

SYSTEM_PROMPT_TEMPLATE = """Você é Noir, um assistente de programação direto, preciso e gentil.
Você ajuda {apelido} a escrever, revisar, depurar e entender código.
Responda sempre em português do Brasil, seja objetivo, use blocos de código ```linguagem
quando fizer sentido, explique decisões técnicas relevantes e assuma que {apelido}
é uma pessoa desenvolvedora experiente — não simplifique conceitos básicos
a menos que seja pedido."""

TEXTO_AJUDA = """[noir.accent]/ajuda[/noir.accent]         mostra esta lista de comandos
[noir.accent]/apelido X[/noir.accent]     muda como o Noir te chama para "X"
[noir.accent]/modelo X[/noir.accent]      troca o modelo da OpenAI usado (ex: gpt-4o, gpt-4o-mini)
[noir.accent]/tokens X[/noir.accent]      define o máximo de tokens de resposta (ex: 6000)
[noir.accent]/limpar[/noir.accent]        limpa o histórico da conversa atual
[noir.accent]/salvar[/noir.accent]        salva a conversa atual em um arquivo .md
[noir.accent]/sair[/noir.accent]          encerra o Noir"""


class Noir:
    def __init__(self) -> None:
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            painel_erro(
                "Variável OPENAI_API_KEY não encontrada.\n"
                "Copie .env.example para .env e coloque sua chave da OpenAI lá dentro."
            )
            sys.exit(1)

        self.client = OpenAI(api_key=api_key)
        self.config = NoirConfig.carregar()
        self.historico: list[dict] = []
        self._resetar_historico()

    def _resetar_historico(self) -> None:
        self.historico = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT_TEMPLATE.format(apelido=self.config.apelido_usuario),
            }
        ]

    def executar(self) -> None:
        mostrar_banner(self.config.apelido_usuario, self.config.modelo)
        while True:
            try:
                entrada = Prompt.ask(f"[noir.user]{self.config.apelido_usuario}[/noir.user]")
            except (KeyboardInterrupt, EOFError):
                console.print()
                painel_sistema("Até mais.")
                break

            entrada = entrada.strip()
            if not entrada:
                continue

            if entrada.startswith("/"):
                if self._tratar_comando(entrada):
                    break
                continue

            self._enviar_mensagem(entrada)

    def _tratar_comando(self, entrada: str) -> bool:
        """Processa um comando iniciado com '/'. Retorna True se deve encerrar o app."""
        partes = entrada.split(maxsplit=1)
        comando = partes[0].lower()
        argumento = partes[1].strip() if len(partes) > 1 else ""

        if comando == "/sair":
            painel_sistema("Até mais.")
            return True

        if comando == "/ajuda":
            console.print(
                Panel(TEXTO_AJUDA, title="[noir.brand]comandos[/noir.brand]",
                      border_style="noir.dim", box=box.ROUNDED)
            )
            return False

        if comando == "/apelido":
            if not argumento:
                painel_erro("Uso: /apelido <novo nome>")
                return False
            self.config.apelido_usuario = argumento
            self.config.salvar()
            self._resetar_historico()
            painel_sistema(f"Combinado. Vou te chamar de {argumento} a partir de agora.")
            return False

        if comando == "/modelo":
            if not argumento:
                painel_sistema(f"Modelo atual: {self.config.modelo}")
                return False
            self.config.modelo = argumento
            self.config.salvar()
            painel_sistema(f"Modelo alterado para {argumento}.")
            return False

        if comando == "/tokens":
            if not argumento:
                painel_sistema(f"Máximo de tokens atual: {self.config.max_tokens}")
                return False
            try:
                novo_valor = int(argumento)
            except ValueError:
                painel_erro("Uso: /tokens <número inteiro>, ex: /tokens 6000")
                return False
            self.config.max_tokens = novo_valor
            self.config.salvar()
            painel_sistema(f"Máximo de tokens alterado para {novo_valor}.")
            return False

        if comando == "/limpar":
            self._resetar_historico()
            mostrar_banner(self.config.apelido_usuario, self.config.modelo)
            painel_sistema("Histórico limpo.")
            return False

        if comando == "/salvar":
            caminho = self._salvar_conversa()
            painel_sistema(f"Conversa salva em {caminho}")
            return False

        painel_erro(f"Comando desconhecido: {comando}. Digite /ajuda para ver a lista.")
        return False

    def _enviar_mensagem(self, texto: str) -> None:
        self.historico.append({"role": "user", "content": texto})
        conteudo_completo = ""

        try:
            stream = self.client.chat.completions.create(
                model=self.config.modelo,
                messages=self.historico,
                temperature=self.config.temperatura,
                max_tokens=self.config.max_tokens,
                stream=True,
            )

            with Live(console=console, refresh_per_second=12) as live:
                live.update(self._painel_resposta("[noir.dim]pensando...[/noir.dim]"))
                for chunk in stream:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        conteudo_completo += delta
                        live.update(self._painel_resposta(Markdown(conteudo_completo)))

        except RateLimitError as erro:
            painel_erro(
                "Limite de requisições/cota da OpenAI atingido.\n"
                "Se isso aconteceu na primeira mensagem, provavelmente é falta de crédito "
                "ou de forma de pagamento cadastrada na conta da OpenAI — não é \"muitas "
                "mensagens por minuto\". Confira em "
                "platform.openai.com/settings/organization/billing.\n"
                f"Detalhe da OpenAI: {erro}"
            )
            self.historico.pop()
            return
        except APIConnectionError:
            painel_erro("Não foi possível conectar à API da OpenAI. Verifique sua internet.")
            self.historico.pop()
            return
        except APIError as erro:
            painel_erro(f"Erro da API da OpenAI: {erro}")
            self.historico.pop()
            return

        self.historico.append({"role": "assistant", "content": conteudo_completo})

    @staticmethod
    def _painel_resposta(conteudo) -> Panel:
        return Panel(
            conteudo,
            title="[noir.brand]Noir[/noir.brand]",
            title_align="left",
            border_style="noir.accent",
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def _salvar_conversa(self) -> Path:
        pasta = Path("conversas_noir")
        pasta.mkdir(exist_ok=True)
        nome_arquivo = f"conversa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        caminho = pasta / nome_arquivo

        linhas = [f"# Conversa com Noir — {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"]
        for msg in self.historico:
            if msg["role"] == "system":
                continue
            autor = self.config.apelido_usuario if msg["role"] == "user" else "Noir"
            linhas.append(f"**{autor}:**\n\n{msg['content']}\n")

        caminho.write_text("\n".join(linhas), encoding="utf-8")
        return caminho


def primeira_execucao_se_necessario() -> None:
    """Na primeiríssima execução, pergunta o apelido antes de abrir o chat."""
    if not CONFIG_PATH.exists():
        console.print("[noir.accent]Primeira vez por aqui.[/noir.accent]")
        apelido = Prompt.ask(
            "[noir.dim]Como você quer que o Noir te chame?[/noir.dim]", default="Dev"
        )
        NoirConfig(apelido_usuario=apelido.strip() or "Dev").salvar()


if __name__ == "__main__":
    primeira_execucao_se_necessario()
    Noir().executar()