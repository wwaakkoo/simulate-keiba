# Task Completion Guidelines

When a task is completed, ensure the following:

1. **Linting and Formatting**:
   - Backend: Run `ruff check app/` and ensure no errors.
   - Frontend: Run `npm run lint` and `npm run format`.
2. **Testing**:
   - Run all relevant tests (pytest for backend, vitest for frontend).
   - Aim for at least 80% coverage.
3. **Type Safety**:
   - Verify no type errors with `mypy` and `tsc`.
4. **Documentation**:
   - Update `README.md` or other docs if necessary.
5. **Code Review Criteria**:
   - No `any` types.
   - No `console.log`.
   - All functions have type hints.
