from anthropic.types.tool_param import ToolParam
from typing import Any

# Grammar Correction Tool
APPLY_GRAMMAR_CORRECTIONS: ToolParam = {
    "name": "apply_grammar_corrections",
    "description": "Apply structured grammar and style corrections to text",
    "input_schema": {
        "type": "object",
        "properties": {
            "corrections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "original": {
                            "type": "string",
                            "description": "Original text to replace",
                        },
                        "replacement": {
                            "type": "string",
                            "description": "Corrected text",
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for the correction",
                        },
                    },
                    "required": ["original", "replacement", "reason"],
                },
                "description": "List of corrections to apply",
            }
        },
        "required": ["corrections"],
    },
}

# Coherence Check Tool
FLAG_COHERENCE_ISSUES: ToolParam = {
    "name": "flag_coherence_issues",
    "description": "Flag narrative coherence, pacing, and consistency issues",
    "input_schema": {
        "type": "object",
        "properties": {
            "issues": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "issue_type": {
                            "type": "string",
                            "enum": ["pacing", "plot", "consistency", "tone", "other"],
                            "description": "Type of coherence issue",
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the issue",
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "description": "Severity level",
                        },
                        "suggestion": {
                            "type": "string",
                            "description": "Suggested fix",
                        },
                    },
                    "required": ["issue_type", "description", "severity"],
                },
                "description": "List of coherence issues found",
            }
        },
        "required": ["issues"],
    },
}

# Character Arc Tool
UPDATE_CHARACTER_ARC: ToolParam = {
    "name": "update_character_arc",
    "description": "Analyze and update character development and consistency",
    "input_schema": {
        "type": "object",
        "properties": {
            "arc_notes": {
                "type": "string",
                "description": "Updated character arc analysis",
            },
            "inconsistencies": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of character inconsistencies found",
            },
            "development_suggestions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Suggestions for character development",
            },
        },
        "required": ["arc_notes"],
    },
}

# Scene Expansion Tool
EXPAND_SCENE: ToolParam = {
    "name": "expand_scene",
    "description": "Expand a raw idea into a full scene draft",
    "input_schema": {
        "type": "object",
        "properties": {
            "expanded_content": {
                "type": "string",
                "description": "Full scene content in markdown",
            },
            "suggested_dialogue": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Key dialogue lines for the scene",
            },
            "scene_notes": {
                "type": "string",
                "description": "Notes on setting, mood, character arcs involved",
            },
        },
        "required": ["expanded_content"],
    },
}

# All tools grouped by agent type
GRAMMAR_TOOLS = [APPLY_GRAMMAR_CORRECTIONS]
COHERENCE_TOOLS = [FLAG_COHERENCE_ISSUES]
CHARACTER_TOOLS = [UPDATE_CHARACTER_ARC]
SCENE_EXPAND_TOOLS = [EXPAND_SCENE]
