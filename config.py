"""
config.py - Configuração persistente do Noir.

Guarda apelido do usuário, modelo da OpenAI e temperatura em um JSON local 
(noir_config.json), para que suas preferências sejam lembradas entre execuções.
"""


import json
from dataclasses import dataclass, asdict
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "noir_config.json"

DEFAULTS = {
    "apelido_usuario": "Dev",
    "modelo": "gpt-4o-mini",
    "temperatura": 0.4,
    "max_tokens": 10000,
}


@dataclass
class NoirConfig:
    apelido_usuario: str = DEFAULTS["apelido_usuario"]
    modelo: str = DEFAULTS["modelo"]
    temperatura: str = DEFAULTS["temperatura"]
    max_tokens: int = DEFAULTS["max_tokens"]

    @classmethod
    def carregar(cls) -> "NoirConfig":
        """Lê o arquivo de configuração do disco, ou retorna os padrões."""
        if CONFIG_PATH.exists():
            try:
                dados = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                mesclado = {**DEFAULTS, **dados}
                return cls(
                    apelido_usuario = mesclado.get("apelido_usuario", DEFAULTS["apelido_usuario"]),
                    modelo = mesclado.get("modelo", DEFAULTS["modelo"]),
                    temperatura = mesclado.get("temperatura", DEFAULTS["temperatura"]),
                    max_tokens=int(mesclado.get("max_tokens", DEFAULTS["max_tokens"])),
                )
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        return cls()

    def salvar(self) -> None:
        """Grava a configuração atual no disco em formato JSON legível."""
        CONFIG_PATH.write_text(
            json.dumps(
                asdict(self), indent=2, ensure_ascii=False),
                  encoding="utf-8",
        )
        