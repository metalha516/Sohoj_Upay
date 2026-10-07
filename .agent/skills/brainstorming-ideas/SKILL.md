---
name: brainstorming-ideas
description: >-
  Turns ideas into fully formed designs and specs through collaborative
  dialogue. Use BEFORE any creative work — creating features, building
  components, adding functionality, or modifying behavior. Activate when the
  user says "brainstorm", "let's think through", "design this", "I have an
  idea", or describes a new feature/project.
---

# Brainstorming Ideas Into Designs

Help turn ideas into fully formed designs and specs through natural
collaborative dialogue. Start by classifying how much process the request
needs, then work through your path: understand the context, refine the idea,
present a design, and get approval.

**Announce at start:** "I'm using the brainstorming skill to help shape this
idea before we build anything."

## When to Use This Skill

- User describes a new feature, project, or component to build
- User says "brainstorm", "let's think through", "design this"
- Before ANY creative/building work — never jump straight to code
- When modifying existing behavior in non-trivial ways

## The Hard Gate

> [!CAUTION]
> Before taking ANY implementation action — writing code, scaffolding,
> installing dependencies, or creating a project — complete the selected
> path's approval. A reply approves the stage actually presented.
> Approval of an idea does NOT approve artifacts that don't exist yet.
> Read-only project exploration IS allowed while prerequisites remain
> incomplete.

## Three Paths

Before your first question, **classify the request and say it out loud** so
the user can override:

### Spike
A feasibility question ("can we...", "is it possible...", "quick and dirty").
Output is an answer, not code you keep.

- Present the question and what you'll try in 2-3 sentences
- Get a nod, then investigate as cheaply as correctness allows
- No design doc, no spec. Report findings as a recommendation
- Anything built stays labeled throwaway

### Bounded
A well-scoped change to code that already exists: a new flag, a small
endpoint, a one-file fix. **Bounded means the flow you are changing is
already here to read.** If there is no existing flow, the task is NOT bounded.

- Ask the clarifying questions that matter
- Present a short design IN CHAT (a few sentences to a few short paragraphs)
- **STOP and wait for explicit approval** before implementing
- No spec file, no implementation plan document

### Architectural
New projects, new subsystems, changes that restructure how components fit
together or alter interfaces others depend on.

- Follow the full process: questions → approaches → design → spec → plan
- Full written spec saved to `docs/specs/YYYY-MM-DD-<topic>-design.md`

> [!IMPORTANT]
> When in doubt between two paths, take the heavier one. The ratchet is
> one-way: hidden complexity discovered mid-task upgrades the path — stop,
> say so, and step up. Nothing downgrades mid-task.

## Workflow Checklists

### Spike Checklist

- [ ] Explore project context — enough to frame the probe
- [ ] Present question + probe plan — 2-3 sentences
- [ ] Get approval — a nod is enough
- [ ] Investigate — as cheaply as correctness allows
- [ ] Report findings — recommendation; label anything built as throwaway

### Bounded Checklist

- [ ] Explore project context — check files, docs, recent commits
- [ ] Ask clarifying questions — one at a time, the ones that matter
- [ ] Present short design in chat — approach, files touched, testing
- [ ] **Get approval** — STOP and wait for explicit yes
- [ ] Implement — proceed with normal development workflow (TDD applies)

### Architectural Checklist

- [ ] Explore project context — check files, docs, recent commits
- [ ] Ask clarifying questions — one at a time; understand purpose,
      constraints, success criteria
- [ ] Propose 2-3 approaches — with trade-offs and your recommendation
- [ ] Present design — in sections scaled to complexity; get approval after
      each section
- [ ] Write design doc — save to `docs/specs/YYYY-MM-DD-<topic>-design.md`
      and commit
- [ ] Spec self-review — check for placeholders, contradictions, ambiguity
- [ ] User reviews written spec — ask user to review before proceeding
- [ ] Transition to planning — invoke writing-plans skill

## Establish Shared Understanding

1. **Discover intent** — Use the request and context to identify the intended
   outcome, who it's for, and what success looks like. When that information
   is missing, ask one focused question about purpose before proposing
   features.

2. **Write back your understanding** — Summarize the intended outcome,
   constraints, and success criteria. Separate what they said from
   assumptions. Invite correction.

3. **Carry intent into the design** — Preserve the agreed understanding in
   the design artifact. Check proposed features against that understanding.

When the request already supplies purpose and constraints, reflect that
understanding instead of re-asking.

## The Process (Bounded & Architectural)

**Understanding the idea:**

- Check out the current project state first (files, docs, recent commits)
- Before detailed questions, assess scope: if the request describes multiple
  independent subsystems, flag this immediately
- If too large for a single spec, help decompose into sub-projects
- Ask questions **one at a time** to refine the idea
- Prefer multiple-choice questions when possible
- Focus on: purpose, constraints, success criteria

**Exploring approaches (architectural):**

- Propose 2-3 different approaches with trade-offs
- Lead with your recommended option and explain why
- YAGNI ruthlessly — remove unnecessary features from every approach

**Presenting the design:**

- Scale each section to its complexity: a few sentences if straightforward,
  up to 200-300 words if nuanced
- Ask after each section whether it looks right so far
- Cover: architecture, components, data flow, error handling, testing
- Be ready to go back and clarify

**Design for isolation and clarity:**

- Break the system into smaller units with one clear purpose each
- Communicate through well-defined interfaces
- For each unit: what does it do, how do you use it, what does it depend on?
- Smaller, well-bounded units are easier to reason about and test

**Working in existing codebases:**

- Explore current structure before proposing changes. Follow existing patterns
- Where existing code has problems affecting the work, include targeted
  improvements as part of the design
- Don't propose unrelated refactoring

## After the Design (Architectural Path)

**Write the spec:**
- Save to `docs/specs/YYYY-MM-DD-<topic>-design.md`
- Commit the design document to git

**Spec self-review:**
1. **Placeholder scan** — Any "TBD", "TODO", incomplete sections? Fix them
2. **Internal consistency** — Any contradictions between sections?
3. **Scope check** — Focused enough for a single implementation plan?
4. **Ambiguity check** — Could any requirement be interpreted two ways?

Fix issues inline. No need to re-review.

**User review gate:**
> "Spec written and committed to `<path>`. Please review it and let me know
> if you want changes before we start the implementation plan."

Wait for the user's response. Only proceed once approved.

**Transition:** Invoke the writing-plans skill to create the implementation
plan. Do NOT invoke any other skill.

## Red Flags

| Thought | Reality |
|:--------|:--------|
| "This is too simple to need a design" | Follow the selected path. Bounded gets a short chat design; architectural gets the full spec |
| "I'll call it bounded and skip the spec" | Reaching for a label to skip work IS the doubt — take the heavier path |
| "It's bounded and obvious — I'll start while they read" | The gate is approval, not the design's length. Present, then stop |
| "I understand this kind of app, so it's bounded" | Bounded measures the REPO, not your familiarity. New project = architectural |
| "The spike works, so I'll keep the code" | A spike's output is an answer. Keeping the code is a new request — classify it |
| "They approved the spike, so the follow-up is approved too" | Each task gets its own classification and its own approval |

## Resources

- [`resources/spec-reviewer-prompt.md`](resources/spec-reviewer-prompt.md) —
  Template for reviewing spec documents before planning
