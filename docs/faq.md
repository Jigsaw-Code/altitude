# Frequently Asked Questions

## Who built Altitude?

Jigsaw and Tech Against Terrorism developed Altitude in collaboration with the
Global Internet Forum to Counter Terrorism (GIFCT).

## Who maintains Altitude?

Altitude is now fully supported and maintained by Tech Against Terrorism. Tech
Against Terrorism will continue to make technical improvements to make Altitude
more effective and easy to use as threats evolve. Altitude users will get all of
those enhancements and context automatically.

## How can I receive onboarding support for Altitude?

Altitude is free for platforms to use. It is also offered as part of Tech Against
Terrorism’s Bronze tier partnership.
[Learn more and request access](https://techagainstterrorism.org/altitude-content-moderation-tool)
to get started today.

## How is removed content stored?

All content uploaded to the tool remains archived locally, even when you remove
it from your platform. This allows you to review this content later and retain
a copy for archiving. If you want to delete it from Altitude, you will need to
take further steps to remove it from the database.

## How does the flagger priority work?

Our tool prioritizes all cases for review to help you focus on the most critical
content first. This is done based entirely on flagger metadata. Here's how it
works:

### Scoring

Each case is supported by 1+ signals. Each case receives a score from 0-10,
calculated by adding its Confidence and Severity scores, which are derived from
the supporting flagger signals:

- **Confidence:** How likely the content is to be a true threat, based on
  metadata like whether the signal was provided by a human flagger or whether
  the flagger is considered trusted.
- **Severity:** How urgently action is needed, based on metadata like whether
  the flagger marked the signal as part of an imminent credible threat.

Example:

| Case                                        | Confidence | Severity | Total Score | **Priority level** |
| ------------------------------------------- | :--------: | :------: | :---------: | :----------------: |
| Terrorist attack threat from trusted source |     3      |    7     |     10      |      **High**      |
| Violent image                               |     1      |    3     |      4      |     **Medium**     |
| User report without metadata                |     1      |    1     |      2      |      **Low**       |

> [!NOTE]
> The severity score is heavily weighted to ensure that cases containing
> critical threats are always addressed first.

### Ranking

Cases are ranked from highest to lowest score. In the frontend they will be
labeled by their flagger priority level ("High priority", "Medium priority", or
"Low priority"). If we there is no flagger data available for scoring, the case
will be labeled "N/A".

## What does sharing diagnostics entail?

Sharing Diagnostics is a feature within Altitude that creates a feedback loop
between online platforms and sources of content alerts (e.g. counter-terrorism
databases like Tech Against Terrorism’s Terrorist Content Analytics Platform
(TCAP) and GIFCT's Hash-Sharing Database). When users make decisions on flagged
content, those decisions are securely recorded and shared with the alert sources
via APIs. This feedback helps the alert sources refine their content analysis,
leading to improved accuracy and effectiveness in flagging harmful content.

The process is passive and privacy-focused. Decisions are shared in the
background weekly (configured in
[signal-service/src/taskqueue/config.py](../signal-service/src/taskqueue/config.py))
without requiring user action, and platform owners can control which alert
sources receive their data. Additionally, only relevant decision data is shared,
and any unnecessary information is removed to protect user and company privacy.
Specifically, only the identifier of the content (e.g. URL) and the decision
taken (e.g. BLOCK, APPROVE) is included.

While primarily focused on improving the accuracy of content alerts, Sharing
Diagnostics also promotes transparency by allowing alert sources to demonstrate
their effectiveness to stakeholders. It fosters collaboration between platforms
and alert sources, strengthening the collective effort against online extremism.

## How does Altitude handle authentication?

Altitude does not provide authentication, as most platforms already have a
preferred method of authentication, like Single Sign-On. You'll need to take
care of authentication yourself. The Altitude gateway (see
[gateway/](../gateway/)) uses nginx, to which you could add
[basic](https://docs.nginx.com/nginx/admin-guide/security-controls/configuring-http-basic-authentication/)
or
[external](https://docs.nginx.com/nginx/admin-guide/security-controls/configuring-subrequest-authentication/)
authentication.

## Can multiple users access Altitude?

Yes. Altitude does not provide user accounts, but multiple users can use the
tool at the same time.

## How do I change the UI to to rename the _"Remove"_ review decision?

We understand that not all platforms deal with content the same way. Maybe you
block content or take another action instead of removing it, and want the action
buttons in the UI to reflect that. There is currently no way to configure this
type of language directly in the UI. However, you can update it in the
underlying config at
[client/src/app/admin/config.ts](../client/src/app/admin/config.ts).

## How do I add other sources of signals?

Altitude can be extended to integrate with more sources. If you'd like to add a
new integration, we welcome contributions!
