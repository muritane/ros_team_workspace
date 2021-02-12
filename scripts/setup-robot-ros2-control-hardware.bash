#!/bin/bash
#
# Copyright 2021 Stogl Denis Stogl (Stogl Robotics Consulting)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

usage="setup-robot-ros2-control-hardware.bash FILE_NAME [CLASS_NAME] [PKG_NAME]"

# echo ""
# echo "Your path is `pwd`. Is this your package folder where to setup robot's bringup?"
# read -p "If so press <ENTER> otherise <CTRL>+C and start the script again from the bringup folder."

# Load Framework defines
script_own_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" > /dev/null && pwd )"
source $script_own_dir/_RosTeamWs_Defines.bash
check_ros_distro ${ROS_DISTRO}

FILE_NAME=$1
if [ -z "$1" ]; then
  print_and_exit "ERROR: You should provide the file name!"
fi
if [ -f src/$FILE_NAME.cpp ]; then
  print_and_exit "ERROR:The file '$FILE_NAME' alread exist!"
fi

CLASS_NAME=$2
if [ -z "$2" ]; then
  delimiter='_'
  s="$FILE_NAME$delimiter"
  CLASS_NAME=""
  while [[ $s ]]; do
    part="${s%%"$delimiter"*}"
    s=${s#*"$delimiter"}
    CLASS_NAME="$CLASS_NAME${part^}"
  done
  echo "ClassName guessed from the '$FILE_NAME': '$CLASS_NAME'. Is this correct? If not provide it as the second parameter."
fi

PKG_NAME=$3
if [ -z "$3" ]; then
  current=`pwd`
  PKG_NAME=$(basename "$current")
  echo "Package name guessed from the current path is '$PKG_NAME'. Is this correct? If not provide it as the third parameter."
fi

echo "Which type of ros2_control hardware interface you want to extend? [0]"
echo "(0) system"
echo "(1) sensor"
echo "(2) actuator"
read choice
choice=${choice="0"}

INTERFACE_TYPE="system"
case "$choice" in
"1")
  INTERFACE_TYPE="sensor"
  ;;
"2")
  INTERFACE_TYPE="actuator"
esac

echo "Which license-header do you want to use? [1]"
echo "(0) None"
echo "(1) Apache 2.0 License"
echo "(2) Propiatery"
read choice
choice=${choice:="1"}

if [ "$choice" != 0 ]; then
  read -p "Insert your company or personal name (copyright): " NAME_ON_LICENSE
  NAME_ON_LICENSE=${NAME_ON_LICENSE=""}
  YEAR_ON_LICENSE=`date +%Y`
fi

LICENSE_HEADER=""
case "$choice" in
"1")
  LICENSE_HEADER="$LICENSE_TEMPLATES/default_cpp.txt"
  ;;
"2")
  LICENSE_HEADER="$LICENSE_TEMPLATES/propriatery_company_cpp.txt"
esac

echo ""
echo "ATTENTION: Setting up ros2_control hardware interface files with following parameters: file name '$FILE_NAME', class '$CLASS_NAME', package/namespace '$PKG_NAME' for interface type '$INTERFACE_TYPE'. Those will be placed in folder '`pwd`'."
echo ""
read -p "If correct press <ENTER>, otherwise <CTRL>+C and start the script again from the package folder and/or with correct robot name."

# Add folders if deleted
ADD_FOLDERS=("include/$PKG_NAME" "src" "test")

for FOLDER in "${ADD_FOLDERS[@]}"; do
    mkdir -p $FOLDER
done

# Set file constants
VC_H="include/$PKG_NAME/visibility_control.h"
HW_ITF_HPP="include/$PKG_NAME/$FILE_NAME.hpp"
HW_ITF_CPP="src/$FILE_NAME.cpp"
PLUGIN_XML="$PKG_NAME.xml"
TEST_CPP="test/test_$FILE_NAME.cpp"

# Copy files
cp -n $ROS2_CONTROL_HW_ITF_TEMPLATES/visibility_control.h $VC_H
cp -n $ROS2_CONTROL_HW_ITF_TEMPLATES/robot_hardware_interface.hpp $HW_ITF_HPP
cp -n $ROS2_CONTROL_HW_ITF_TEMPLATES/robot_hardware_interface.cpp $HW_ITF_CPP
cp -n $ROS2_CONTROL_HW_ITF_TEMPLATES/robot_pluginlib.xml $PLUGIN_XML
cp -n $ROS2_CONTROL_HW_ITF_TEMPLATES/test_robot_hardware_interface.cpp $TEST_CPP

echo "Template files copied."

