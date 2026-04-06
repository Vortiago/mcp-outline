# Plan: Create "Incident Response Runbook" Template in Outline

## Step-by-Step Tool Calls

### Step 1: Find the Engineering collection ID

**Tool:** `list_collections()`
**Arguments:** _(none)_

**Reason:** I need the `collection_id` for the "Engineering" collection to pass to `create_document`. The `list_collections` tool will return all collections with their IDs and names, and I will locate the one named "Engineering."

---

### Step 2: Create the document as a template

**Tool:** `create_document`
**Arguments:**
```
title: "Incident Response Runbook"
collection_id: <engineering_collection_id from Step 1>
text: <full markdown content below>
publish: true
template: true
```

**Full markdown content for the `text` parameter:**

```markdown
## Purpose

This runbook provides a standardized process for responding to incidents. Use this template when a new incident is declared to ensure consistent response, escalation, and communication across the team.

---

## Severity Levels

| Severity | Description | Examples | Response Time |
|----------|-------------|----------|---------------|
| **SEV-1 (Critical)** | Complete service outage or data loss affecting all users | Production database down, security breach, full API outage | Immediate (within 15 minutes) |
| **SEV-2 (Major)** | Significant degradation affecting a large subset of users | Partial outage, major feature broken, severe performance degradation | Within 30 minutes |
| **SEV-3 (Minor)** | Limited impact on a small number of users or non-critical functionality | Minor feature bug, intermittent errors, single-region issue | Within 2 hours |
| **SEV-4 (Low)** | Minimal or no user impact; cosmetic or minor issues | UI glitch, non-critical logging failure, minor config drift | Next business day |

### How to Determine Severity

1. Assess the **blast radius** — how many users or services are affected.
2. Determine whether there is **data loss or security exposure**.
3. Check if there is a **workaround** available.
4. When in doubt, **escalate to the higher severity** and downgrade later.

---

## Escalation Path

### Tier 1 — On-Call Engineer
- **Who:** Current on-call engineer (see PagerDuty schedule)
- **Responsibilities:**
  - Acknowledge the alert within the response time for the severity level
  - Perform initial triage and diagnosis
  - Attempt first-pass mitigation or rollback
  - Escalate to Tier 2 if unresolved within 30 minutes (SEV-1/2) or 1 hour (SEV-3)

### Tier 2 — Team Lead / Senior Engineer
- **Who:** Engineering team lead or designated senior engineer
- **Responsibilities:**
  - Join the incident channel and take over coordination
  - Bring in additional engineers with domain expertise
  - Decide whether to invoke rollback, feature flag, or hotfix
  - Escalate to Tier 3 if business-critical impact continues beyond 1 hour

### Tier 3 — Engineering Management / VP of Engineering
- **Who:** Engineering Manager or VP of Engineering
- **Responsibilities:**
  - Coordinate cross-team response
  - Authorize emergency changes (e.g., infrastructure scaling, vendor contact)
  - Handle executive communication and status page updates
  - Initiate post-incident review process

### Escalation Decision Tree

1. **Can the on-call engineer resolve it within the target response window?**
   - Yes -> Tier 1 handles to resolution
   - No -> Escalate to Tier 2
2. **Is the issue cross-team or requires architectural decisions?**
   - Yes -> Escalate to Tier 3
   - No -> Tier 2 continues
3. **Is there customer or revenue impact exceeding 1 hour?**
   - Yes -> Escalate to Tier 3 immediately

---

## Communication Templates

### Incident Declaration (Internal - Slack/Teams)

> **[INCIDENT DECLARED] — SEV-{severity} — {short description}**
>
> **Impact:** {describe user/service impact}
> **Started:** {timestamp}
> **Incident Lead:** {name}
> **Channel:** #{incident-channel-name}
>
> We are investigating. Updates will follow every {15/30} minutes.

### Status Update (Internal)

> **[UPDATE] — SEV-{severity} — {short description}**
>
> **Current status:** {investigating / identified / mitigating / resolved}
> **What we know:** {brief summary of findings}
> **Next steps:** {what is being tried next}
> **ETA to resolution:** {estimate or "unknown"}
>
> Next update in {15/30} minutes.

### Customer-Facing Status Page Update

> **Title:** {Service Name} — Degraded Performance / Outage
>
> **Body:**
> We are currently experiencing issues with {service/feature}. Our engineering team is actively investigating and working on a fix. We will provide updates as more information becomes available.
>
> **Last updated:** {timestamp}

### Incident Resolution (Internal)

> **[RESOLVED] — SEV-{severity} — {short description}**
>
> **Duration:** {start time} to {end time} ({total duration})
> **Root cause:** {brief root cause}
> **Resolution:** {what fixed it}
> **Follow-up:** Post-incident review scheduled for {date/time}
>
> Thank you to everyone who helped respond.

### Customer-Facing Resolution

> **Title:** {Service Name} — Resolved
>
> **Body:**
> The issue affecting {service/feature} has been resolved. Service has been restored to normal operation. We apologize for any inconvenience and will be conducting a thorough review to prevent recurrence.

---

## Post-Incident Checklist

- [ ] Incident timeline documented
- [ ] Root cause identified
- [ ] Post-incident review scheduled (within 48 hours for SEV-1/2)
- [ ] Action items created and assigned
- [ ] Customer communication sent (if applicable)
- [ ] Monitoring/alerting gaps addressed
- [ ] Runbook updated with lessons learned
```

---

## Summary

| Step | Tool | Purpose |
|------|------|---------|
| 1 | `list_collections()` | Retrieve the collection ID for "Engineering" |
| 2 | `create_document(title, collection_id, text, publish=true, template=true)` | Create the incident response runbook as a published template |

**Total tool calls: 2**

No additional calls are needed. The `create_document` tool supports `template=true` which marks the document as a template so the team can use "New from template" to create new incident documents from it. Setting `publish=true` ensures it is immediately visible to the team rather than sitting in draft state.
