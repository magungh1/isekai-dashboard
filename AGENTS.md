# Agent Guidelines

## Workflow

**Always use PR-based workflow for new features and changes.** Never push directly to `main`.

### Feature Branch Naming

Use `feat/<short-description>` format:
- `feat/habit-tracker`
- `feat/command-palette`
- `fix/supabase-coalesce`
- `docs/update-readme`

### Steps

1. **Create branch** from latest `main`:
   ```bash
   git checkout -b feat/<description> main
   ```

2. **Commit changes** with conventional commit messages:
   ```
   feat: add habit tracker widget
   fix: handle COALESCE in Supabase REST wrapper
   docs: update README with new features
   ```

3. **Run tests** before pushing:
   ```bash
   make test
   ```

4. **Push and create PR**:
   ```bash
   git push -u origin feat/<description>
   gh pr create --title "<title>" --body "<summary>"
   ```

5. **Merge PR** after review (squash merge preferred).

### Commit Message Format

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation changes
- `refactor:` code refactoring
- `test:` test additions/changes
- `chore:` maintenance tasks

### Exceptions

- Hotfixes for critical bugs may go directly to `main` with explicit approval
- Documentation-only changes (typos, formatting) may skip PR if trivial
