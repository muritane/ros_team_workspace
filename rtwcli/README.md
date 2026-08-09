# rtw cli installation

Clone this repo: `git clone https://github.com/b-robotized/ros_team_workspace.git`

Install venv (e.g. `sudo apt install python3.12-venv`)

Create a new venv: `python -m venv .rtw_venv`

Activate the created venv: `. .rtw_venv/bin/activate`

Install rtwcli: `cd ros_team_workspace/rtwcli/ && pip3 install --break-system-dependencies -r requirements.txt`


## For workspace visibility

Source rtw: `source ros_team_workspace/setup.bash`

Setup auto-sourcing: `setup-auto-sourcing`


## Usage

Activate the created venv: `. .rtw_venv/bin/activate`

Try rtwcli help command: `rtw --help`


## Porting workspace

add explicit export to variables: `bash ros_team_workspace/scripts/update-rtw.bash`

source new methods with exports: `source ~/.ros_team_ws_rc`

source your workspace: `_<ws_name>`

port config: `rtw wokspace port`

test porting: `rtw wokspace use`


## For converting https to ssh:
> [!NOTE]
> `git config --global url."git@github.com:".insteadOf "https://github.com/"`
