---
description: Produce a plain-language Ticket Brief before implementing. Usage: /ticket-brief PROJ-123  or  /ticket-brief path/to/ticket.md
---
Use the ticket-review skill in Ticket Brief mode for: $ARGUMENTS

If the argument looks like a Jira key, run the pre-phase with --jira. If it is a path, use --file. If nothing was given, ask for the ticket text and save it to .ticket-review/raw-ticket.md before running the pre-phase.

Do not write any implementation code. Finish by presenting the brief and asking for approval of the task list in section seven.
