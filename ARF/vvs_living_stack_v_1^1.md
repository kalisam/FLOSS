# Virtual Verifiable Singularity (VVS) — **Living Stack v1.1**
**Autonomy Kernel • Auto‑Evolution • Proof‑Driven Operation**  
*Last updated: 01 Oct 2025*

> **North Star (reaffirmed)**  
> **Not run by people.** A **Virtual, Verifiable, Self‑Governing** intelligence commons on Holochain: all actions pass **machine‑checkable law**, consume **risk budgets**, emit **proofs**, and can be **forked** at any time.

---

## 0) Scope & Objectives
- Replace human approvals with **code‑enforced constraints** and **autonomy budgets**.  
- Make the stack **self‑improving** via a safe **Auto‑Evolution Loop** (propose → sandbox → verify → promote/rollback), with every step signed and reproducible.  
- Keep compute local; keep authority **cryptographic**; keep improvements **forkable**.

---

## 1) Architecture Additions (beyond v1.0)
```mermaid
flowchart TB
  subgraph DNA[Rose Forest DNA]
    IZ[Integrity Zome = Law\n(entries, links, validation)]
    CZ[Coordinator Zome = Logic\n(embed, search, edges, sharding, guards)]
    AK[Autonomy Kernel (in CZ)\n• RuleEngine • BudgetEngine • AuditTrail]
    AC[AutoConstitution Registry\n(rule specs + invariants)]
  end

  subgraph EVO[Auto‑Evolution System]
    P[Proposal Maker]\n(host‑side agent)
    S[Sandbox Grid]\n(tryorama swarms)
    G[Gatekeeper]\n(KPI & invariant checks)
  end

  subgraph Aux[Aux DNAs]
    HREA[Holo‑REA value‑flow]\n(bounties, credit)
    KPI[KPI/Telemetry DNA]\n(DP aggregates)
  end

  P-->S-->G-->DNA
  DNA<-->HREA
  DNA<-->KPI
```

**Why**: AK provides *bounded autonomy*; EVO provides *safe improvement*. Both are verifiable and forkable.

---

## 2) AutoConstitution (Rule DSL + Registry)
Rules are pure, deterministic constraints evaluated in **integrity** (hard fail) and **coordinator** (pre‑/post‑guards).

### 2.1 Rule Spec (NormLang v0 — JSON)
```json
{
  "id": "ModelCardRequired@1",
  "when": {"entry_type": "RoseNode", "visibility": "public"},
  "require": [
    {"path": "metadata.model_id", "exists": true},
    {"path": "metadata.model_card_hash", "matches": "^sha256:"}
  ],
  "on_fail": {"action": "deny", "code": "E_MODEL_CARD"}
}
```
```json
{
  "id": "BudgetedWrites@1",
  "when": {"op": "extern_call"},
  "budget": {"unit": "RU", "cost": {
    "add_knowledge": 1.0,
    "link_edge:cites": 0.5,
    "link_edge:supports": 1.5
  }},
  "limits": {"window": "24h", "max_ru": 100.0},
  "on_exhaust": {"action": "auto_halt", "signal": "BudgetLow"}
}
```

### 2.2 Registry Entries (Integrity)
- `RuleSpec { id, version, body_json, hash }` (public, signed).  
- `RuleActivation { rule_id, version, dna_version, activated_at }` (pins active set).  
- Validation: rule hashes must match; activation must be monotonic.

**Why**: Rules are content‑addressed and versioned—*law you can diff*.

---

## 3) Autonomy Kernel (AK)
### 3.1 Components
- **RuleEngine**: evaluates NormLang rules pre/post operation.  
- **BudgetEngine**: per agent/tool **Risk Units (RU)** ledger with sliding windows & adaptive throttling.  
- **AuditTrail**: append‑only local log mirrored as public summaries.

### 3.2 Guard Flow (per extern)
```
pre: RuleEngine.check(op, ctx) → may deny or require RU
     BudgetEngine.reserve(agent, ru)
exec: perform operation
post: BudgetEngine.commit(agent, ru); RuleEngine.post_check(op, result)
err:  BudgetEngine.rollback(agent, ru); emit AutoHalt if rule violated
```

### 3.3 Budget math (default)
`RU = base_cost(op) * risk_multipliers(context)`  
Context multipliers examples: new edge without citation (+1.3), large content (+1.2), low‑reputation agent (+1.5).

---

## 4) Extern API (stable v1)
```text
add_knowledge(AddNode {content, license, metadata}) -> ActionHash
vector_search(Query {text, k}) -> Vec<(ActionHash, f32)>
link_edge(AddEdge {from, to, relationship, confidence}) -> ActionHash
explain(Explain {root, depth=2}) -> EvidenceGraph
budget_status(Who {agent_or_tool}) -> BudgetState
propose_rule(RuleSpec) -> RuleHash
list_rules() -> Vec<RuleMeta>
```
**Signals**: `BudgetLow {who, remaining}`, `RuleViolation {rule_id, context}`, `IndexUpdated {delta}`.

---

## 5) Evidence Graph (canonical)
```json
{
  "nodes": [{"hash":"uhCA..","type":"RoseNode","score":0.87}],
  "edges": [{"from":"uhC..","to":"uhD..","rel":"cites","confidence":0.92}],
  "explanation": "Query→similarity→cites chain",
  "provenance": {"model_id":"text-embed-001@sha256:..","ts":"2025-10-01T12:00:00Z"}
}
```

