My Engineer is an AI coding assistant that is good at creating or editing multiple files at a time.



## Installation
```
python -m venv .venv
source .venv/bin/activate
pip install my-engineer
```

## Execution

```
# must run at the root of your application
my-engineer
```

## How to use

- my-engineer will open a blank vscode file, enter your instructions ("write a complete next.js application" or "add comments to all files in my codebase"). **Processing will start when you close the file** (⌘-W).


# Things to know:

- my-engineer uses Sonnet 3.5 to generate the code change instructions, but uses Haiku for everything else
- Anthropic API requests are cached, so continuing a conversation is 10% of the cost of starting a new one
- You have 5 minutes to continue a conversation before the Anthropic cache expires
- A log of the interaction with the llm is created in the folder runs/ 
- The file file_summaries.yaml is only update with new files, if you make significant changes to many files, delete it so it gets re-created

# Recommended addition to .gitignore

```
runs/
file_summaries.yaml
```