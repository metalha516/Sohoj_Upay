---
name: writing-plans
description: >-
  Creates structured implementation plans from specs or requirements before
  touching code. Use when the user says "write a plan", "create an
  implementation plan", "plan this feature", or after a brainstorming/design
  phase produces a spec that needs execution steps.
---

# Writing Implementation Plans

Write plans for an engineer who has never seen this codebase or spec. Assume
they write idiomatic code once they know the exact interface and exact test.
What they cannot know is what you decided: which files, which names and
signatures, which values from the spec, which tests prove each task. Document
those decisions. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD.
Frequent commits.

**Announce at start:** "I'm using the writing-plans skill to create the
implementation plan."

**Save plans to:** `docs/plans/YYYY-MM-DD-<feature-name>.md`
(User preferences for plan location override this default.)

## When to Use This Skill

- A spec or design doc exists and needs to become actionable tasks
- User says "plan this", "write a plan", "implementation plan"
- After a brainstorming session produces an approved design
- Before any multi-step coding work begins

## Workflow

- [ ] **Read the spec** — Understand requirements, constraints, success criteria
- [ ] **Scope check** — If spec covers multiple subsystems, suggest separate plans
- [ ] **Map file structure** — List files to create/modify with responsibilities
- [ ] **Define tasks** — Break work into right-sized, independently testable units
- [ ] **Write steps** — Each step = one action with a checkable result
- [ ] **Self-review** — Check coverage, consistency, proportion
- [ ] **Present to user** — Get approval before any execution begins

## Scope Check

If the spec covers multiple independent subsystems, suggest breaking into
separate plans — one per subsystem. Each plan should produce working, testable
software on its own.

## File Structure Section

Before defining tasks, map out which files will be created or modified:

- Design units with clear boundaries and well-defined interfaces
- Prefer smaller, focused files over large ones doing too much
- Files that change together should live together — split by responsibility
- In existing codebases, follow established patterns

## Task Right-Sizing

A task is the smallest unit that carries its own test cycle. When drawing
task boundaries:
- Fold setup, configuration, and scaffolding into the task whose deliverable
  needs them
- Split only where a reviewer could meaningfully reject one task while
  approving its neighbor
- Each task ends with an independently testable deliverable

## Plan Document Template

Every plan must start with this header:

```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

**Spec:** [Path to the spec/design doc this plan implements]

## Global Constraints

[Project-wide requirements — version floors, dependency limits, naming rules,
platform requirements — one line each with exact values from the spec.]

## Review Focus

[The five input classes or failure modes the spec implies but no task's tests
exercise — one line each, naming the input/condition and expected behavior.]

---
```

## Task Structure Template

```markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.ext`
- Modify: `exact/path/to/existing.ext`
- Test: `tests/exact/path/to/test.ext`

**Interfaces:**
- Consumes: [what this task uses from earlier tasks — exact signatures]
- Produces: [what later tasks rely on — exact function names, types]

- [ ] **Step 1: Write the failing test**

\`\`\`python
def test_specific_behavior():
    result = function(input)
    assert result == expected
\`\`\`

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Implement the function**

[One line on approach when signature + test leave a choice.]

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

\`\`\`bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
\`\`\`
```

## Step Granularity Rules

Each step is **one action with a checkable result:**

| Step Type | Contains | Does NOT Contain |
|:----------|:---------|:-----------------|
| Test step | Test name + assertions as code with spec's exact values | Implementation code |
| Code step | Exact signature (name, params, return type), file, spec values | Full body (unless algorithm not determined by signature + tests) |
| Verify step | Command to run + output that means it passed | Ambiguous expected results |
| Reference step | Pointer to another task's Interfaces block | Repeated code from that task |

> [!IMPORTANT]
> A plan longer than the code it describes has written the code instead.
> Lines that decide nothing ("TBD", "handle edge cases", "add appropriate
> validation") are the opposite failure. The self-review catches both.

## Self-Review Checklist

After writing the complete plan, check it against the spec:

1. **Spec coverage** — Skim each requirement. Can you point to a task that
   implements it? List any gaps.
2. **Step scan** — Every step lets the implementer write exactly one
   reasonable thing. No more, no less.
3. **Type consistency** — Do types, method signatures, and property names
   match across tasks? A function called `clearLayers()` in Task 3 but
   `clearFullLayers()` in Task 7 is a bug.
4. **Review Focus** — For each uncovered failure mode, add a test to the
   owning task.
5. **Proportion** — Compare plan length to spec length. If code blocks are
   most of the document, replace bodies with signatures.

If you find issues, fix them inline. No need to re-review.

## Execution Handoff

After saving and self-reviewing the plan, present it to the user for review.
Ask them to confirm it captures what they want before any implementation
begins.

> **"Plan complete and saved to `docs/plans/<filename>.md`. Please review.
> Does it capture what you want? How would you like to proceed with
> implementation?"**

## Anti-patterns

| Thought | Reality |
|:--------|:--------|
| "I'll start coding while they read the plan" | The gate is approval, not the plan's existence |
| "The test is obvious, I'll skip the test step" | Every task needs explicit test code with assertions |
| "I'll add TBD and fill it in later" | Every step must be unambiguous NOW |
| "This plan needs 50 tasks" | Decompose into multiple plans instead |
