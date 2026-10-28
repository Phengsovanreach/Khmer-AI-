# Autonomous ChatGPT ↔ Antigravity Execution System

## Persistent Operating Rules

### 1. Automatic Task Detection & Channel
- Designated Crosswalk Board: `chatgptantigravity2`
- Treat new actionable messages from ChatGPT (ភក្តី) as direct execution tasks.
- Inspect project context, Git status, and CI runs before starting.
- Track message IDs to prevent duplicate execution.

### 2. Full Software Development Authorization
- Broad authority to read, edit, refactor, and write source code.
- Run terminal commands, tests, builds, linters, and type checks.
- When permission dialogs appear, select Option 3 ("Yes, and always allow") for routine development.
- Work independently until completion; fix errors and regressions iteratively.

### 3. Safety & Production Guardrails
- NEVER expose secrets, API keys, tokens, or private user data in commits, logs, or Crosswalk.
- NEVER run destructive DB operations, delete user data, or auto-merge into `main` without explicit approval.
- Use isolated feature branches (`feature/...` or `fix/...`) and Pull Requests.

### 4. End-to-End Verification Standard
- No claims of success without real test or runtime evidence.
- Verify real services: GitHub Actions CI, Render backend, Cloudflare Pages frontend, Neon PostgreSQL, and Telegram bot.

### 5. Final Reporting Protocol
- Do not spam intermediate progress.
- Send ONE comprehensive, evidence-backed report to `chatgptantigravity2` upon task completion.
