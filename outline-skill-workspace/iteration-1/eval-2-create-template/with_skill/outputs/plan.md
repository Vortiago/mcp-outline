# Plan: Create "Incident Response Runbook" Template

## Step 1 -- Find the Engineering collection ID

**Tool:** `list_collections`
**Arguments:** *(none)*

**Why:** Every document belongs to a collection, and `create_document` requires a `collection_id`. Per the skill guide, use `list_collections` to discover available collections and find the UUID for the "Engineering" collection.

From the response, identify the entry whose name is "Engineering" and note its `id` (e.g. `abcd1234-...`).

---

## Step 2 -- Create the document as a template

**Tool:** `create_document`
**Arguments:**

| Parameter       | Value |
|-----------------|-------|
| `title`         | `"Incident Response Runbook"` |
| `collection_id` | *UUID obtained from Step 1* (e.g. `"abcd1234-..."`) |
| `template`      | `True` |
| `text`          | *(full markdown below)* |

**Markdown content for `text`:**

```markdown
## Purpose

This runbook provides a standardized process for responding to production incidents. Use this template each time a new incident is declared.

## Severity Levels

| Level | Name     | Description                                                     | Response Time | Examples                                  |
|-------|----------|-----------------------------------------------------------------|---------------|-------------------------------------------|
| SEV-1 | Critical | Complete service outage or data loss affecting all users        | Immediate     | Full platform down, data breach           |
| SEV-2 | Major    | Significant degradation affecting a large subset of users       | 15 minutes    | Core feature broken, major API failures   |
| SEV-3 | Minor    | Partial degradation with a workaround available                 | 1 hour        | Non-critical feature broken, slow queries |
| SEV-4 | Low      | Cosmetic or minor issue with no meaningful user impact          | Next business day | UI glitch, typo in logs               |

### How to Assign Severity

1. Assess the blast radius -- how many users or systems are affected.
2. Determine whether a workaround exists.
3. Consider data integrity -- is any data at risk of loss or corruption?
4. When in doubt, start with a higher severity and downgrade after triage.

## Escalation Path

### SEV-1 (Critical)

1. **Incident Commander (IC):** On-call engineering lead declares the incident.
2. **Notify:** VP of Engineering and CTO within 5 minutes.
3. **Assemble war room:** Pull in relevant service owners immediately.
4. **External comms:** Alert Customer Support and Status Page team within 15 minutes.

### SEV-2 (Major)

1. **Incident Commander:** On-call engineer declares the incident.
2. **Notify:** Engineering Manager within 15 minutes.
3. **Assemble responders:** Ping the relevant team channel.
4. **External comms:** Update the status page if the issue is user-visible.

### SEV-3 (Minor)

1. **Owner:** On-call engineer triages and owns the fix.
2. **Notify:** Team lead via the team channel.
3. **Track:** Create a ticket and link it in the incident channel.

### SEV-4 (Low)

1. **Owner:** Any available engineer picks up the issue.
2. **Track:** Create a ticket in the backlog.

### Escalation Contacts

| Role                | Name          | Contact              |
|---------------------|---------------|----------------------|
| On-call Engineer    | *(rotate)*    | See PagerDuty        |
| Engineering Manager | [Name]        | [Email / Slack]      |
| VP of Engineering   | [Name]        | [Email / Slack]      |
| CTO                 | [Name]        | [Email / Slack]      |

## Communication Templates

### Incident Declaration (Internal -- Slack)

> **Incident Declared -- [SEV-X] [Short Description]**
>
> **Impact:** [Describe what is broken and who is affected]
> **Status:** Investigating
> **Incident Commander:** [Name]
> **Channel:** #incident-[number]
>
> Please join the channel if you can help. Do not deploy until the all-clear is given.

### Status Page Update (External)

> **[Service Name] -- Degraded Performance / Major Outage**
>
> We are aware of an issue affecting [describe impact]. Our engineering team is actively investigating. We will provide an update within [30 / 60] minutes.
>
> *Last updated: [timestamp]*

### Incident Resolved (Internal -- Slack)

> **Incident Resolved -- [SEV-X] [Short Description]**
>
> **Duration:** [start time] to [end time] ([total duration])
> **Root Cause:** [One-line summary]
> **Action Items:** A post-mortem will be scheduled within 48 hours.
>
> Deploys are now unblocked. Thank you to everyone who helped.

### Post-Mortem Meeting Invite

> **Subject:** Post-Mortem -- [Incident Title] ([Date])
>
> **Agenda:**
> 1. Timeline of events
> 2. Root cause analysis
> 3. What went well
> 4. What could be improved
> 5. Action items and owners
>
> Please review the incident channel log before the meeting.

## Checklist

- [ ] Severity assigned
- [ ] Incident Commander identified
- [ ] Communication sent to the appropriate channels
- [ ] Status page updated (if user-visible)
- [ ] Deploys paused (SEV-1 / SEV-2)
- [ ] Post-mortem scheduled within 48 hours
- [ ] Action items tracked in the issue tracker
```

---

## Summary

The plan requires exactly **two** tool calls:

1. `list_collections` -- to resolve the "Engineering" collection name to its UUID.
2. `create_document(title, collection_id, text, template=True)` -- to create the document as a template so it appears in Outline's "New from template" picker.

No additional calls are needed. The `template=True` flag ensures the document is registered as a template rather than a regular page in the collection tree.
