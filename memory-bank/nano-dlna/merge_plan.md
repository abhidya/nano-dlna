# Worktree Merge Plan

## Current State
- **Master branch**: Has uncommitted changes (10 modified + 2 untracked files)
- **locks-fix**: Already merged (clean working tree)
- **api-typing**: Committed (ea88835)
- **cli-types**: Committed (7a4cdac)
- **thread-simplify**: Committed (996a913)

## Merge Order (Recommended)
1. **First**: Commit master branch changes
2. **Second**: Merge api-typing (API return types)
3. **Third**: Merge cli-types (CLI type annotations)
4. **Fourth**: Merge thread-simplify (threading architecture)

## Pre-merge Checklist
- [ ] Commit master branch changes
- [ ] Run tests on each worktree
- [ ] Check for conflicts between branches
- [ ] Backup current state

## Merge Commands
```bash
# 1. Commit master changes
git add .
git commit -m "fix: DeviceManager lock consolidation and test updates"

# 2. Merge api-typing
git merge api-typing

# 3. Merge cli-types  
git merge cli-types

# 4. Merge thread-simplify
git merge thread-simplify

# 5. Clean up worktrees
git worktree remove ../nano-dlna-api-typing
git worktree remove ../nano-dlna-cli-types
git worktree remove ../nano-dlna-locks-fix
git worktree remove ../nano-dlna-thread-simplify
```

## Post-merge Tasks
- [ ] Run full test suite
- [ ] Update documentation
- [ ] Tag release if appropriate
- [ ] Push to origin