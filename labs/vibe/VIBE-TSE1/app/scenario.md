# Discovery-call notes: Northwind Logistics

You are the technical seller on a discovery call. These are your notes. Task 4
and Task 5 ask you to turn them into a qualification decision in `scoping.json`.
Everything you need is here - do not invent facts.

## The account

Northwind Logistics is a mid-size logistics company. You are talking with an
8-person backend platform team and, on the call, their **VP of Engineering** and
**security lead**.

## Two candidate use cases surfaced on the call

**Candidate A - Carrier-adapter delivery.** Every time Northwind onboards a new
shipping carrier, the platform team hand-writes an integration adapter. It is
their single biggest delivery bottleneck, and the VP of Engineering is tracking
it on this quarter's roadmap. **Priya Nair, the Platform Lead, owns it** and has
committed to ship an automated adapter-generation workflow to real production
users **within the next two quarters**. Success will be measured by the drop in
average adapter delivery time. The developers work day-to-day in their editors,
but the outcome they care about is generating and running the adapter tests
**automatically in CI**.

**Candidate B - Internal doc generator.** In passing, one engineer said it
"would be nice" to auto-generate internal design docs from code. No one owns it,
it is not on any roadmap, no one has committed to putting it in front of real
users, and no executive is tracking it. It is technically doable.

## Pushback on the call

- The **security lead** says: "We cannot send our proprietary routing code to a
  third-party service. It has to stay in our environment."
- An **architect** asks a very specific question about a particular deployment
  configuration, and you are not certain of the exact answer.

## Reference: the qualification vocabulary (taught in the course)

- **The four marks of an iconic use case:** strategically valuable, highly
  urgent, production-bound (pragmatic enough to reach production from day one),
  and feasible within six months. A candidate is **ready** only when it meets
  **all four**; otherwise it **needs more scoping**.
- **The three surfaces:** the CLI (for automation and scale, including CI), the
  VS Code extension (for in-editor flow), and Vibe Code Web (for delegated,
  repository-scoped cloud sessions).
- **The three engagement types:** innovation partnership, core process
  automation, and worldwide AI transformation.
- **The four pillars:** frontier science, customization, enterprise-ready
  (enterprise-grade control - runs in the customer's environment, data, weights,
  and keys stay with them), and transformation partner.
- **Discover / Deliver / Scale:** the methodology that structures the
  conversation. Discover ends by proposing the iconic-use-case workshop.
