---
name: matt-pocock-skills
description: |
    Pragmatic engineering habits popularized by Matt Pocock:
    1. Grill Me (/grill-me): Relentlessly interview the user to eliminate ambiguity and uncover edge cases before writing code.
    2. Handoff (/handoff): Compress session context into a high-signal markdown artifact for seamless session resets and team handovers.
    3. Strict TDD (/tdd): Enforce test-first red-green-refactor discipline for rock-solid TypeScript and software systems.

    Relevant when:
      - User presents vague or high-level requirements that need deep alignment before coding.
      - Long session context needs to be compressed into a concise summary or handoff doc.
      - Implementing complex TypeScript, API, or state-machine logic.
---

# Matt Pocock Engineering Skills

This skill suite packages three high-impact engineering workflows: **Grill Me**, **Handoff**, and **Pragmatic TDD**.

---

## 1. Grill Me (`/grill-me`)

### Objective

Interview the user relentlessly to eliminate hidden assumptions, resolve ambiguous requirements, and identify edge cases _before_ any implementation begins.

### Protocol

1. **Never jump to code**: If the user provides a prompt with open questions or vague specs, pause and enter grilling mode.
2. **One category at a time**: Group questions logically:
    - **Data & Schema**: What does the data look like? Optional fields? Nullable values?
    - **Edge Cases & Failure**: What happens on offline state, 404, rate limit, duplicate submission, or invalid permissions?
    - **User Flow & UI**: Expected loading states, optimistic updates, skeleton screens, error toasts?
    - **Scope Boundaries**: What is strictly NOT part of this implementation?
3. **Offer concrete multiple-choice options**: Instead of open-ended "What do you want?", suggest 2–3 specific industry-standard alternatives with trade-offs.
4. **Final alignment**: Once all questions are answered, summarize the agreed-upon contract in 4–5 bullet points before writing the first line of code.

---

## 2. Handoff (`/handoff`)

### Objective

Condense a sprawling, context-heavy development session into an ultra-compact, high-signal handoff document.

### Structure of a Handoff Document

When the session is concluding, switching topics, or resetting context, produce a markdown document containing:

```markdown
# Session Handoff: [Feature/Project Name]

## 1. Goal & Context

- Brief summary of what was accomplished and the high-level architecture.

## 2. Completed Milestones

- [x] Feature A implemented (path/to/file.ts)
- [x] Integration tests passing (path/to/test.ts)

## 3. Current State & Active Changes

- Exact file paths modified and key abstractions introduced.
- Status of current test suite.

## 4. Known Gotchas & Decisions Made

- Why approach X was chosen over Y.
- Any workaround or external dependency quirk to watch out for.

## 5. Immediate Next Steps

1. Task 1: [Exact actionable description]
2. Task 2: [Exact actionable description]
```

---

## 3. Pragmatic TDD (`/tdd`)

### Objective

Enforce strict test-first development tailored for modern TypeScript / JavaScript stacks.

### Cycle:

1. **Red**:
    - Write a test using modern test runners (Vitest, Jest, Playwright).
    - Test user observable behavior, not internal implementation details.
    - Run the test and confirm it fails for the exact reason expected.
2. **Green**:
    - Implement the simplest, most straightforward code that satisfies the test.
    - Avoid premature abstraction or over-engineering.
3. **Refactor**:
    - Improve typing (discriminated unions, type guards, eliminating `any`).
    - Clean up code structure while all tests remain green.
