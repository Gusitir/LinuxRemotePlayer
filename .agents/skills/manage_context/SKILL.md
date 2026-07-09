---
name: manage_context
description: Skill to easily read and update the AI context markdown files (PLAN, CURRENT, APPCORE, CONTEXT).
---

# `manage_context` Skill

**Trigger**: Anytime you need to update the status of the project, learn about the architecture, or start a new task.

**Protocol**:
1. To know what to do next: Read `.agents/CURRENT.md`.
2. After finishing a task step: Edit `.agents/CURRENT.md` to check the box `[x]`.
3. When creating new core files: Edit `.agents/APPCORE.md` to document their path and purpose.
4. When a phase is done: Edit `.agents/PLAN.md` to check it off, and wipe/rewrite `.agents/CURRENT.md` with tasks for the next phase.
5. Keep edits minimal and token-efficient. Use `replace_file_content` or `write_to_file` tools.
