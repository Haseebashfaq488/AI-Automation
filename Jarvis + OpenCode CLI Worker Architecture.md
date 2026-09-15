# Jarvis + OpenCode CLI Worker Architecture

## 1. Purpose

The goal is to make **Jarvis the manager and orchestrator**, while OpenCode acts as one of Jarvis's coding workers.

Jarvis should not perform the actual coding work itself. Instead, Jarvis should:

1. Understand the user's request.
2. Break the work into meaningful milestones.
3. Select OpenCode when a coding worker is appropriate.
4. Prepare a detailed prompt for the current milestone.
5. Send that prompt to OpenCode without opening the interactive OpenCode TUI.
6. Monitor the worker's progress and result.
7. Verify whether the milestone was actually completed.
8. Report the result to the user.
9. Continue with the next milestone using the **same OpenCode session**.
10. Handle failures, corrections, and blocked tasks.

The objective is to create a manager/worker relationship rather than another chatbot interface.

---

# 2. What We Do NOT Want

When OpenCode is started normally, it opens its full-screen terminal user interface (TUI). That interface is useful for a human who wants to sit in front of OpenCode and chat with it.

That is **not** the interface Jarvis should use.

We do not want:

- Jarvis opening the OpenCode TUI.
- Jarvis pretending to be a human typing into the TUI.
- Jarvis repeatedly creating new OpenCode conversations.
- Jarvis manually copying the entire previous conversation into every new prompt.
- Jarvis depending on visual automation of the terminal.
- Jarvis acting as the coder itself.

Instead, Jarvis should use OpenCode's **non-interactive CLI capabilities** and, where appropriate, its headless server/API capability.

---

# 3. OpenCode Has Two Different Ways of Being Used

## Interactive Mode

Running OpenCode normally starts the TUI.

The normal experience is:

**Human → OpenCode → Chat → OpenCode works on the project**

This mode is intended for direct human interaction.

## Non-Interactive Mode

OpenCode also provides a `run` command.

This allows a prompt to be submitted directly without opening the interactive interface.

The desired experience is:

**Jarvis → OpenCode run → Worker performs task → Result returned to Jarvis**

This mode is much more appropriate for automation because Jarvis does not need to interact with a visual terminal interface.

---

# 4. Why the OpenCode CLI Is Suitable for Jarvis

OpenCode provides capabilities that fit the planned worker architecture.

Important capabilities include:

- Non-interactive execution through `run`
- Session continuation
- Specific session IDs
- JSON output
- Working-directory selection
- Model selection
- Agent selection
- Permission and automatic-execution controls
- Connection to a running OpenCode server
- Headless server mode
- Session listing and management

These capabilities allow OpenCode to function as a proper worker rather than only as an interactive coding chatbot.

---

# 5. The Most Important Concept: OpenCode Sessions

A **session** is the persistent conversation and work context that OpenCode maintains for a task.

This is extremely important for Jarvis.

We do **not** want this:

**Task**

→ OpenCode conversation 1  
→ Result  
→ New OpenCode conversation 2  
→ Resend all context  
→ Result  
→ New OpenCode conversation 3  
→ Resend all context

Instead, we want:

**Task**

→ OpenCode Session A  
→ Milestone 1  
→ Milestone 2  
→ Milestone 3  
→ Milestone 4  
→ Final verification

All of these milestones belong to the same worker session.

The session therefore becomes the worker's ongoing context for a particular task.

---

# 6. How Jarvis Should Think About a Session

Every Jarvis coding task should conceptually have a worker record containing:

- Jarvis task ID
- Worker type
- Project/workspace
- OpenCode session ID
- Current milestone
- Current status
- Previous milestone results
- Verification status
- Final result

The **OpenCode session ID** is particularly important.

Once Jarvis starts a task and establishes its OpenCode session, Jarvis should remember that session ID and use it whenever the next milestone is sent.

This allows OpenCode to retain the context of the work already performed.

---

# 7. Example of a Single Task

