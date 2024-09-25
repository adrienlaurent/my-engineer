from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Define requirements directly in setup.py
requirements = [
    "pytest==8.3.3",
    "anthropic==0.34.2",
    "astor==0.8.1",
    "PyYAML==6.0.2",
    "rich==13.8.1",
    "pydantic==2.9.2",
    "colorama==0.4.6",
    "python-dotenv==1.0.1",
    "tiktoken==0.7.0"
]

setup(
    name="my-engineer",
    version="0.1.9",
    author="Adrien Laurent",
    author_email="adrien.laurent@gmail.com",
    description="My Engineer is an AI coding assistant that is good at creating or editing multiple files at a time.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/adrienlaurent/my-engineer",
    packages=find_packages(),
    install_requires=requirements,
    package_data={"my_engineer": ["templates/*"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "my-engineer=my_engineer.main:main",
        ],
    },
    python_requires=">=3.7",
)