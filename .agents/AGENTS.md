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
- CURRENT.md: Active state, uncommitted changes, pending git/deploy actions, phase history.
- APPCORE.md: Core paths/architecture map (kept current through v1.5).
- CONTEXT.md: Session dumps for context recovery.
- AUDITS/: heavy code audits for major versions (AUDIT_v1.5.md ...). One file per big audit.
- PLAN_GEMINI_*.md: task briefs for the external coder (Gemini executes; Claude plans+audits).
  One task = one commit = one audit checkpoint. Gemini logs out-of-scope findings in
  CURRENT.md (HALLAZGOS GEMINI) instead of fixing them.
- TESTING.md: current intensive test plan (owner executes on HTPC+phone; failures become
  tasks in the next plan). Replaces the old root-level TESTING.md (deleted 2026-07-17).
- archive/: closed milestone plans and superseded reports (PLAN_GEMINI_v1.6/v1.7,
  AUDIT_G07_G13_Report). Do not resurrect; reference only.

# MODELS (updated 2026-07-17)
- Executor: Gemini 3.5 Pro. Auditor/planner: Claude — owner switched tier from
  "Fable5 Supercode" to "Fable5 Alto". Verification discipline stays the same:
  every claim backed by a real command output; auditor re-runs checks independently.

# ENVIRONMENT RULE (critical)
- The bash mount (/mnt) TRUNCATES large files (~40KB): app.js real=1402 lines, mount shows ~1116.
  So bash/python/node/git over the mount are UNRELIABLE for large files (false syntax errors,
  misleading git status). Read/edit/audit large files ONLY with the harness tools; run
  node --check / py_compile / .deb builds in WSL, never in the mount.
