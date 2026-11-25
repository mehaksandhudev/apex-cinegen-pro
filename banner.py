"""
APEX CINEGEN — Autonomous Generative Video & Publishing Engine
Architected & Developed by Mehak Sandhu (@mehaksandhudev)
"""

import sys

def print_creator_terminal_banner(project_name: str = "APEX CINEGEN — AUTONOMOUS REVENUE ENGINE"):
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
            
    gold = "\033[1;33m"
    cyan = "\033[1;36m"
    green = "\033[1;32m"
    reset = "\033[0m"
    bold = "\033[1m"
    
    print(f"""
{gold}================================================================================{reset}
{cyan}  █████╗ ██████╗ ███████╗██╗  ██╗    ██████╗██╗███╗   ██╗███████╗ ██████╗ {reset}
{cyan} ██╔══██╗██╔══██╗██╔════╝╚██╗██╔╝   ██╔════╝██║████╗  ██║██╔════╝██╔════╝ {reset}
{cyan} ███████║██████╔╝█████╗   ╚███╔╝    ██║     ██║██╔██╗ ██║█████╗  ██║  ███╗{reset}
{cyan} ██╔══██║██╔═══╝ ██╔══╝   ██╔██╗    ██║     ██║██║╚██╗██║██╔══╝  ██║   ██║{reset}
{cyan} ██║  ██║██║     ███████╗██╔╝ ██╗   ╚██████╗██║██║ ╚████║███████╗╚██████╔╝{reset}
{cyan} ╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝    ╚═════╝╚═╝╚═╝  ╚═══╝╚══════╝ ╚═════╝ {reset}
{gold}--------------------------------------------------------------------------------{reset}
  👑 {bold}LEAD ARCHITECT & DEVELOPER{reset} : {gold}MEHAK SANDHU{reset} ({cyan}@mehaksandhudev{reset})
  🌐 {bold}OFFICIAL REPOSITORY{reset}        : {cyan}https://github.com/mehaksandhudev{reset}
  🎬 {bold}AUTONOMOUS STUDIO{reset}          : {bold}{project_name}{reset}
  ⚡ {bold}NEURAL PIPELINE{reset}            : Google Flow 8K • Gemini 2.5 Flash • ChatGPT
{gold}================================================================================{reset}
""")

if __name__ == "__main__":
    print_creator_terminal_banner()
