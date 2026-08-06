---
paths:
  - "src/**/*.tsx"
  - "src/**/*.jsx"
  - "src/components/**"
  - "packages/frontend/**"
---

# React Best Practices (Example Sector-Specific Rule)

> This is an EXAMPLE path-scoped rule. Copy and adapt it for your project's
> frontend framework. Create similar files for backend, infra, ML, etc.
> This rule only loads when editing files matching the paths above.

## Components
- Functional components only with hooks — no class components
- Prefer composition over inheritance
- Keep components under 200 lines; extract sub-components when larger

## Styling
- Use your project's chosen CSS approach (Tailwind, CSS Modules, styled-components, etc.)
- Maintain consistent spacing and color tokens from the design system

## State Management
- Colocate state as close to where it's used as possible
- Lift state only when shared between siblings
- Use appropriate state management for complexity (context, Zustand, TanStack Query, etc.)

## Accessibility
- All interactive elements must be keyboard-navigable
- Use semantic HTML elements (button, nav, main, etc.)
- Include aria-labels on icon-only buttons
- Test with screen reader when adding new interactive components

## Testing
- Unit test complex logic and custom hooks
- Integration test user-facing workflows
- Snapshot tests only for stable, rarely-changed components
