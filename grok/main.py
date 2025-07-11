# grok/main.py
import click
from prompt_toolkit import PromptSession
from .agent import agent_loop
from .config import get_api_key
from .slash_commands import handle_slash_command

session = PromptSession()

@click.command()
@click.option('--mode', help='Set mode: default, auto-complete, planning')
@click.option('-p', '--print', is_flag=True, help='Print response and exit')
@click.argument('prompt', required=False)
def cli(mode, print, prompt):
    if mode:
        set_mode(mode)
    
    api_key = get_api_key()
    if not api_key:
        print("No API key found. Use /login in REPL.")
        handle_slash_command('/login', [])
    
    if print and prompt:
        # Non-interactive
        response = call_api([{"role": "user", "content": prompt}])
        print(response.choices[0].message.content)
    else:
        agent_loop(initial_prompt=prompt)

if __name__ == '__main__':
    cli()