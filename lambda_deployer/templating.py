import pathlib

from jinja2 import Environment
import lambda_deployer

_environment = Environment()


def render(location: str, **kwargs) -> str:
    """Loads a template from the path and returns the rendered contents."""
    contents = (
        pathlib.Path(lambda_deployer.__file__)
        .parent
        .joinpath(*location.strip('/').split('/'))
        .read_text()
    )
    return _environment.from_string(contents).render(**kwargs)


def printer(location: str, **kwargs):
    """Renders the template and prints it to stdout."""
    print(render(location, **kwargs))
