import click

from taretto.scripting.application import main as app_main
from taretto.scripting.ipyshell import main as shell_main
from taretto.scripting.tests import main as tests_main


@click.group()
def cli():
    pass


cli.add_command(app_main, name="application")
cli.add_command(tests_main, name="tests")

if __name__ == "__main__":
    cli()
