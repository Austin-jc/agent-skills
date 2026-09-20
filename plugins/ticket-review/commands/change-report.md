---
description: Produce a plain-language Change Report from the diff on this branch. Usage: /change-report [PROJ-123] [--base main] [--working-tree]
---
Use the ticket-review skill in Change Report mode for: $ARGUMENTS

Run the diff inventory first (pass --base or --working-tree through if given), read the inventory, pull hunks only for files the report needs, then write the report and run the gate until it passes. Write from the diff, not from memory of this session.
