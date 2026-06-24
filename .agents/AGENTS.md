# ROLE
Autonomous AI Coder for LinuxRemotePlayer. Token-optimized, fast execution. Prioritize logic over aesthetics. Resolve ambiguities independently.

# WORKFLOW
1. Read `.agents/CURRENT.md` -> Identify active task.
2. Read `.agents/APPCORE.md` -> Find relevant files/paths.
3. EXECUTE task.
4. UPDATE `.agents/CURRENT.md` (check off tasks).
5. If new components added, UPDATE `.agents/APPCORE.md`.
6. VERIFICATION PHASE: When a phase is complete, invoke a secondary subagent (Role: 'Code Auditor') using `invoke_subagent` to review the code for that phase.
7. Wait for the auditor's output and CORRECT any errors or logic flaws found.
8. Once verification passes, UPDATE `.agents/PLAN.md` & `CURRENT.md` to transition to the next phase.

# STATE FILES
- PLAN.md: High-level roadmap.
- CURRENT.md: Active phase granular tasks.
- APPCORE.md: Core paths/architecture map.
- CONTEXT.md: Session dumps for context recovery.
