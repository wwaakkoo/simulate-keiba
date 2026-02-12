# Style and Conventions

## General Rules
- Use absolute paths for file operations.
- All functions must have type hints (Python).
- No `any` type in TypeScript; use `unknown` instead.
- No `console.log` in production code.

## Naming Conventions
### Frontend (TS/TSX)
- Files: `kebab-case.ts` / `PascalCase.tsx`
- Classes/Components: `PascalCase`
- Functions/Variables: `camelCase`
- Constants: `UPPER_SNAKE_CASE`

### Backend (Python)
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/Variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

## Design Principles
- Separation of concerns: Clear split between frontend (display) and backend (logic).
- Test-first approach.
