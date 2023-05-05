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

import os
from rtwcli.verb import VerbExtension
from rtw_cmds.docker.utils import extract_variables, start_and_connect_user


class EnterVerb(VerbExtension):
    """Enter docker container."""

    def main(self, *, args):
        print("##### enter docker verb begin #####")

        ROS_WS = os.environ.get("ROS_WS", None)
        if not ROS_WS:
            print(
                'It seems ROS_WS was not exported. Did you source your workspace by executing _"<ws_alias>"?'
            )
            return

        ros_ws_name = ROS_WS.split("/")[-1]
        print(f"ROS_WS is exported: {ROS_WS} -> ros_ws_name: {ros_ws_name}")

        print(
            "RosTeamWS_WS_DOCKER* variables are not exported, therefore getting them from reading '~/.ros_team_ws_rc'"
        )
        variables = extract_variables(ros_ws_name, os.path.expanduser("~/.ros_team_ws_rc"))
        print(f"Read variables: {variables}")

        RosTeamWS_WS_DOCKER_SUPPORT = variables.get("RosTeamWS_WS_DOCKER_SUPPORT", None)
        if not RosTeamWS_WS_DOCKER_SUPPORT or RosTeamWS_WS_DOCKER_SUPPORT == "false":
            print(
                'It seems your current workspace does not support docker. If it should, did you activate it by executing _"<ws_alias>"?'
            )
            return

        RosTeamWS_DOCKER_TAG = variables.get("RosTeamWS_DOCKER_TAG", None)
        print(f"RosTeamWS_DOCKER_TAG: {RosTeamWS_DOCKER_TAG}")

        start_and_connect_user(RosTeamWS_DOCKER_TAG)

        print("##### enter docker verb end #####")
