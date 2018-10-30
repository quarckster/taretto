import click
from cookiecutter.exceptions import OutputDirExistsException
from cookiecutter.main import cookiecutter


@click.group(help="Helper commands for application installation")
def main():
    """Main application group"""
    pass


@click.option("--path", default=".", help="Path to create the new application in")
@main.command("create", help="Makes a skeleton of a new application")
def make_application(path):
    print(
        "Git initialize is required for application to work, select 'y' at 'initialize_git' "
        "prompt to run this automatically."
    )
    try:
        # TODO
        plugin_path = cookiecutter(str(DATA_PATH / "application_skel"), output_dir=path)
        print("Application created at {}".format(plugin_path))
    except OutputDirExistsException:
        print("Output dir already exists, application create failed")