Suppose the user tells Jarvis:

> Build authentication for my backend.

Jarvis should not immediately send the entire request as one enormous coding instruction.

Instead, Jarvis creates a plan.

### Milestone 1 — Understand the Project

OpenCode is instructed to inspect the existing project and understand:

- Existing authentication
- User model
- Database structure
- Existing API endpoints
- Middleware
- Tests
- Relevant configuration

The worker should initially focus on understanding the project and producing findings.

Jarvis receives the result.

Jarvis then verifies the result and reports to the user:

> Milestone 1 completed. OpenCode analyzed the authentication architecture and identified the relevant files and implementation requirements.

---

# 8. Continuing the Same Session

Jarvis then sends the next milestone to the **same OpenCode session**.

### Milestone 2 — Implement Authentication

The prompt can refer to the previous analysis because OpenCode is continuing the existing session.

The worker can now:

- Modify the relevant files
- Implement the required functionality
- Run appropriate commands
- Run tests
- Report what it changed

Jarvis receives the result.

The important point is:

> **Milestone 2 is not a new worker conversation.**

It continues the same OpenCode session created for the overall task.

---

# 9. Milestone 3 — Testing

After implementation, Jarvis can continue the same session again.

The next milestone can ask OpenCode to:

- Run the relevant tests
- Identify failures
- Fix implementation problems
- Re-run the tests
- Report the final state

Again, the same OpenCode session is used.

This gives OpenCode continuity across the entire task.

---

# 10. Why Milestones Are Better Than One Huge Prompt

The milestone approach gives Jarvis control over the worker.

A large task can be divided into meaningful stages such as:

1. Analyze
2. Plan
3. Implement
4. Test
5. Fix
6. Review
7. Final verification

Jarvis can observe the result after every important stage.

This also means the user can see what is happening instead of waiting for a large task to finish with no visibility.

The milestones should be meaningful units of work, not arbitrary pieces of text.

For example, this is useful:

**Milestone 1:** Analyze the existing authentication system.

**Milestone 2:** Implement the authentication changes.

**Milestone 3:** Run tests and fix failures.

This is not useful:

**Chunk 1:** Write the first 20% of the code.

**Chunk 2:** Write the next 20%.

The chunks should represent actual logical stages of work.

---

# 11. Jarvis Should Generate the Worker Prompts

Jarvis's most important responsibility is producing good worker instructions.

A worker prompt should contain enough information for OpenCode to perform the current milestone properly.

A typical prompt should communicate:

### Overall Task

What the user ultimately wants.

### Current Milestone

Exactly what OpenCode should accomplish now.

### Project Context

Which project/workspace the worker is operating in and any relevant background.

### Requirements

Specific functional and technical requirements.

### Constraints

What the worker must not change or break.

### Expected Behavior

What the completed milestone should achieve.

### Verification Criteria

How OpenCode should determine whether the milestone succeeded.

### Reporting Requirements

What OpenCode should tell Jarvis when the milestone is complete.

Jarvis should generate these prompts dynamically rather than relying on one static prompt.

---

# 12. Jarvis Is the Supervisor

OpenCode should not be considered the authority on whether a task is complete.

OpenCode can report:

> Done.

But Jarvis should still verify the result.

The desired relationship is:

**User**

↓

**Jarvis**

↓

**OpenCode**

↓

**Project**

↓

**OpenCode Result**

↓

**Jarvis Verification**

↓

**User**

Jarvis therefore has two different sources of information:

1. What the worker claims it accomplished.
2. What the project and verification results actually show.

The second source should be used to validate the first.

---

# 13. Worker Status

Jarvis should conceptually maintain statuses such as:

### Planning

Jarvis is preparing the task.

### Assigned

A worker has been selected.

### Running

OpenCode is actively working.

### Waiting

The worker has reached a point where it needs additional direction or input.

### Verification

Jarvis is checking the worker's result.

### Completed

The milestone has been successfully verified.

