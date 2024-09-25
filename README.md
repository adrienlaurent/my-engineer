# My Engineer

My Engineer is an AI coding assistant that excels at editing multiple files simultaneously.

## GitHub Codespaces
My Engineer works well in GitHub Codespaces. It's easy to try it out: https://github.com/codespaces

## Installation
```
python -m venv .venv
source .venv/bin/activate
pip install my-engineer
```

## Execution
```
# Must run at the root of your application
source .venv/bin/activate
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

## Recommended Additions to .gitignore
```
.venv
runs/
file_summaries.yaml
```
