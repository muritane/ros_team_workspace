# Copyright (c) 2023, Stogl Robotics Consulting UG (haftungsbeschränkt)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import shutil
import subprocess


def get_git_name():
    return _get_git_config("name")


def get_git_email():
    return _get_git_config("email")


def _get_git_config(config: str):
    git = shutil.which("git")
    if git is None:
        return ""
    p = subprocess.Popen([git, "config", f"user.{config}"], stdout=subprocess.PIPE)
    resp = p.communicate()
    return resp[0].decode().rstrip()
