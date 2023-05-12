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

from pathlib import Path
from rtwcli.verb import VerbExtension
from rtw_cmds.utils import ScriptExecutor


class CreateVerb(VerbExtension):
    """Create a new ROS package."""

    def main(self, *, args):
        print("Create a new ROS package")
        script_exec = ScriptExecutor()
        script_path = Path("/home/daniela/ros_team_workspace/scripts/create-new-package.bash")
        script_exec.execute(script_path, "foo", "foo")
