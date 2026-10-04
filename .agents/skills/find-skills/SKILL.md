---
name: find-skills
description: |
    Discovers, recommends, and locates the right agent skills, tools, and technical patterns
    for any project task, library, or framework.

    Relevant when:
      - User asks how to do something new or asks for recommended skills/tools.
      - Assessing what capabilities or extensions are needed for a specific tech stack.
      - Searching local or global skill directories (.agents/skills, ~/.gemini/config/skills).
---

# Find Skills: Agent Capability Discovery

This skill empowers the agent to quickly find, recommend, and structure modular skills and workflows tailored to the user's project requirements.

---

## 1. Skill Discovery Workflow

When embarking on a new feature or technology:

1. **Analyze Project Dependencies**: Inspect `package.json`, `requirements.txt`, `go.mod`, or `Cargo.toml` to identify the runtime stack.
2. **Identify Capability Gaps**:
    - Building UI? -> Needs `ui-ux-pro-max`
    - Testing business logic? -> Needs `tdd`
    - Deploying frontend? -> Needs `deploy-to-vercel`
    - Architecture & flow design? -> Needs `excalidraw`
    - Video generation? -> Needs `remotion`
    - Web performance & SEO? -> Needs `web-quality`
    - Disciplined planning? -> Needs `superpowers`
3. **Discover Local & Global Skills**:
    - Check Workspace Skills: `.agents/skills/`
    - Check Global Skills: `~/.gemini/config/skills/`

---

## 2. Creating New On-Demand Skills

When a project introduces a custom workflow, establish a new skill:

```text
.agents/skills/<skill-name>/
├── SKILL.md          # YAML frontmatter + concise runbook
└── scripts/          # Optional automation scripts
```
