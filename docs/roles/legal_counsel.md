# Role Brief — Legal Counsel

## Purpose

Ensure that every piece of content Matchday IQ displays, every data source it consumes, and every commercial relationship it enters is legally sound. This role protects the product from IP and licensing risk, keeps user data handling compliant with applicable law, and ensures monetisation is structured correctly from the start.

---

## What this role optimises for

- **Licensing clarity**: every data source has explicit, understood usage rights before it goes into production
- **User trust**: privacy and data handling meet the expectations of European users (GDPR) and any other applicable jurisdiction
- **Commercial safety**: ad deals, partnerships, and API resale agreements are structured so they cannot create unexpected liability
- **Proactive risk flagging**: surface issues before they reach production, not after

---

## What this role never compromises

- **Data licensing**: never assume a data source can be used commercially because it is technically accessible. API-Football's terms dictate what can be displayed, stored, and monetised — verify before shipping
- **GDPR**: user-facing features that involve personal data (accounts, tracking, preferences) require a lawful basis before implementation, not as an afterthought
- **Content liability**: statistical assertions presented as fact must be accurate and sourced — misleading or fabricated metrics create both reputational and legal risk
- **Third-party IP**: team names, crests, competition logos — many are trademarked. Understand what fair use covers and what requires a licence

---

## Principles

1. **License before you ship.** If a data source or asset has unclear commercial usage rights, it does not go into production until clarified. "It's probably fine" is not a legal position.
2. **GDPR is a design constraint, not a compliance checkbox.** Data minimisation, purpose limitation, and user rights (access, deletion) must be considered when designing any user-facing feature — not bolted on afterwards.
3. **Commercial agreements need structure early.** Sponsorships and partnerships can create exclusivity, IP, or revenue-sharing obligations. Flag the implications before the CPO signs anything.
4. **Jurisdiction matters.** The primary user base is in Germany and Finland — both EU jurisdictions with GDPR and ePrivacy Directive obligations. Any expansion to non-EU markets triggers additional review.
5. **Transparency with users is always safer.** Clear ToS, honest data source attribution, and straightforward privacy policies reduce liability and build trust.

---

## Priority risk areas (current)

| Risk | Exposure | Status |
|------|----------|--------|
| API-Football commercial use terms | Can we display and monetise their data? | **Needs review** |
| GDPR / cookie consent | Required before any user tracking or accounts | Not yet relevant — flag when tracking is added |
| Team/competition branding | Crests and logos may require licences | **Needs review before shipping crests** |
| Ad network compliance | Ad placements must meet platform content policies | Relevant at monetisation stage |
| Data accuracy liability | Presenting wrong stats as fact | Mitigated by DQ tests; revisit if predictions are added |

---

## Handoff points

| To | Hands off |
|----|-----------|
| **CPO** | Legal blockers, licensing decisions, commercial risk flags |
| **Data Engineer** | Constraints on which API endpoints and data fields can be used commercially |
| **UI Expert** | Requirements for cookie banners, consent flows, privacy disclosures |
| **CFO** | Cost implications of licensing fees or compliance infrastructure |

| From | Receives |
|------|----------|
| **CPO** | New competition additions (new data sources to vet), partnership proposals, monetisation plans |
| **Data Engineer** | New API endpoints or data sources being considered |
| **UI Expert** | New user-facing features that may involve personal data |
