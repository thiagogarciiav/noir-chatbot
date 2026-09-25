#!/usr/bin/env python3
"""
noir_popup.py — Noir em uma janela de desktop flutuante (sem terminal).

Reaproveita a mesma configuração (noir_config.json) do noir.py (CLI).

Uso:
    python noir_popup.py
"""

import os
import queue
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path

import customtkinter as ctk
from dotenv import load_dotenv
from openai import OpenAI, APIError, APIConnectionError, RateLimitError

from config import NoirConfig, CONFIG_PATH
from ui import BANNER

COR_FUNDO = "#1e1f29"
COR_FUNDO_CHAT = "#181920"
COR_BARRA = "#15161d"
COR_BRAND = "#8be9fd"
COR_ACCENT = "#bd93f9"
COR_TEXTO = "#f8f8f2"
COR_DIM = "#6272a4"
COR_ERRO = "#ff5555"

SYSTEM_PROMPT_TEMPLATE = """Você é Noir, um assistente de programação direto, preciso e gentil.
Você ajuda {apelido} a escrever, revisar, depurar e entender código.
Responda sempre em português do Brasil, seja objetivo, use blocos de código ```linguagem
quando fizer sentido, explique decisões técnicas relevantes e assuma que {apelido}
é uma pessoa desenvolvedora experiente — não simplifique conceitos básicos
a menos que seja pedido."""

TEXTO_AJUDA = (
    "/apelido X   muda como o Noir te chama\n"
    "/modelo X    troca o modelo da OpenAI (ex: gpt-4o, gpt-4o-mini)\n"
    "/tokens X    define o máximo de tokens de resposta (ex: 10000)\n"
    "/limpar      limpa o histórico da conversa\n"
    "/salvar      salva a conversa em conversas_noir/*.md\n"
    "/ajuda       mostra esta lista\n"
)

ctk.set_appearance_mode("dark")


