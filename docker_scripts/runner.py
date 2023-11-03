import json
import os
import subprocess
import time
import pathlib as pl
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(filename)s:%(lineno)d] %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main"""

    input_path = pl.Path(
        os.environ["DY_SIDECAR_PATH_INPUTS"]) / 'input_1'

    pyrunner = PythonRunner(input_path)

    try:
        pyrunner.setup()
        pyrunner.start()
        pyrunner.teardown()
    except Exception as err:  # pylint: disable=broad-except
        logger.error(f"{err} . Stopping %s", exc_info=True)


class PythonRunner:

    def __init__(self, input_path, polling_time=1):
        """Constructor"""

        self.input_path = input_path
        self.main_sh_path = pl.Path(__file__).parent.absolute() / 'main.sh'
        self.venv_dir = pl.Path.home() / ".venv"
        self.polling_time = 1
        self.found_user_code_entrypoint = False
        self.user_code_entrypoint = None

    def _find_user_code_entrypoint(self, code_dir: pl.Path) -> pl.Path:
        logger.info("Searching for script main entrypoint ...")
        code_files = list(code_dir.rglob("*.py"))

        if not code_files:
            logger.info('No python files found')
            return None

        if len(code_files) > 1:
            code_files = list(code_dir.rglob("main.py"))
            if not code_files:
                raise ValueError("No main.py found in user-provided directory")
            if len(code_files) > 1:
                raise ValueError(
                    "Multiple main python files found"
                    " in user-provided directory,"
                    f"I don't know which one to run: {code_files}")

        main_py = code_files[0]
        logger.info("Found %s as python script", main_py)
        return main_py

    def _ensure_pip_requirements(self, code_dir: pl.Path) -> pl.Path:
        logger.info("Searching for requirements file ...")
        requirements = list(code_dir.rglob("requirements.txt"))
        if len(requirements) > 1:
            raise ValueError("Multiple requirements found, "
                             "don't know which one to pick"
                             f": {requirements}")
        elif len(requirements) == 0:
            return None
        else:
            requirements = requirements[0]
            logger.info("Found: %s", requirements)
        return requirements

    def _show_io_environments(self) -> None:
        for io_type in ["input", "output"]:
            logger.info(
                f"{io_type.capitalize()} ENVs available: %s",
                json.dumps(
                    list(
                        filter(
                            lambda x,
                            io_type=io_type: f"{io_type.upper()}_" in x,
                            os.environ,
                        )),
                    indent=2,
                ),
            )

    def try_find_user_entrypoint(self):

        while not self.user_code_entrypoint:
            logger.info(
                'Trying to find python files in input directory: '
                f'{self.input_path}')
            self.user_code_entrypoint = self._find_user_code_entrypoint(
                self.input_path)
            time.sleep(self.polling_time)

        self.found_user_code_entrypoint = True

        self.requirements_path = self._ensure_pip_requirements(self.input_path)
        self.main_env = {}
        self.main_env['OSPARC_VENV_DIR'] = str(self.venv_dir)
        self.main_env['OSPARC_USER_ENTRYPOINT_PATH'] = \
            str(self.user_code_entrypoint)
        self.main_env['OSPARC_REQUIREMENTS_TXT'] = str(
            self.requirements_path) if self.requirements_path else ''
        self.main_env['OSPARC_USER_ENTRYPOINT_DIR'] = \
            str(self.user_code_entrypoint.parents[0])

    def setup(self):
        self._show_io_environments()

        # Try to find user entrypoint, will poll until found
        self.try_find_user_entrypoint()

    def start(self):
        logger.info(f"Starting script {self.main_sh_path.resolve()} ...")
        if self.found_user_code_entrypoint:
            env = os.environ.copy()
            env |= self.main_env  # Merge envs
            logging.info(f'Using env: {env}')

            proc = subprocess.Popen(
                [f'{self.main_sh_path.resolve()}'], env=env)
            proc.wait()
        else:
            logger.info("No main script found, exiting")
        logger.info("Finished running python scripts")

    def teardown(self):
        logger.info("Completed")


if __name__ == "__main__":
    main()
