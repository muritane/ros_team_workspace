import errno
import os
import subprocess

from pathlib import Path


class ScriptExecutor:
    def __init__(self) -> None:
        self._shell = "bash"

    def execute(self, script: Path, *argv):
        if not script.is_file():
            raise FileNotFoundError(
                errno.ENOENT,
                os.strerror(errno.ENOENT),
                f'The script:"{script}" passed to the ScriptExecutor does not exist.',
            )

        cmd = [self._shell] + [script] + [arg for arg in argv if arg != None]
        print(cmd)
        try:
            subprocess.run(cmd, check=True, text=True)
        except:
            pass
