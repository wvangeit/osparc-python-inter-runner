import json
import logging
import os
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("osparc-python-inter-runner-prepare")

INPUT_1 = Path(os.environ["DY_SIDECAR_PATH_INPUTS"])  # TODO: this is wrong ...
main_script_path = Path("main.sh")


def _find_user_code_entrypoint(code_dir: Path) -> Path:
    logger.info("Searching for script main entrypoint ...")
    code_files = list(code_dir.rglob("*.py"))

    if not code_files:
        raise ValueError(
            f"No python scripts found in user-provided directory: {code_dir}")

    if len(code_files) > 1:
        code_files = list(code_dir.rglob("main.py"))
        if not code_files:
            raise ValueError("No main.py found in user-provided directory")
        if len(code_files) > 1:
            raise ValueError(f"Multiple main python files found"
                             " in user-provided directory,"
                             "I don't know which one to run: {code_files}")

    main_py = code_files[0]
    logger.info("Found %s as python script", main_py)
    return main_py


def _ensure_pip_requirements(code_dir: Path) -> Path:
    logger.info("Searching for requirements file ...")
    requirements = list(code_dir.rglob("requirements.txt"))
    if len(requirements) > 1:
        raise ValueError(f"Multiple requirements found, "
                         "don't know which one to pick"
                         ": {requirements}")
    elif len(requirements) == 0:
        return None
    else:
        requirements = requirements[0]
        logger.info("Found: %s", requirements)
    return requirements


def _show_io_environments() -> None:
    for io_type in ["input", "output"]:
        logger.info(
            "%s ENVs available: %s",
            io_type.capitalize(),
            json.dumps(
                list(
                    filter(
                        lambda x, io_type=io_type: f"{io_type.upper()}_" in x,
                        os.environ,
                    )
                ),
                indent=2,
            ),
        )


def setup():
    _show_io_environments()

    user_code_entrypoint = _find_user_code_entrypoint(INPUT_1)
    requirements_txt = _ensure_pip_requirements(INPUT_1)

    logger.info("Preparing launch script ...")
    venv_dir = Path.home() / ".venv"
    script = [
        "#!/bin/sh", "set -o errexit", "set -o nounset",
        "IFS=$(printf '\\n\\t')", 'echo "Creating virtual environment ..."',
        f'python3 -m venv --system-site-packages --symlinks --upgrade "{venv_dir}"',
        f'"{venv_dir}/bin/pip" install -U pip wheel setuptools',
        f'"{venv_dir}/bin/pip" install -r "{requirements_txt}"'
        if requirements_txt else '',
        f'echo "Executing code {user_code_entrypoint.name}..."',
        f'cd "{user_code_entrypoint.parents[0]}"',
        f'"{venv_dir}/bin/python3" "{user_code_entrypoint}"',
        'echo "DONE ..."',]
    main_script_path = Path("main.sh")
    main_script_path.write_text("\n".join(script), encoding="utf-8")
    main_script_path.chmod(0o755)


def start():
    logger.info("Starting main script ...")
    if main_script_path.exists():
        proc = subprocess.Popen([f'{main_script_path.resolve()}'])
        proc.wait()
    else:
        logger.info("No main script found, exiting")
    logger.info("Finished running python scripts")


def teardown():
    logger.info("Completed")


if __name__ == "__main__":
    action = "setup" if len(sys.argv) == 1 else sys.argv[1]
    try:
        if action == "setup":
            setup()
        elif action == "start":
            start()
        elif action == "teardown":
            teardown()
        else:
            raise ValueError(f"Unknown option for python runner {action}")
    except Exception as err:  # pylint: disable=broad-except
        logger.error("%s . Stopping %s", err, action)
