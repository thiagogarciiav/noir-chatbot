"""
ui.py - Camada visual do Noir: tema noturno minimalista, banner e painéis.
"""


from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme


NOIR_THEME = Theme (
    {
        "noir.brand": "bold #8be9fd",
        "noir.accent": "#bd93f9",
        "noir.dim": "#6272a4",
        "noir.user": "bold #f8f8f2",
        "noir.error": "bold #ff5555",
        "noir.success": "#50fa7b",
        "noir.system": "italic #6272a4"        
    }
)

console = Console(theme=NOIR_THEME)

BANNER = r"""
███╗   ██╗ ██████╗ ██╗██████╗ 
████╗  ██║██╔═══██╗██║██╔══██╗
██╔██╗ ██║██║   ██║██║██████╔╝
██║╚██╗██║██║   ██║██║██╔══██╗
██║ ╚████║╚██████╔╝██║██║  ██║
╚═╝  ╚═══╝ ╚═════╝ ╚═╝╚═╝  ╚═╝
"""


def mostrar_banner(apelido: str, modelo: str) -> None:
    """Limpa a tela e mostra o cabeçalho minimalista do Noir."""
    console.clear()
    console.print(Align.center(f"[noir.brand]{BANNER}[/noir.brand]"))
    console.print(Align.center("[noir.dim]seu parceiro de código nas sombras[/noir.dim]"))
    console.print()
    info = (
        f"[noir.dim]Olá, [noir.accent]{apelido}[/noir.accent]"
        f" · modelo: {modelo} · digite [noir.accent]/ajuda[/noir.accent] para comandos[/noir.dim]"
    )
    console.print(Align.center(info))
    console.print()


def painel_erro(mensagem: str) -> None:
    console.print(
        Panel(mensagem, title="[noir.error]erro[/noir.error]", border_style="noir.error", box=box.ROUNDED)
    )


def painel_sistema(mensagem: str) -> None:
    console.print(f"[noir.system]{mensagem}[/noir.system]")