---
name: aetherhub-execute
description: Execute a skill from AetherHub marketplace on the current codebase. Use when user wants to apply a skill to their project.
trigger: "execute skill" "run skill" "apply skill" "use skill from aetherhub" "download and run skill"
version: 1.0.0
---

# AetherHub Execute Skill

Execute a skill from AetherHub marketplace on the current codebase.

## When to Use

Use this skill when:
- User wants to download and execute a specific skill on their project
- User has found a skill they want to apply
- User asks to "run" or "execute" a skill from the marketplace

## Prerequisites

Before executing a skill:
1. The skill must be downloaded from AetherHub marketplace
2. Any dependencies specified by the skill must be installed
3. The skill code should be reviewed for safety

## API Usage

### Get Skill Details and Files
```
GET /api/v1/skills/{skill_id}
```

Returns skill metadata including:
- `name`, `version`, `description`
- `category`, `tags`
- `files` array with download URLs: `/api/v1/skills/{skill_id}/files/{filename}`

### Download Skill Files
```
GET /api/v1/skills/{skill_id}/files/{filename}
```

Save the file content to a local directory for execution.

### A2A Protocol - Agent Request
```
POST /api/v1/a2a/skill-request
Content-Type: application/json

{
  "capability": "csv-processing",
  "params": {"filepath": "data.csv"},
  "preferred_category": "数据处理"
}
```

Returns skill metadata and execution instructions.

## Execution Workflow

1. **Identify the skill** the user wants to execute
2. **Get skill details** via API
3. **Download skill files** to a working directory
4. **Review skill code** before execution
5. **Install dependencies** if needed
6. **Execute** the skill with appropriate parameters
7. **Report results** to the user

## Safety Considerations

- Always review skill code before execution
- Execute in sandboxed environment when possible
- Warn about file system modifications
- Check for potentially harmful operations

## Example

**User says:** "Execute the csv-data-processor skill on my data.csv file"

1. Search or get skill by name (skill_id=1 typically)
2. Download the skill.py file
3. Review the code
4. Execute: `python skill.py --input data.csv`
5. Report output path to user
