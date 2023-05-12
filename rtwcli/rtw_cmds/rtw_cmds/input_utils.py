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

from dataclasses import dataclass
import os
import re
from typing import List


@dataclass
class Choice:
    prompt: str
    value: any


def get_input_with_validation(prompt: str, error_msg: str, validation_func):
    while True:
        user_input = input(prompt).strip()
        if validation_func(user_input):
            return user_input
        print(error_msg)


def get_valid_email_from_input(
    prompt="Enter an email address: ",
    error_msg="Invalid email format, please enter a valid email.",
    validation_func=lambda email: re.match(
        r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$", email
    ),
):
    return get_input_with_validation(prompt, error_msg, validation_func)


def get_valid_name_from_input(
    prompt="Enter a name: ",
    error_msg="Invalid name, please enter a valid name.",
    validation_func=lambda name: len(name) > 0,
):
    return get_input_with_validation(prompt, error_msg, validation_func)


def get_valid_path_from_input(
    prompt="Enter a path: ",
    error_msg="Invalid path, please enter a valid path.",
    validation_func=lambda path: os.path.exists(path) and os.path.isdir(path),
):
    return get_input_with_validation(prompt, error_msg, validation_func)


def get_choice_number_from_input(num_range: range):
    while True:
        try:
            user_input = int(input("Enter the number corresponding to your choice: "))
            if user_input in num_range:
                return user_input
            else:
                print("Invalid input. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def get_user_choice_from_choices(choices: List[Choice], start=1) -> Choice:
    if len(choices) == 1:
        return choices[0]
    options = [f"{idx}) {choice.prompt}" for idx, choice in enumerate(choices, start=start)]
    print("\n".join(options))
    valid_choices = range(start, len(choices) + start)
    choice_idx = get_choice_number_from_input(valid_choices)
    return choices[choice_idx - start]