### Failed

The milestone did not meet its requirements.

### Blocked

The worker cannot continue without information, permission, or another dependency.

These statuses allow Jarvis to communicate useful progress to the user.

---

# 14. OpenCode JSON Output

For automation, OpenCode supports a JSON output format for non-interactive execution.

This is useful because Jarvis should not have to interpret the visual formatting of a terminal.

Instead, structured events can be consumed by the worker-management layer.

This makes it possible for Jarvis to understand events such as:

- Worker responses
- Tool activity
- Command execution
- File-related activity
- Completion
- Errors

Jarvis can then convert these events into human-friendly progress updates.

For example:

> OpenCode is currently running the authentication tests.

or:

> OpenCode completed the implementation milestone and returned the verification results.

The goal is not to expose raw OpenCode output to the user all the time. Jarvis should interpret it and provide useful progress information.

---

# 15. Headless OpenCode Server

OpenCode also provides a **headless server mode**.

The purpose of this mode is to expose OpenCode functionality without opening the TUI.

Conceptually:

**Jarvis**

↓

**OpenCode Headless Server**

↓

**OpenCode Sessions**

↓

**Project / Workspace**

This is particularly useful for Jarvis because the worker can remain available while Jarvis sends multiple requests to it.

A persistent server can also reduce unnecessary startup overhead and provide a cleaner separation between the Jarvis manager and the OpenCode worker.

The OpenCode server/API capability is therefore a strong candidate for the long-term worker architecture.

---

# 16. Two Possible Automation Approaches

There are two relevant approaches.

## Approach A — Direct Non-Interactive Runs

Jarvis sends prompts using OpenCode's non-interactive `run` capability.

### Advantages

- Simple
- Easy to understand
- Good for initial testing
- No TUI interaction
- Suitable for scripts and automation

This is a good starting point for proving the worker concept.

## Approach B — Persistent Headless OpenCode Server

Jarvis communicates with a running OpenCode server and manages sessions through that environment.

### Advantages

- More suitable for a long-running Jarvis worker
- Avoids unnecessary repeated startup
- Provides a clearer separation between Jarvis and the worker
- Better foundation for persistent workers
- Provides API-based interaction rather than TUI automation

For the eventual Jarvis architecture, the **headless server approach is the stronger long-term direction**.

---

# 17. The Planned OpenCode Worker

OpenCode should eventually be treated as a worker with a standard conceptual interface.

### Worker Identity

**OpenCode**

### Worker Type

**Coding / Software Development Agent**

### Main Capabilities

- Understand existing codebases
- Read project files
- Modify project files
- Create project files
- Run development commands
- Run tests
- Debug problems
- Refactor code
- Analyze project structure

### Jarvis Responsibilities

- Decide when OpenCode should be used
- Create the overall plan
- Divide the task into milestones
- Create detailed prompts
- Establish the OpenCode session
- Continue the same session
- Monitor the worker
- Verify results
- Decide whether another milestone is needed
- Report progress to the user
- Handle failures

---

# 18. Future Worker Architecture

OpenCode should be the first worker, not the only worker.

Eventually the architecture should look conceptually like this:

**JARVIS — Manager / Orchestrator**

├── **OpenCode Worker**  
│   └── CLI / headless coding agent

├── **Cline Worker**  
│   └── VS Code coding agent

├── **Word Worker**  
│   └── Document tasks

├── **Excel Worker**  
│   └── Spreadsheet tasks

└── **Future Workers**

Jarvis should not need to fundamentally change its management process whenever a new worker is added.

Worker-specific details should remain inside each worker integration.

---

# 19. Why OpenCode Is a Good First Worker

OpenCode is particularly suitable as the first worker because its CLI provides capabilities designed for automation.

The important capabilities for this project are:

- Non-interactive `run`
- Session continuation
- Session IDs
- JSON output
- Working-directory selection
- Model and agent selection
- Headless server mode
- Session management
- API access

