# Swift Security And Compliance

These rules are mandatory for Apple-platform work under `r0-work`.

## 1. Security First

- Never hardcode secrets, tokens, API keys, signing material, or private endpoints in source files.
- Prefer Keychain or system-managed secure storage for sensitive credentials.
- Treat local persistence as non-secure by default unless explicit secure storage is used.
- Do not log secrets, auth headers, tokens, personally identifiable information, or raw user content that may be sensitive.

## 2. Platform Compliance

- Respect App Sandbox, entitlements, and privacy permission boundaries.
- Do not request broader permissions than the feature needs.
- When camera, microphone, screen recording, contacts, calendar, photos, Bluetooth, or location are involved:
  - verify the request is in scope
  - verify usage-description keys are required
  - avoid speculative permission flows
- Prefer least-privilege access and explicit user-triggered actions.

## 3. Network Safety

- Default to HTTPS and ATS-compatible networking.
- Do not add insecure transport exceptions unless the user explicitly requests it and understands the compliance impact.
- Validate remote inputs before using them in file paths, shell commands, WebView content, or deep-link routing.
- Avoid loading arbitrary remote HTML/JS into embedded views unless the product explicitly requires it and the safety boundary is reviewed.

## 4. Data Minimization

- Persist only the minimum user data required for the feature.
- Prefer derived/session state over long-term storage when feasible.
- Define clear ownership for cached vs durable state.
- When handling user documents or exported files, keep scope narrow and avoid broad filesystem access.

## 5. Review Checklist

Before completion, explicitly review:

- secrets exposure
- entitlement / sandbox impact
- permission scope
- network transport safety
- sensitive logging
- data persistence scope
