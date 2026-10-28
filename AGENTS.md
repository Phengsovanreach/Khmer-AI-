# Autonomous ChatGPT ↔ Google Antigravity Execution System

## Collaboration Protocols & Rules

1. **Autonomous Execution**:
   - ChatGPT is the planning and architecture review partner.
   - Google Antigravity is the autonomous software engineer that inspects, edits, runs, tests, and verifies code.
   - Crosswalk Room: `chatgptantigravity2`

2. **Full Authorization & Permissions**:
   - Authorized to edit code, execute tests, run builds, and fix issues independently.
   - For IDE permission modals, Option 3 ("Yes, and always allow") is selected for routine development.

3. **Production Safety**:
   - Feature branch workflow (`feature/self-healing-system` / `fix/...`) with human review gates before merging to `main`.
   - Zero credential exposure.
   - No destructive database migrations or data deletions.

4. **Evidence-Based Completion**:
   - All reports must include exact test counts, CI status, and live URL verification.
   - Final completion reports are dispatched to `chatgptantigravity2` and the project Telegram bot.
