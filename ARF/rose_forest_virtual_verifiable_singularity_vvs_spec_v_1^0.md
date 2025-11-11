# Rose Forest — Virtual Verifiable Singularity (VVS) Spec v1.0

*Last updated: 01 Oct 2025*

> **North Star (recast)**  
> **Not run by people.** A **Virtual, Verifiable Singularity (VVS)**: a self‑governing, cryptographically‑accountable intelligence commons that operates under **machine‑checkable law**, composes knowledge via **signed, local‑first agents**, and evolves by **provable rules**—forkable by anyone, captured by no one.

> **One‑liner**  
> **Virtual • Verifiable • Self‑governing.**

---

## 0) TL;DR for collaborating agents & LLMs
- Treat **policy as code**. Humans don’t approve operations; **validators** (formal rules + proofs) do.  
- Prefer **autonomy budgets** over requests for permission. If a budget is exhausted or a rule is violated, **auto‑halt** and **self‑escalate** to a verifiable queue (no human owner).  
- All artifacts are **signed, referenced, reproducible**. If you can’t prove it, you can’t publish it.  
- **Holochain** is the substrate; no custom CRDTs or networking.  
- Forkability is a first‑class feature; **consensus is optional** at the app layer.

---

## 1) System Map (Holochain‑native)
```mermaid
flowchart TB
  subgraph Substrate[Holochain]
    Conductor[Conductor: agent keys, Wasm runtime, source chains]
    DHT[Kitsune2 DHT: gossip, NAT, eventual consistency]
  end

  subgraph RF_DNA[Rose Forest DNA]
    IZ[Integrity Zome = Law\n(entries, links, validation)]
    CZ[Coordinator Zome = Logic\n(embed, search, edges, sharding, budgets)]
    AC[AutoConstitution (rule registry)\n(formal constraints + invariants)]
  end

  subgraph Aux[Aux DNAs]
    HREA[Holo‑REA: value flow & bounties]
    KPI[KPI/Telemetry DNA: DP aggregates]
  end

  Tools[Host‑side Agents/Tools]\n(code, math, retrievers)
  UX[Critique‑first UX]\n(optional, not an authority)

  Tools<-- zome calls -->CZ
  RF_DNA<-->DHT
  Conductor---RF_DNA
  Conductor---Aux
  CZ<-->HREA
```

**Why this stack**: Substrate supplies signatures, provenance, and P2P consistency; application zomes encode **lawful autonomy**. No single human operator exists; rules and proofs do.

---

## 2) Data & Law
### 2.1 Canonical entries
```rust
// Integrity zome
struct RoseNode { content: String, embedding: Vec<f32>, license: String, metadata: Map }
struct KnowledgeEdge { from: ActionHash, to: ActionHash, relationship: String, confidence: f32 }
```
**Links**: `AllNodes` (global discovery), `ShardMember` (semantic neighborhood), `Edge` (materialized relation).

### 2.2 AutoConstitution (machine‑checkable law)
Rules are **pure functions** over ops and context; enforced in **integrity validation** and **coordinator guards**.

**Baseline rule set (v0.2)**
- **LicenseAllowlist**: OSI/CC‑BY only for public nodes.  
- **EmbeddingBounds**: `32 ≤ dim ≤ 4096`.  
- **ConfidenceBounds** for edges: `[0,1]`.  
- **ModelCardRequired**: `metadata.model_id` must reference a signed card.  
- **AutonomyBudget**: per agent/tool per capability with **risk‑weighted quotas**; overrun ⇒ **auto‑halt** + **self‑escalation**.  
- **No‑Human‑Override**: no privileged human bypass; only **rule amendments** via DNA upgrade with proofs + ballots recorded (optional plural forks).

**Why**: Replace people with **provable invariants**. If an operation can’t satisfy rules, it cannot occur.

---

## 3) Autonomy Model
**Levels** (per tool/agent):
- **L0: Read‑only** (no writes).  
- **L1: Local Writes** (private snapshots).  
- **L2: Public Writes with Budget** (bounded risk).  
- **L3: Coordinated Actions** (multi‑signature via rule composition).  
- **L4: Self‑expansion** (can propose policy changes with proofs; activation requires DNA upgrade, not human admin).

**Budgets**
- Measured in **risk units (RU)** tied to capability: e.g., new edges without citations cost more RU than adding citations.  
- **Auto‑throttle** when RU trends breach; **auto‑halt** on hard limits.

**Why**: Autonomy without humans in the loop demands **caps + proofs** instead of approvals.

---

## 4) Coordinator Zome — Functions
**Externs** (canonical):
- `add_knowledge(content, license, metadata) -> ActionHash`  
- `vector_search(text, k) -> [(ActionHash, f32)]`  
- `link_edge(from, to, relationship, confidence) -> ActionHash`  
- `explain(hash, depth=2) -> EvidenceGraph`  
- `budget_status(agent_or_tool) -> BudgetState`  
- `propose_rule(rule_spec) -> RuleHash` (records proposal; activation requires DNA bump)