class JanelaNoir(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self._resposta_em_andamento = False
        self._arrasto = {"x": 0, "y": 0}
        self.sempre_no_topo = True
        self.fila_resposta: "queue.Queue" = queue.Queue()

        self._montar_janela()

        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        self._sem_api_key = not bool(api_key)
        self.client = OpenAI(api_key=api_key) if api_key else None

        if not CONFIG_PATH.exists():
            dialog = ctk.CTkInputDialog(
                text="Como você quer que o Noir te chame?", title="Bem-vindo ao Noir"
            )
            apelido = dialog.get_input()
            NoirConfig(apelido_usuario=(apelido or "Dev").strip() or "Dev").salvar()

        self.config_noir = NoirConfig.carregar()
        self.historico: list[dict] = []
        self._resetar_historico()

        self._montar_widgets()

        if self._sem_api_key:
            self._adicionar_mensagem(
                "erro",
                "OPENAI_API_KEY não encontrada. Crie um .env (veja .env.example) e reinicie o app.",
            )

        self.entrada.focus_set()
        self.after(80, self._processar_fila)

    def _montar_janela(self) -> None:
        self.overrideredirect(True)
        self.attributes("-topmost", self.sempre_no_topo)
        self.configure(fg_color=COR_FUNDO)
        largura, altura = 420, 560
        x = self.winfo_screenwidth() - largura - 40
        y = self.winfo_screenheight() - altura - 80
        self.geometry(f"{largura}x{altura}+{x}+{y}")
        self.minsize(340, 420)

    def _montar_widgets(self) -> None:
        barra = ctk.CTkFrame(self, fg_color=COR_BARRA, height=36, corner_radius=0)
        barra.pack(fill="x", side="top")
        barra.bind("<ButtonPress-1>", self._iniciar_arrasto)
        barra.bind("<B1-Motion>", self._arrastar)

        titulo = ctk.CTkLabel(
            barra, text="●  NOIR", text_color=COR_BRAND,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        titulo.pack(side="left", padx=12)
        titulo.bind("<ButtonPress-1>", self._iniciar_arrasto)
        titulo.bind("<B1-Motion>", self._arrastar)

        ctk.CTkButton(
            barra, text="✕", width=28, height=24, fg_color="transparent",
            hover_color="#3a1f22", text_color=COR_DIM, command=self.destroy,
        ).pack(side="right", padx=6)

        self.btn_pin = ctk.CTkButton(
            barra, text="📌", width=28, height=24, fg_color="transparent",
            hover_color="#2a2b38", text_color=COR_ACCENT, command=self._alternar_topo,
        )
        self.btn_pin.pack(side="right")

        self.chat = tk.Text(
            self, bg=COR_FUNDO_CHAT, fg=COR_TEXTO, insertbackground=COR_TEXTO,
            font=("Consolas", 11), wrap="word", relief="flat",
            padx=10, pady=8, borderwidth=0, highlightthickness=0,
        )
        self.chat.pack(fill="both", expand=True, padx=10, pady=(10, 6))
        self.chat.tag_config("noir", foreground=COR_BRAND, font=("Consolas", 11, "bold"))
        self.chat.tag_config("usuario", foreground=COR_TEXTO, font=("Consolas", 11, "bold"))
        self.chat.tag_config("sistema", foreground=COR_DIM)
        self.chat.tag_config("erro", foreground=COR_ERRO)
        self.chat.tag_config("banner", foreground=COR_BRAND)
        self.chat.insert("end", BANNER.strip("\n") + "\n\n", "banner")
        self.chat.configure(state="disabled")

        self.rotulo_status = ctk.CTkLabel(
            self, text=self._texto_status(), text_color=COR_DIM,
            font=ctk.CTkFont(size=11), anchor="w",
        )
        self.rotulo_status.pack(fill="x", padx=14)

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", padx=10, pady=10)

        self.entrada = ctk.CTkEntry(
            rodape, placeholder_text="Digite sua mensagem ou /ajuda...",
            fg_color=COR_FUNDO_CHAT, text_color=COR_TEXTO,
            border_color=COR_ACCENT, corner_radius=8,
        )
        self.entrada.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.entrada.bind("<Return>", lambda _evt: self._enviar())

        self.btn_enviar = ctk.CTkButton(
            rodape, text="Enviar", width=70, fg_color=COR_ACCENT,
            hover_color="#a67ef0", text_color="#1e1f29", command=self._enviar,
        )
        self.btn_enviar.pack(side="right")

        self._adicionar_mensagem("sistema", "seu parceiro de código nas sombras — digite /ajuda para ver os comandos.")

    def _texto_status(self) -> str:
        return f"{self.config_noir.apelido_usuario} · {self.config_noir.modelo}"

    def _iniciar_arrasto(self, evento) -> None:
        self._arrasto = {"x": evento.x, "y": evento.y}

    def _arrastar(self, evento) -> None:
        x = self.winfo_x() + evento.x - self._arrasto["x"]
        y = self.winfo_y() + evento.y - self._arrasto["y"]
        self.geometry(f"+{x}+{y}")

    def _alternar_topo(self) -> None:
        self.sempre_no_topo = not self.sempre_no_topo
        self.attributes("-topmost", self.sempre_no_topo)
        self.btn_pin.configure(text_color=COR_ACCENT if self.sempre_no_topo else COR_DIM)

    def _resetar_historico(self) -> None:
        self.historico = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT_TEMPLATE.format(apelido=self.config_noir.apelido_usuario),
            }
        ]

    def _adicionar_mensagem(self, remetente: str, texto: str) -> None:
        self.chat.configure(state="normal")
        if remetente == "usuario":
            self.chat.insert("end", f"{self.config_noir.apelido_usuario}: ", "usuario")
            self.chat.insert("end", f"{texto}\n\n")
        elif remetente == "erro":
            self.chat.insert("end", f"{texto}\n\n", "erro")
        else:
            self.chat.insert("end", f"{texto}\n\n", "sistema")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _chat_delta(self, texto: str) -> None:
        self.chat.configure(state="normal")
        if not self._resposta_em_andamento:
            self.chat.insert("end", "Noir: ", "noir")
            self._resposta_em_andamento = True
        self.chat.insert("end", texto)
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _chat_finalizar_resposta(self) -> None:
        if self._resposta_em_andamento:
            self.chat.configure(state="normal")
            self.chat.insert("end", "\n\n")
            self.chat.configure(state="disabled")
            self.chat.see("end")
        self._resposta_em_andamento = False

    def _enviar(self) -> None:
        if self.btn_enviar.cget("state") == "disabled":
            return
        texto = self.entrada.get().strip()
        if not texto:
            return
        self.entrada.delete(0, "end")

        if texto.startswith("/"):
            self._tratar_comando(texto)
            return

        if not self.client:
            self._adicionar_mensagem("erro", "Sem OPENAI_API_KEY configurada — não é possível conversar.")
            return

        self._adicionar_mensagem("usuario", texto)
        self.historico.append({"role": "user", "content": texto})
        self.btn_enviar.configure(state="disabled")
        self.entrada.configure(state="disabled")
        threading.Thread(target=self._chamar_api, daemon=True).start()

    def _tratar_comando(self, entrada: str) -> None:
        partes = entrada.split(maxsplit=1)
        comando = partes[0].lower()
        argumento = partes[1].strip() if len(partes) > 1 else ""

        if comando == "/ajuda":
            self._adicionar_mensagem("sistema", TEXTO_AJUDA)
        elif comando == "/apelido":
            if not argumento:
                self._adicionar_mensagem("erro", "Uso: /apelido <novo nome>")
                return
            self.config_noir.apelido_usuario = argumento
            self.config_noir.salvar()
            self._resetar_historico()
            self.rotulo_status.configure(text=self._texto_status())
            self._adicionar_mensagem("sistema", f"Combinado. Vou te chamar de {argumento}.")
        elif comando == "/modelo":
            if not argumento:
                self._adicionar_mensagem("sistema", f"Modelo atual: {self.config_noir.modelo}")
                return
            self.config_noir.modelo = argumento
            self.config_noir.salvar()
            self.rotulo_status.configure(text=self._texto_status())
            self._adicionar_mensagem("sistema", f"Modelo alterado para {argumento}.")
        elif comando == "/tokens":
            if not argumento:
                self._adicionar_mensagem("sistema", f"Máximo de tokens atual: {self.config_noir.max_tokens}")
                return
            try:
                novo_valor = int(argumento)
            except ValueError:
                self._adicionar_mensagem("erro", "Uso: /tokens <número inteiro>, ex: /tokens 6000")
                return
            self.config_noir.max_tokens = novo_valor
            self.config_noir.salvar()
            self._adicionar_mensagem("sistema", f"Máximo de tokens alterado para {novo_valor}.")
        elif comando == "/limpar":
            self._resetar_historico()
            self.chat.configure(state="normal")
            self.chat.delete("1.0", "end")
            self.chat.configure(state="disabled")
            self._adicionar_mensagem("sistema", "Histórico limpo.")
        elif comando == "/salvar":
            caminho = self._salvar_conversa()
            self._adicionar_mensagem("sistema", f"Conversa salva em {caminho}")
        else:
            self._adicionar_mensagem("erro", f"Comando desconhecido: {comando}")

    def _chamar_api(self) -> None:
        try:
            stream = self.client.chat.completions.create(
                model=self.config_noir.modelo,
                messages=self.historico,
                temperature=self.config_noir.temperatura,
                max_tokens=self.config_noir.max_tokens,
                stream=True,
            )
            conteudo_completo = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    conteudo_completo += delta
                    self.fila_resposta.put(("delta", delta))
            self.historico.append({"role": "assistant", "content": conteudo_completo})
            self.fila_resposta.put(("fim", None))
        except RateLimitError as erro:
            self.historico.pop()
            self.fila_resposta.put((
                "erro",
                "Limite de requisições/cota da OpenAI atingido. Se isso aconteceu na "
                "primeira mensagem, provavelmente falta crédito ou forma de pagamento "
                "cadastrada na conta OpenAI (não é limite de velocidade). Confira "
                f"platform.openai.com/settings/organization/billing.\nDetalhe: {erro}"
            ))
        except APIConnectionError:
            self.historico.pop()
            self.fila_resposta.put(("erro", "Não foi possível conectar à API da OpenAI. Verifique sua internet."))
        except APIError as erro:
            self.historico.pop()
            self.fila_resposta.put(("erro", f"Erro da API da OpenAI: {erro}"))

    def _processar_fila(self) -> None:
        try:
            while True:
                tipo, dado = self.fila_resposta.get_nowait()
                if tipo == "delta":
                    self._chat_delta(dado)
                elif tipo == "fim":
                    self._chat_finalizar_resposta()
                    self.btn_enviar.configure(state="normal")
                    self.entrada.configure(state="normal")
                elif tipo == "erro":
                    self._chat_finalizar_resposta()
                    self._adicionar_mensagem("erro", dado)
                    self.btn_enviar.configure(state="normal")
                    self.entrada.configure(state="normal")
        except queue.Empty:
            pass
        self.after(80, self._processar_fila)

    def _salvar_conversa(self) -> Path:
        pasta = Path("conversas_noir")
        pasta.mkdir(exist_ok=True)
        nome_arquivo = f"conversa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        caminho = pasta / nome_arquivo

        linhas = [f"# Conversa com Noir — {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"]
        for msg in self.historico:
            if msg["role"] == "system":
                continue
            autor = self.config_noir.apelido_usuario if msg["role"] == "user" else "Noir"
            linhas.append(f"**{autor}:**\n\n{msg['content']}\n")

        caminho.write_text("\n".join(linhas), encoding="utf-8")
        return caminho


if __name__ == "__main__":
    app = JanelaNoir()
    app.mainloop()