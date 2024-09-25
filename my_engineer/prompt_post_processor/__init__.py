import sys
from .prompt_post_processor import PromptPostProcessor

"""Prompt Post Processor Module

This module provides functionality to post-process user prompts using the Haiku LLM.

Contents:
- PromptPostProcessor: Main class for post-processing prompts.

Usage:
    from prompt_post_processor import PromptPostProcessor
    post_processor = PromptPostProcessor()
    post_processed_prompt = post_processor.post_process(original_prompt)

Note:
    This module requires the Haiku LLM provider and access to a post-processing prompt file.

Tests for this module can be found in the `tests` directory.
"""