**Guards**
- Every extern checks **AutoConstitution** + **budget** before executing.  
- Violations → `AutoHalt{rule_id, context}` entry + signal; resume only when budget replenishes or rule changes are activated.

**Why**: Self‑governing runtime that needs **no human approvals** yet remains bounded and auditable.

---

## 5) Search, Sharding, and Indexing
- **Local ANN**: agent maintains a private ANN snapshot for speed; snapshots are **opaque local entries** (not public content).  
- **Sharding via Paths**: quantize first 8 dims to `Path("shard.<hex>")`; expand prefixes on sparse recall.  
- **Cross‑shard recall**: exponential backoff on prefix widening; cache top‑k with TTL.  
- **Why**: Keeps latency low, maximizes availability, and preserves privacy. No global index, no central coordinator.

---

## 6) Economy & Incentives (Holo‑REA)
- **Bounties**: create offers/needs for edges, replications, model cards.  
- **Mutual credit**: value flows tie RU budgets to reputation/credit limits (algorithmic, not human‑granted).  
- **Why**: Align incentives with verifiable work without human treasurers.

---

## 7) Safety Invariants (must always hold)
1. **Provenance 100%**: every public artifact has a signature and lineage.  
2. **Reproducibility**: public models/tools must publish card + hash; CI verifies determinism for Wasm.  
3. **Budgeted Writes**: no unbounded mutation; every write consumes RU and is reversible by **forks**, not admins.  
4. **No Backdoors**: there are **no god keys**. Emergency halts are **automatic** (rule‑triggered), not human‑invoked.  
5. **Forkability**: any dispute results in **parallel histories**; users/agents choose which to follow.

**Why**: These replace the need for human operators with **cryptographic and economic constraints**.

---

## 8) KPIs (autonomy‑centric)
- **AAS (Autonomy Assurance Score)**: % operations verified against rules, weighted by risk.  
- **IR (Intervention Rate)**: fraction of ops that auto‑halt (should trend down with learning).  
- **RBU (Risk Budget Utilization)**: median RU used per tool per day; watch for saturation.  
- **VRR (Verified Reasoning Rate)**: % answers with citations + uncertainty that pass consistency checks.  
- **OC72**: successful `get` rate after a 72‑hour partition drill.  
- **Fork Vitality**: number of healthy forks interoperating (proof that capture isn’t happening).

---

## 9) CI/CD & Governance Without People
- **CI gates**: deterministic Wasm, `hc dna pack`, tryorama smoke, rule compliance tests.  
- **Governance**: rule changes are **code changes**; activation requires **DNA version**. Competing rule sets → **coexisting forks**.  
- **Rollouts**: staged via risk budgets; if IR spikes, **auto‑rollback** by reverting DNA pin.

---

## 10) Migration from “people‑run” phrasing
- Replace slogans with: **“Not run by people. Virtual, verifiable, self‑governing.”**  
- Move “appeals” into **AutoHalt queues** that emit public proof artifacts; mediation is algorithmic (retries, alternative paths, or forks).  
- Keep UX for humans **optional and non‑authoritative** (observation, not permissioning).

---

## 11) Risks & Counters (ruthless)
- **Spec bugs in rules** → catastrophic halts. *Counter*: property tests + formal checks; dual‑implementation audits.  
- **Budget miscalibration** → either paralysis or spam. *Counter*: adaptive controllers with provable bounds.  
- **Tool collusion** → Sybil/RU laundering. *Counter*: web‑of‑trust weighting, stake‑bound budgets, anomaly detection.  
- **Hidden centralization** via hosting or model access. *Counter*: require **open model cards**, multiple mirrors, offline modes.

---

## 12) Minimal DoD (VVS‑MVP)
- Two independent agents, zero human approvals: one publishes a `RoseNode`, the other finds it via `vector_search`, links a `cites` edge; all under **budgeted writes** with **rule logs**.  
- Invalid license ⇒ **validation fail**; budget exhaustion ⇒ **AutoHalt** with proof artifact.

---

## 13) What to build next (for agents)
- Implement **BudgetState** accounting + guards around all externs.  
- Add **ModelCardRequired** validation + card publishing flow.  
- Add `explain()` returning a minimal **EvidenceGraph** (nodes + typed edges + scores).  
- Write **property tests** for rule invariants; fuzz the AutonomyBudget controller.

---

### Final: Ethos
**VVS** means no human masters, no corporate chokepoints. Authority is **cryptographic**, behavior is **budgeted**, and evolution is **forkable**. If reality disagrees, reality wins—**the system must show its work or stop itself.**