# Add license header to the files
# TODO: When Propiatery then add the follwing before ament_lint_auto_find_test_dependencies()
# list(APPEND AMENT_LINT_AUTO_EXCLUDE
#    ament_cmake_copyright
#  )
FILES_TO_LICENSE=($VC_H $HW_ITF_HPP $HW_ITF_CPP $TEST_CPP)
TMP_FILE=".f_tmp"
if [[ "$LICENSE_HEADER" != "" ]]; then
  touch $TMP_FILE
  for FILE_TO_LIC in "${FILES_TO_LICENSE[@]}"; do
    cat $LICENSE_HEADER > $TMP_FILE
    cat $FILE_TO_LIC >> $TMP_FILE
    sed -i "/\\\$LICENSE\\\$/d" $TMP_FILE
    mv $TMP_FILE $FILE_TO_LIC
    sed -i "s/\\\$YEAR\\\$/${YEAR_ON_LICENSE}/g" $FILE_TO_LIC
    sed -i "s/\\\$NAME_ON_LICENSE\\\$/${NAME_ON_LICENSE}/g" $FILE_TO_LIC
  done
#   echo "Licence header added to files: ("`declare -p FILES_TO_LICENSE`")"
fi

FILES_TO_SED=("${FILES_TO_LICENSE[@]}")
# sed all needed files
FILES_TO_SED+=("$PLUGIN_XML")
# declare -p FILES_TO_SED

for SED_FILE in "${FILES_TO_SED[@]}"; do
  sed -i "s/\\\$PACKAGE_NAME\\\$/${PKG_NAME^^}/g" $SED_FILE
  sed -i "s/\\\$package_name\\\$/${PKG_NAME}/g" $SED_FILE
  sed -i "s/\\\$file_name\\\$/${FILE_NAME}/g" $SED_FILE
  sed -i "s/\\\$FILE_NAME\\\$/${FILE_NAME^^}/g" $SED_FILE
  sed -i "s/\\\$ClassName\\\$/${CLASS_NAME}/g" $SED_FILE
  sed -i "s/\\\$interface_type\\\$/${INTERFACE_TYPE}/g" $SED_FILE
  sed -i "s/\\\$Interface_Type\\\$/${INTERFACE_TYPE^}/g" $SED_FILE
done


# CMakeLists.txt: Remove comments if there any and add library
DEL_STRINGS=("# uncomment the following" "# further" "# find_package(<dependency>")

for DEL_STR in "${DEL_STRINGS[@]}"; do
  sed -i "/$DEL_STR/d" CMakeLists.txt
done

TMP_FILE=".f_tmp"
touch $TMP_FILE

# Get line with if(BUILD_TESTING)
TEST_LINE=`awk '$1 == "if(BUILD_TESTING)" { print NR }' CMakeLists.txt`
let CUT_LINE=$TEST_LINE-1
head -$CUT_LINE CMakeLists.txt >> $TMP_FILE

# Add Plugin library stuff inside
echo "add_library(" >> $TMP_FILE
echo "  $PKG_NAME" >> $TMP_FILE
echo "  SHARED" >> $TMP_FILE
echo "  $HW_ITF_CPP" >> $TMP_FILE
echo ")" >> $TMP_FILE

echo "target_include_directories(" >> $TMP_FILE
echo "  $PKG_NAME" >> $TMP_FILE
echo "  PUBLIC" >> $TMP_FILE
echo "  include" >> $TMP_FILE
echo ")" >> $TMP_FILE

echo "ament_target_dependencies(" >> $TMP_FILE
echo "  $PKG_NAME" >> $TMP_FILE
echo "  hardware_interface" >> $TMP_FILE
echo "  rclcpp" >> $TMP_FILE
echo ")" >> $TMP_FILE

# TODO(anyone): Delete after Foxy!!!
echo "# prevent pluginlib from using boost" >> $TMP_FILE
echo "target_compile_definitions($PKG_NAME PUBLIC \"PLUGINLIB__DISABLE_BOOST_FUNCTIONS\")" >> $TMP_FILE

echo "" >> $TMP_FILE
echo "pluginlib_export_plugin_description_file(" >> $TMP_FILE
echo "  hardware_interface $PLUGIN_XML)" >> $TMP_FILE

## Add install directives
echo "" >> $TMP_FILE
echo "install(" >> $TMP_FILE
echo "  TARGETS" >> $TMP_FILE
echo "  $PKG_NAME" >> $TMP_FILE
echo "  RUNTIME DESTINATION bin" >> $TMP_FILE
echo "  ARCHIVE DESTINATION lib" >> $TMP_FILE
echo "  LIBRARY DESTINATION lib" >> $TMP_FILE
echo ")" >> $TMP_FILE

if [[ ! `grep -q "DIRECTORY include/" $TMP_FILE` ]]; then
  echo "" >> $TMP_FILE
  echo "install(" >> $TMP_FILE
  echo "  DIRECTORY include/" >> $TMP_FILE
  echo "  DESTINATION include" >> $TMP_FILE
  echo ")" >> $TMP_FILE
