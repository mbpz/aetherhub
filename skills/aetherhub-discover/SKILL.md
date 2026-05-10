---
name: aetherhub-discover
description: Search and discover skills from AetherHub marketplace. Use when user wants to find a skill for a specific task or capability.
trigger: "find skill" "search skills" "discover skill" "skill marketplace" "look for skill" "need a skill for"
version: 1.0.0
---

# AetherHub Discover Skill

Search and discover skills from the AetherHub marketplace.

## When to Use

Use this skill when:
- User wants to find a skill for a specific task (e.g., "find a CSV processing skill")
- User asks about available skills in the marketplace
- User needs to discover capabilities they didn't know existed
- User wants to browse or search the skill marketplace

## API Usage

The skill uses the AetherHub web API at `http://localhost:8000/api/v1`:

### Search Skills (Hybrid Search)
```
GET /api/v1/skills/search?q={query}&category={category}&tags={tags}
```

Parameters:
- `q`: Search query (uses FTS5 + vector embeddings with RRF fusion)
- `category`: Optional filter by category (数据处理, 网络工具, 文件操作, AI工具, 系统工具, 其他)
- `tags`: Optional tags filter (comma-separated)
- `page`, `size`: Pagination (default size 20, max 100)

### List Categories
```
GET /api/v1/skills/categories
```
Returns category list with skill counts.

### Get Skill Details
```
GET /api/v1/skills/{skill_id}
```

### Get Leaderboard
```
GET /api/v1/analytics/leaderboard?period=week&limit=10
```

## Example Interactions

**User says:** "I need a skill for processing CSV files"

1. Call `/api/v1/skills/search?q=csv data processing`
2. Review the returned skills for CSV processing capabilities
3. Present the user with top matching skills

**User says:** "What AI tools are available?"

1. Call `/api/v1/skills/search?q=ai&category=AI工具`
2. Present the results

**User says:** "Show me the top rated skills"

1. Call `/api/v1/analytics/leaderboard?limit=10`
2. Present the leaderboard

## Response Format

All API responses follow this format:
```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

Error responses have non-zero code and error message in the `message` field.
