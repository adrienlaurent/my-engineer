import os
import platform
import subprocess
from .config import get_config

EDITOR_COMMANDS = {
    'vscode': 'code',
    'cursor': 'cursor',
    'vim': 'vim',
    'pycharm': 'pycharm',
    'notepad': 'notepad',
    'textedit': 'open -a TextEdit',
    'nano': 'nano',
    'xcode': 'xed',
    'eclipse': 'eclipse',
    'android_studio': 'studio'
}

def get_editor_command():
    config = get_config()
    editor = config.editor
    return EDITOR_COMMANDS.get(editor, 'code')  # Default to VS Code if editor not found

def open_file_in_editor(file_path: str):
    editor_command = get_editor_command()
    if ' ' in editor_command:
        command = f"{editor_command} '{file_path}'"
    else:
        command = f"{editor_command} {file_path}"
    
    if platform.system() == 'Windows':
        os.system(command)
    else:
        subprocess.Popen(command, shell=True)