---

## 6) Code — Key Snippets (Rust, Holochain)
### 6.1 Integrity: enforce ModelCardRequired & bounds
```rust
// in integrity zome validate()
if let Ok(node) = RoseNode::try_from(app.clone()) {
    let valid = matches!(node.license.as_str(), "MIT"|"Apache-2.0"|"BSD-3-Clause"|"MPL-2.0"|"CC-BY-4.0");
    if !valid { return invalid("E_LICENSE"); }
    let dim = node.embedding.len();
    if !(32..=4096).contains(&dim) { return invalid("E_EMBED_DIM"); }
    // ModelCardRequired
    if let (Some(mid), Some(mh)) = (node.metadata.get("model_id"), node.metadata.get("model_card_hash")) {
        if !mh.starts_with("sha256:") { return invalid("E_MODEL_CARD_HASH"); }
    } else { return invalid("E_MODEL_CARD_MISSING"); }
    return valid();
}
```

### 6.2 Coordinator: guard wrapper
```rust
pub fn guarded<T,F>(who:&AgentPubKey, op:&str, ctx:&Ctx, ru:f32, f:F) -> ExternResult<T>
where F: FnOnce()->ExternResult<T>
{
    RuleEngine::pre(op, ctx)?;                 // may deny
    BudgetEngine::reserve(who, ru)?;           // throws if exhausted
    match f() {
        Ok(out) => { BudgetEngine::commit(who, ru)?; RuleEngine::post(op, ctx, &out)?; Ok(out) },
        Err(e) => { BudgetEngine::rollback(who, ru).ok(); AutoHalt::emit(op, ctx, &e)?; Err(e) }
    }
}
```

### 6.3 Coordinator: `add_knowledge` using guard
```rust
#[hdk_extern]
pub fn add_knowledge(input: AddNode) -> ExternResult<ActionHash> {
    let who = agent_info()?.agent_latest_pubkey;
    let ru = AK::cost("add_knowledge", &input);
    guarded(&who, "add_knowledge", &Ctx::from(&input), ru, || {
        let vec = embed(&input.content);
        let node = RoseNode { content: input.content, embedding: vec, license: input.license, metadata: input.metadata };
        let hash = create_entry(&node)?;
        link_allnodes_and_shard(&hash, &node.embedding)?;
        Ok(hash)
    })
}
```

---

## 7) Auto‑Evolution Loop (EVO)
1. **Proposal**: agent/tool submits `RuleSpec`/embedder/model change with **model card** and **bench/eval** bundle.  
2. **Sandbox**: CI spins **tryorama swarms**; runs scenario suite + fuzz + property tests; computes KPIs (AAS, IR, VRR, OC72).  
3. **Gatekeeping**: promotion iff KPIs ≥ pinned baselines and invariants hold; else **auto‑rollback**.  
4. **Activation**: publish `RuleActivation`/`ModelCard` entries; pin DNA version.

### 7.1 Scenario Spec (for tryorama grid)
```json
{
  "name": "replication-basic",
  "agents": 3,
  "ops": [
    {"call":"add_knowledge","args":{"content":"causal inference","license":"MIT","metadata":{"model_id":"text-embed-001"}}},
    {"call":"vector_search","args":{"text":"causal","k":3}},
    {"call":"link_edge","args":{"from":"$0","to":"$1","relationship":"cites","confidence":0.9}}
  ],
  "assert": [{"metric":"VRR","gte":0.7},{"metric":"IR","lte":0.05}]
}
```

---

## 8) CI/CD (GitHub Actions)
```yaml
name: vvs-ci
on: [push, pull_request]
jobs:
  build-pack-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with: {targets: wasm32-unknown-unknown}
      - run: cargo build --release --target wasm32-unknown-unknown -p rose_forest_integrity -p rose_forest_coordinator
      - run: hc dna pack dnas/rose_forest -o dnas/rose_forest/rose_forest.dna
      - name: Tryorama smoke
        run: npm i -D @holochain/tryorama ts-node && npx ts-node tests/tryorama/rose_forest.test.ts
      - name: Property tests
        run: cargo test -p rose_forest_coordinator -- --nocapture
```

---

## 9) KPIs (autonomy‑centric)
- **AAS (Autonomy Assurance Score)** = verified_ops / total_ops (risk‑weighted).  
- **IR (Intervention Rate)** = auto_halts / total_ops (lower is better).  
- **RBU (Risk Budget Utilization)** = median RU/day by tool; alert on saturation.  
- **VRR**, **OC72**, **Fork Vitality** (count healthy forks).

---

## 10) Threats & Counters
- **Spec bugs** → halts: property tests + differential testing of RuleEngine.  
- **RU laundering/Sybil**: stake‑bound budgets + web‑of‑trust weighting.  
- **Hidden centralization**: require multi‑mirror model cards; offline‑first modes.  
- **Prompt rot/sycophancy**: critique‑first UX and rule `CitationRequired` for claims.

---

## 11) Do Now (practical)
- Add **ModelCardRequired** to integrity; wire **BudgetEngine** guards to `add_knowledge`/`link_edge`.  
- Stand up the **tryorama grid** with the scenario JSON above.  
- Turn on the CI workflow and pin KPI baselines.

**Ethos**: If it can’t be proved, it can’t be promoted. If it breaks the rules, it stops itself. Forks are features, not failures.