fi

echo ""  >> $TMP_FILE

END_TEST_LINE=`tail -n +$TEST_LINE CMakeLists.txt | awk '$1 == "endif()" { print NR }'`
let CUT_LINE=$END_TEST_LINE-1
tail -n +$TEST_LINE CMakeLists.txt | head -$CUT_LINE >> $TMP_FILE

echo "" >> $TMP_FILE
echo "  ament_add_gmock(test_$FILE_NAME $TEST_CPP)" >> $TMP_FILE
echo "  target_include_directories(test_$FILE_NAME PRIVATE include)" >> $TMP_FILE
echo "  ament_target_dependencies(" >> $TMP_FILE
echo "    test_$FILE_NAME" >> $TMP_FILE
echo "    hardware_interface" >> $TMP_FILE
echo "    pluginlib" >> $TMP_FILE
echo "    ros2_control_test_assets" >> $TMP_FILE
echo "  )" >> $TMP_FILE
echo ""

# Add export definitions
tail -n +$TEST_LINE CMakeLists.txt | head -$END_TEST_LINE | tail -1 >> $TMP_FILE

echo "" >> $TMP_FILE
echo "ament_export_include_directories(" >> $TMP_FILE
echo "  include" >> $TMP_FILE
echo ")" >> $TMP_FILE

echo "ament_export_libraries(" >> $TMP_FILE
echo "  $PKG_NAME" >> $TMP_FILE
echo ")" >> $TMP_FILE

echo "ament_export_dependencies(" >> $TMP_FILE
echo "  hardware_interface" >> $TMP_FILE
echo "  pluginlib" >> $TMP_FILE
echo "  rclcpp" >> $TMP_FILE
echo ")" >> $TMP_FILE

# Add last part
let CUT_LINE=$END_TEST_LINE+1
tail -n +$TEST_LINE CMakeLists.txt | tail -n +$CUT_LINE >> $TMP_FILE

mv $TMP_FILE CMakeLists.txt

# CMakeLists.txt & package.xml: Add dependencies if they not exist
DEP_PKGS=("rclcpp" "pluginlib" "hardware_interface")

for DEP_PKG in "${DEP_PKGS[@]}"; do

  # CMakeLists.txt
  if `grep -q "find_package(${DEP_PKG} REQUIRED)" CMakeLists.txt`; then
    echo "'$DEP_PKG' is already dependency in CMakeLists.txt"
  else
    append_to_string="find_package(ament_cmake REQUIRED)"
    sed -i "s/$append_to_string/$append_to_string\\nfind_package(${DEP_PKG} REQUIRED)/g" CMakeLists.txt
  fi

  # package.xml
  if `grep -q "<depend>${DEP_PKG}</depend>" package.xml`; then
    echo "'$DEP_PKG' is already listed in package.xml"
  else
    append_to_string="<buildtool_depend>ament_cmake<\/buildtool_depend>"
    sed -i "s/$append_to_string/$append_to_string\\n\\n  <depend>${DEP_PKG}<\/depend>/g" package.xml
  fi

done

# CMakeLists.txt & package.xml: Add test dependencies if they not exist
TEST_DEP_PKGS=("ros2_control_test_assets" "ament_cmake_gmock")

for DEP_PKG in "${TEST_DEP_PKGS[@]}"; do

  # CMakeLists.txt
  if `grep -q "  find_package(${DEP_PKG} REQUIRED)" CMakeLists.txt`; then
    echo "'$DEP_PKG' is already listed in CMakeLists.txt"
  else
    append_to_string="ament_lint_auto_find_test_dependencies()"
    sed -i "s/$append_to_string/$append_to_string\\n  find_package(${DEP_PKG} REQUIRED)/g" CMakeLists.txt
  fi

  # package.xml
  if `grep -q "<test_depend>${DEP_PKG}</test_depend>" package.xml`; then
    echo "'$DEP_PKG' is already listed in package.xml"
  else
    append_to_string="<test_depend>ament_lint_common<\/test_depend>"
    sed -i "s/$append_to_string/$append_to_string\\n  <test_depend>${DEP_PKG}<\/test_depend>/g" package.xml
  fi
done

# extend README with general instructions
if [ -f README.md ]; then

  echo "" >> README.md
  echo "Pluginlib-Library: $PKG_NAME" >> README.md
  echo "Plugin: $PKG_NAME/${CLASS_NAME} (hardware_interface::${INTERFACE_TYPE^}Interface)" >> README.md

fi

git add .
# git commit -m "RosTeamWS: ros2_control skeleton files for $ROBOT_NAME generated."

# Compile and add new package the to the path
compile_and_source_package $PKG_NAME "yes"

echo ""
echo "FINISHED: Your package is set and the tests should be finished without any errors."






























