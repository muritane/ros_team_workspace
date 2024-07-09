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

import argparse
import os
import shutil
import subprocess
import sys
from typing import Dict, List
import questionary
from rtwcli.verb import VerbExtension
from rtwcli.workspace_utils import get_current_workspace
from rtwcli import logger
from catkin_pkg.package import parse_package
from cmakelists_parsing import CMakeListsParser


ROS2_CONTROL_TEMPLATES = os.environ.get("ROS2_CONTROL_TEMPLATES", "/path/to/templates")


def get_cmd_output(cmd: str) -> str:
    """Run a command and return its output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            shell=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run command '{cmd}': {e}")
        return ""
    except FileNotFoundError as e:
        logger.error(f"Command '{cmd}' not found: {e}")
        return ""

    return result.stdout


def get_ws_packages(ws_folder: str, src_suffix: str = "src/*") -> Dict[str, str]:
    """Return a dictionary of package names and their paths."""
    colcon_list_output = get_cmd_output(
        f"colcon list --paths {os.path.join(ws_folder, src_suffix)}"
    )
    if not colcon_list_output:
        return {}

    logger.debug(f"colcon list output:\n{colcon_list_output}")

    # Expected output of colcon list: <package_name> <path> (<build_type>)
    packages = {}
    for line in colcon_list_output.splitlines():
        parts = line.split()
        logger.debug(f"Parts: {parts}")
        if len(parts) < 2:
            continue

        package_name = parts[0]
        package_path = parts[1]
        packages[package_name] = package_path

    return packages


def package_name_completer(**kwargs) -> List[str]:
    """Return a list of package names."""
    ws = get_current_workspace()
    if not ws or ws.standalone or not ws.ws_folder:
        return ["NO_WORKSPACE_SET"]

    package_names = list(get_ws_packages(ws.ws_folder).keys())
    if not package_names:
        return ["NO_PACKAGES_FOUND"]

    return package_names


def setup_robot_bringup(robot_name, description_pkg_name):
    if not os.path.exists("package.xml"):
        logger.error(
            "'package.xml' not found. Execute this script at the top level of your package folder."
        )
        sys.exit(1)

    pkg = parse_package("package.xml")
    pkg_name = pkg.name

    logger.info(
        f"Setting up bringup configuration for robot '{robot_name}' in package '{pkg_name}' "
        f"in folder '{os.getcwd()}' with robot description package '{description_pkg_name}'."
    )

    if not is_package_suitable_for_bringup():
        logger.error("This package doesn't seem suitable for bringup. It should be almost empty.")
        sys.exit(1)

    if not questionary.confirm("Is this correct? Press Y to continue, N to exit.").ask():
        logger.info("Exiting as per user request.")
        sys.exit(0)

    remove_empty_folders(["include", "src"])
    create_folders(["config", "launch"])
    copy_config_files(robot_name)
    launch_file_types = get_launch_file_types()
    copy_launch_files(robot_name, pkg_name, description_pkg_name, launch_file_types)
    update_package_xml(pkg, description_pkg_name)
    update_cmakelists()
    update_readme(pkg_name, robot_name, description_pkg_name)

    logger.info(
        f"FINISHED: You can test the configuration by executing 'ros2 launch {pkg_name} {robot_name}.launch{' '.join(launch_file_types)}'"
    )


def is_package_suitable_for_bringup():
    content_count = sum(len(files) for _, _, files in os.walk("."))
    logger.debug(f"Package contains {content_count} files/directories.")
    return content_count < 5  # Arbitrary threshold, adjust as needed


def remove_empty_folders(folders):
    for folder in folders:
        if os.path.isdir(folder) and not os.listdir(folder):
            os.rmdir(folder)
            logger.debug(f"Removed empty folder: {folder}")


def create_folders(folders):
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        logger.debug(f"Created folder: {folder}")


def copy_config_files(robot_name):
    shutil.copy(
        f"{ROS2_CONTROL_TEMPLATES}/robot_controllers.yaml", f"config/{robot_name}_controllers.yaml"
    )
    shutil.copy(
        f"{ROS2_CONTROL_TEMPLATES}/test_goal_publishers_config.yaml",
        "config/test_goal_publishers_config.yaml",
    )
    logger.debug("Copied config files")


def get_launch_file_types():
    choices = [
        questionary.Choice("XML (.xml)", value=[".xml"]),
        questionary.Choice("Python (.py)", value=[".py"]),
        questionary.Choice("Both (.xml and .py)", value=[".xml", ".py"]),
    ]
    return questionary.select("Which launch file types should be added?", choices=choices).ask()


def copy_launch_files(robot_name, pkg_name, description_pkg_name, launch_file_types):
    for file_type in launch_file_types:
        files_to_copy = [
            (f"robot_ros2_control.launch{file_type}", f"{robot_name}.launch{file_type}"),
            (
                f"test_forward_position_controller.launch{file_type}",
                f"test_forward_position_controller.launch{file_type}",
            ),
            (
                f"test_joint_trajectory_controller.launch{file_type}",
                f"test_joint_trajectory_controller.launch{file_type}",
            ),
        ]

        for src, dest in files_to_copy:
            shutil.copy(f"{ROS2_CONTROL_TEMPLATES}/{src}", f"launch/{dest}")
            logger.debug(f"Copied {src} to launch/{dest}")

            with open(f"launch/{dest}") as file:
                content = file.read()

            content = content.replace("$PKG_NAME$", pkg_name)
            content = content.replace("$RUNTIME_CONFIG_PKG_NAME$", pkg_name)
            content = content.replace("$ROBOT_NAME$", robot_name)
            content = content.replace("$DESCR_PKG_NAME$", description_pkg_name)

            with open(f"launch/{dest}", "w") as file:
                file.write(content)
            logger.debug(f"Updated content in launch/{dest}")


def update_package_xml(pkg, description_pkg_name):
    dep_pkgs = [
        "xacro",
        "rviz2",
        "ros2_controllers_test_nodes",
        "robot_state_publisher",
        "joint_trajectory_controller",
        "joint_state_broadcaster",
        "forward_command_controller",
        "controller_manager",
        description_pkg_name,
    ]

    for dep_pkg in dep_pkgs:
        if not pkg.has_exec_depend(dep_pkg):
            pkg.exec_depends.append(dep_pkg)
            logger.debug(f"Added exec_depend for {dep_pkg}")

    with open("package.xml", "w") as f:
        f.write(pkg.to_xml())
    logger.debug("Updated package.xml")


def update_cmakelists():
    parser = CMakeListsParser("CMakeLists.txt")

    install_command = "install(DIRECTORY config launch DESTINATION share/${PROJECT_NAME})"
    if not any(
        cmd.command == "install" and "DIRECTORY config launch" in " ".join(cmd.arguments)
        for cmd in parser.parse()
    ):
        parser.add_command(install_command)
        logger.debug("Added install command to CMakeLists.txt")

    with open("CMakeLists.txt", "w") as f:
        f.write(str(parser))
    logger.debug("Updated CMakeLists.txt")


def update_readme(pkg_name, robot_name, description_pkg_name):
    if os.path.exists("README.md"):
        with open(f"{ROS2_CONTROL_TEMPLATES}/append_to_README.md") as f:
            append_content = f.read()

        append_content = append_content.replace("$PKG_NAME$", pkg_name)
        append_content = append_content.replace("$ROBOT_NAME$", robot_name)
        append_content = append_content.replace("$DESCR_PKG_NAME$", description_pkg_name)

        with open("README.md", "a") as f:
            f.write(append_content)
        logger.debug("Updated README.md")


class SetupRobotBringUpVerb(VerbExtension):
    """Change the current directory to the selected package directory."""

    def add_arguments(self, parser: argparse.ArgumentParser, cli_name: str):
        arg = parser.add_argument(
            "package_name",
            help="The package name",
            nargs="?",
        )
        arg.completer = package_name_completer  # type: ignore

    def main(self, *, args):
        ws = get_current_workspace()
        if not ws:
            logger.debug("No workspace is active.")
            return

        if ws.standalone:
            logger.debug("Standalone workspace does not have local folder.")
            return

        if not ws.ws_folder:
            logger.error("Workspace folder is not set.")
            return

        ws_packages = get_ws_packages(ws.ws_folder)
        if not ws_packages:
            logger.info("No packages found in the workspace.")
            return

        package_names = list(ws_packages.keys())

        pkg_name = args.package_name
        if not pkg_name:
            pkg_name = questionary.autocomplete(
                "Choose package",
                package_names,
                qmark="'Tab' to see all packages, type to filter, 'Enter' to select\n",
                meta_information=ws_packages.copy(),
                validate=lambda ws_choice: ws_choice in package_names,
                style=questionary.Style([("answer", "bg:ansiwhite")]),
                match_middle=True,
            ).ask()
            if not pkg_name:  # Cancelled by user
                return

        package_path = ws_packages.get(pkg_name)
        if not package_path:
            logger.error(f"Package '{pkg_name}' not found.")
            return

        logger.debug(f"Package path: {package_path}")

        robot_name = questionary.text("Enter the robot name:").ask()
        description_pkg_name = questionary.text("Enter the description package name:").ask()
        setup_robot_bringup(robot_name, description_pkg_name)