This means we are not trying to force an interactive application into an automation workflow. OpenCode already exposes interfaces intended for programmatic use.

---

# 20. The Final Desired Experience

The user should eventually be able to tell Jarvis:

> Fix the authentication system in my project and make sure all tests pass.

Jarvis should internally do the following:

### Phase 1 — Planning

Understand the task and create milestones.

### Phase 2 — Worker Assignment

Select OpenCode.

### Phase 3 — Session Creation

Create or establish an OpenCode session associated with the task.

### Phase 4 — Milestone 1

Send a detailed analysis prompt.

### Phase 5 — Monitoring

Receive the worker's result.

### Phase 6 — Verification

Determine whether the analysis milestone was completed.

### Phase 7 — User Update

Tell the user what was accomplished.

### Phase 8 — Milestone 2

Continue the same OpenCode session and send the implementation prompt.

### Phase 9 — Milestone 3

Continue the same session and perform testing.

### Phase 10 — Correction

If tests fail, Jarvis gives OpenCode another detailed instruction in the same session.

### Phase 11 — Final Verification

Jarvis checks whether the requested task has actually been completed.

### Phase 12 — Final Report

Jarvis tells the user:

- What was changed
- What was tested
- What succeeded
- What failed
- What remains
- Whether the task is complete

---

# 21. Core Principle

The most important design principle is:

> **Jarvis owns the task. OpenCode owns the implementation.**

Jarvis should know:

- What needs to happen
- Why it needs to happen
- Which worker should do it
- What the worker should be told
- What milestone comes next
- Whether the result is acceptable

OpenCode should know:

- How to inspect the project
- How to modify the code
- How to execute commands
- How to debug
- How to test
- How to report its implementation work

This separation is what turns Jarvis from another coding chatbot into an actual **AI orchestrator**.

---

# 22. First Implementation Goal

The first goal should be deliberately small.

We should prove this complete workflow:

**Jarvis → OpenCode Non-Interactive Worker → One Project → One Session → One Milestone → Result → Jarvis**

Once this works reliably, expand it to:

**Jarvis → OpenCode Session → Multiple Milestones → Verification → Correction → Final Report**

Only after that should we add Cline or additional workers.

---

# 23. Final Architecture

The intended architecture is:

```text
                         YOU
                          │
                          ▼
                       JARVIS
                 Manager / Orchestrator
                          │
                 ┌────────┴────────┐
                 │                 │
            Planning         Worker Manager
                                   │
                                   ▼
                         OpenCode Worker
                                   │
                         Headless / CLI
                                   │
                         OpenCode Session
                                   │
              ┌────────────────────┼───────────────────┐
              │                    │                   │
         Milestone 1          Milestone 2         Milestone 3
         Analyze              Implement             Test
              │                    │                   │
              └────────────────────┴───────────────────┘
                                   │
                                   ▼
                           Jarvis Verification
                                   │
                                   ▼
                              User Report
```

The critical part is that **Milestone 1, Milestone 2, and Milestone 3 can all remain inside the same OpenCode session**.

This gives the worker continuity while allowing Jarvis to remain in control of the overall task.

---

# 24. Summary

The planned system is not intended to replace OpenCode.

It is intended to **control OpenCode**.

OpenCode remains the specialized coding worker.

Jarvis becomes the higher-level intelligence that:

**Understands → Plans → Assigns → Prompts → Monitors → Verifies → Continues → Reports**

The first worker integration should therefore focus on OpenCode's non-interactive CLI and session capabilities rather than its interactive TUI.

Once that foundation works, the same orchestration philosophy can be extended to Cline and other specialized workers.

## References

OpenCode CLI documentation:
https://dev.opencode.ai/docs/cli/

OpenCode server documentation:
https://dev.opencode.ai/docs/server/

OpenCode CLI command documentation:
https://opencode.ai/v2/docs/cli/commands/

The exact flags and behavior should be checked against the installed OpenCode version when implementation begins, because CLI capabilities can change between releases.