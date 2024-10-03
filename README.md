# My Engineer

My Engineer is an AI coding assistant that excels at editing multiple files simultaneously.

## GitHub Codespaces
My Engineer works well in GitHub Codespaces. It's easy to try it out: https://github.com/codespaces

## Installation (from pip)
Locally
```
python -m venv .venv
source .venv/bin/activate
pip install my-engineer
```

Globally
```
brew install pipx
pipx ensurepath
pipx install my-engineer
```

Globally (windows)
```
python3 -m pip install my-engineer
python3 -m my_engineer
```

## Installation (from sources)

```
pip install -r my_engineer/requirements.txt
python3 -m my_engineer
```

## Execution
```
# must run at the root of your application
my-engineer
```

## How to Use
- My Engineer will open a blank VS Code file. Enter your instructions (e.g., "Write a complete Next.js application" or "Add comments to all files in my codebase"). **Processing will start when you close the file**.

## Things to Know
- My Engineer uses Claude 3.5 Sonnet to generate code change instructions, but uses Claude 3 Haiku for everything else.
- Anthropic API requests are cached, so continuing a conversation costs only 10% of starting a new one.
- You have 5 minutes to continue a conversation before the Anthropic cache expires.
- A log of the interaction with the LLM is created in the `runs/` folder.
- The `file_summaries.yaml` file is only updated with new files. If you make significant changes to many files, delete it so it gets re-created.
- After you've completed a conversation, commit all your changes. my-engineer will offer to create a new branch for the next batch of changes.
- Before you commit the changes from my-engineer, you can view all of them with COMMAND-SHIFT-P, then "Git: View Changes".
- For small application, it's better to always include all files in the context.
- Add your code files, types definition and db structures to `always_include_patterns.txt` so that they are always included in the context.


## Recommended Additions to .gitignore
```
.venv
runs/
file_summaries.yaml
```
