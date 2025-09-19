from typer.testing import CliRunner
import traceback
from src.cli.main import app


def run():
    runner = CliRunner()
    res = runner.invoke(app, ["fix-folder", "tests/fixtures"])
    print("exit_code:", res.exit_code)
    print(res.output)
    if res.exception:
        traceback.print_exception(
            type(res.exception), res.exception, res.exception.__traceback__)


if __name__ == '__main__':
    run()
