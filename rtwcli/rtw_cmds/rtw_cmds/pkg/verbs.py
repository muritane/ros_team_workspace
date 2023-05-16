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

import ament_copyright
import os
import re
from rtw_cmds.helpers import (
    check_ros2_command_available,
    print_error,
    print_info,
)
from rtwcli.verb import VerbExtension
import subprocess
from rtw_cmds import input_utils
from rtw_cmds.git_utils import get_git_email, get_git_name


class CreateVerb(VerbExtension):
    """Create a new ROS package."""

    def add_arguments(self, parser, cli_name):
        parser.add_argument("package_name", help="The package name")
        parser.add_argument(
            "description",
            help="The description given in the package.xml",
        )

    def extract_build_types(self) -> list:
        ros2_pkg_create_help = subprocess.run(
            ["ros2", "pkg", "create", "-h"], stdout=subprocess.PIPE, text=True
        ).stdout
        build_type_line = re.search(r"--build-type {(.+?)}", ros2_pkg_create_help).group(1)
        build_types = build_type_line.split(",")
        return build_types

    def get_package_destination_from_input(self) -> str:
        return input_utils.get_valid_path_from_input(
            "Enter the destination path to create the ROS package: ",
            "Invalid path, please enter a valid directory path.",
        )

    def get_maintainer_name_from_input(self) -> str:
        return input_utils.get_valid_name_from_input(
            "Enter the maintainer's name: ", "Name cannot be empty, please enter a valid name."
        )

    def get_maintainer_email_from_input(self) -> str:
        return input_utils.get_valid_email_from_input("Enter the maintainer's email address: ")

    def get_maintainer_info(self):
        maintainer_info_choices = [
            input_utils.Choice(
                "user input",
                lambda: (
                    self.get_maintainer_name_from_input(),
                    self.get_maintainer_email_from_input(),
                ),
            )
        ]

        maintainer_name_git, maintainer_email_git = get_git_name(), get_git_email()
        if maintainer_name_git and maintainer_email_git:
            maintainer_info_choices.append(
                input_utils.Choice(
                    f"git: {maintainer_name_git} <{maintainer_email_git}>",
                    lambda name=maintainer_name_git, email=maintainer_email_git: (name, email),
                )
            )

        return input_utils.get_user_choice_from_choices(maintainer_info_choices).value()

    def get_destination_path(self) -> str:
        destination_choices = [
            input_utils.Choice("user input", self.get_package_destination_from_input)
        ]

        cwd = os.getcwd()
        cwd_choice = input_utils.Choice(f"current directory: {cwd}", lambda cwd=cwd: cwd)
        destination_choices.append(cwd_choice)

        ros_ws = os.environ.get("ROS_WS", None)
        ros_ws_src = None if ros_ws is None else os.path.join(ros_ws, "src")
        if ros_ws_src is not None:
            ros_ws_src_choice = input_utils.Choice(
                f"src directory: {ros_ws_src}", lambda ros_ws_src=ros_ws_src: ros_ws_src
            )
            destination_choices.append(ros_ws_src_choice)

        return input_utils.get_user_choice_from_choices(destination_choices).value()

    def get_build_type(self):
        build_types = self.extract_build_types()
        build_choices = [
            input_utils.Choice(f"{build_type}", f"{build_type}") for build_type in build_types
        ]
        return input_utils.get_user_choice_from_choices(build_choices).value

    def get_pkg_type(self, pkg_types=["standard", "metapackage", "subpackage"]):
        pkg_type_choices = [
            input_utils.Choice(f"{pkg_type}", f"{pkg_type}") for pkg_type in pkg_types
        ]
        return input_utils.get_user_choice_from_choices(pkg_type_choices).value

    def get_license_from_input(self) -> str:
        return input_utils.get_valid_name_from_input(
            "Enter the license's name: ",
            "License cannot be empty, please enter a valid license's name.",
        )

    def get_license(self) -> str:
        licenses_choices = [input_utils.Choice("user input", self.get_license_from_input)]
        licenses = [entry.spdx for _, entry in ament_copyright.get_licenses().items()]
        licenses_choices += [
            input_utils.Choice(f"{license}", lambda license=license: license)
            for license in licenses
        ]
        return input_utils.get_user_choice_from_choices(licenses_choices).value()

    def main(self, *, args):
        pkg_format = 3

        ros2_command_available = check_ros2_command_available()
        print(f"ros2_command_available: {ros2_command_available}")

        if not ros2_command_available:
            print_error("The 'ros2' command is not available. Did you source your workspace?")
            return

        print_info("Where to create the package?")
        destination = self.get_destination_path()
        print_info(f"The package '{args.package_name}' will be created in '{destination}'")

        print()
        print_info("What type of package you want to create?")
        pkg_type = self.get_pkg_type()
        pkg_type_to_print = {
            "standard": "Standard package",
            "metapackage": "Meta-package",
            "subpackage": "Subpackage",
        }[pkg_type]
        print_info(f"{pkg_type_to_print} '{args.package_name}' will be created in '{destination}'")
        print_error("TODO: implement the use of pkg_type")

        print()
        print_info("Who will maintain the package you want to create? Please provide the info.")
        maintainer_name, maintainer_email = self.get_maintainer_info()
        print_info(
            f"The name '{maintainer_name}' and email address '{maintainer_email}' will be used as maintainer info!"
        )

        print()
        print_info("How do you want to license your package?")
        pkg_license = self.get_license()
        print_info(f"The license '{pkg_license}' will be used! ($)")

        print()
        print_info("Please choose your package build type:")
        build_type = self.get_build_type()

        print()
        print_info(
            f"ATTENTION: Creating '{pkg_type}' package '{args.package_name}' in '{destination}' with description '{args.description}', license '{pkg_license}', build type '{build_type}' and maintainer '{maintainer_name} <{maintainer_email}>'"
        )
        print("If correct press <ENTER>, otherwise <CTRL>+C and start the script again.")
        input()

        ros2_pkg_create_cmd = (
            ["ros2", "pkg", "create", args.package_name]
            + ["--package-format", f"{pkg_format}"]
            + ["--description", f"{args.description}"]
            + ["--license", f"{pkg_license}"]
            + ["--destination-directory", f"{destination}"]
            + ["--build-type", f"{build_type}"]
            + ["--maintainer-email", f"{maintainer_email}"]
            + ["--maintainer-name", f"{maintainer_name}"]
        )
        ros2_pkg_create_completed_process = subprocess.run(
            ros2_pkg_create_cmd, stdout=subprocess.PIPE, text=True
        )
        print(f"ros2_pkg_create stdout: {ros2_pkg_create_completed_process.stdout}")
        print(f"ros2_pkg_create stderr: {ros2_pkg_create_completed_process.stderr}")
