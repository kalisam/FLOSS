# VVS — BIGGER BANG v1.2: Proof‑Carrying Autonomy & zk‑Attested Models
**Virtual • Verifiable • Self‑Governing — now with Proof‑Carrying Agents and Zero‑Knowledge Attestations**  
*Last updated: 01 Oct 2025*

> **Intent**  
> Turn the Virtual Verifiable Singularity into a **living, self‑upgrading machine**: every write is budgeted and policy‑checked, every improvement carries a **proof**, and models/tools can be verified with **zero‑knowledge**—no human gatekeepers, no god keys, only math and forks.

---

## 0) Delta from v1.1 (Living Stack)
- **Autonomy Kernel (AK)++**: add **Proof‑Carrying Code (PCC)** checks and **RU×ε** joint budget (risk units + privacy epsilon).  
- **AutoConstitution++**: rules can reference **proof requirements** and **attestation types** (e.g., `zk-proof: groth16:model-card@sha256:…`).  
- **New Zome: `attestations`**: entries for **ModelCard**, **ProofArtifact**, and **ToolClaim**; verification externs.  
- **Gatekeeper v2**: sandbox grid runs KPIs **and** proof verifiers before promotion.  

---

## 1) Proof‑Carrying Agents (PCA)
**Idea**: Any agent/tool that performs a sensitive operation must attach a **claims+proof envelope**. The system verifies before accepting the op.

### 1.1 Envelope (canonical JSON)
```json
{
  "op": "add_knowledge",
  "subject": "uhCA...",         // optional target hash or future hash preimage
  "code_hash": "sha256:...",    // tool binary/Wasm hash
  "claims": {                    // machine-checkable claims
    "model_id": "text-embed-001@sha256:...",
    "deterministic": true,
    "dp_epsilon": 0.8,
    "dataset_proof_id": "zk:groth16:Qm..."  // references ProofArtifact
  },
  "proofs": ["uhPF1...", "uhPF2..."],    // ProofArtifact ActionHashes
  "sig": "ed25519:..."                   // tool/agent signature
}
```

### 1.2 Verification Flow (coordinator)
```
RuleEngine.pre(op) → requires proof types
Attestations.verify(proofs, claims) → ok?
BudgetEngine.reserve(RU×ε)
execute(op)
BudgetEngine.commit(); RuleEngine.post(op)
```

**Why**: No humans in the loop; **evidence precedes action**.

---

## 2) Zero‑Knowledge Attested Models (ZK‑AM)
**Goal**: Verify model lineage/metrics/training constraints without revealing private data.

### 2.1 Entries (integrity zome)
```rust
#[hdk_entry_helper]
#[derive(Clone)]
pub struct ModelCard {    // public, signed
  pub name: String,       // e.g., "text-embed-001"
  pub version: String,    // semver
  pub hash: String,       // sha256 of weights/artifact
  pub license: String,
  pub dim: u16,
  pub eval: Vec<(String, f32)>,
  pub provenance: Vec<String>, // refs
}

#[hdk_entry_helper]
#[derive(Clone)]
pub struct ProofArtifact { // may be public or content‑addressed ref
  pub proof_type: String,  // e.g., "groth16",
  pub statement: String,   // canonical statement hash or JSON
  pub blob_ref: String,    // ipfs://... or inline small proof
}

#[hdk_entry_helper]
#[derive(Clone)]
pub struct ToolClaim {     // claims about a tool run
  pub code_hash: String,
  pub claims_json: String,
  pub proofs: Vec<ActionHash>,
}
```

### 2.2 Verifiers (coordinator zome)
```rust
#[hdk_extern]
pub fn verify_proof(input: VerifyInput) -> ExternResult<bool> {
  // dispatch by proof_type → call host-side verifier (ffi) or wasm circuit
  // cache result in local ANN snapshot metadata
  Ok(true)
}

#[hdk_extern]
pub fn attest_model(card: ModelCard, proofs: Vec<ActionHash>) -> ExternResult<ActionHash> {
  // validate license/dim; verify proofs match statement "weights hash == sha256:... && eval >= baseline"
  // link Path("models/<name>/<version>") → card
  create_entry(&card)
}
```

**Why**: Enables **privacy‑preserving verification** of models and training claims; no central auditor.

---

## 3) RU×ε Joint Budget
- **RU**: risk units (operation risk).  
- **ε**: differential privacy budget (privacy cost).  
- **Joint cost**: `J = α·RU + β·ε` with per‑agent/tool windows and maxes.

**NormLang fragments**
```json
{
  "id": "JointBudget@1",
  "when": {"op": "extern_call"},
  "budget": {"unit": "J", "alpha": 1.0, "beta": 2.0, "cost": {"add_knowledge": 1.0}},
  "limits": {"window": "24h", "max": 150.0},
  "on_exhaust": {"action": "auto_halt", "signal": "BudgetLow"}
}
```

**Why**: Marries safety (RU) with privacy (ε) so the system can be autonomous **and** privacy‑respecting.

---

## 4) Fork Orchestration & Re‑merge
- **Canary Forks**: proposed rule/model changes activate as parallel DNA versions with **bounded exposure** via budgets.
- **Re‑merge**: if KPIs improve and invariants hold, tag fork as **mainline**; otherwise it dies out.  
- **Evidence‑weighted rebase**: prefer histories with stronger proofs and better KPIs.

**Why**: Evolution without committees; **selection by evidence**.

---

## 5) Formal Invariants
- **I1: No God Keys** — no extern can bypass validation/budget.  
- **I2: Budgeted Writes** — all public writes consume J; J windows are monotonic.  
- **I3: Reproducibility** — public models must have a ModelCard with deterministic build attestation.  
- **I4: Verifiable Promotion** — promotions only when KPI deltas ≥ thresholds and verifiers pass.  

*Sketch (PlusCal/TLA+ outline omitted for brevity in this doc; see `formal/` in repo).*  

---

## 6) API Additions (stable v1.2)
```text
attest_model(ModelCard, proofs[]) -> ActionHash
submit_tool_claim(ToolClaim) -> ActionHash
verify_proof(VerifyInput{proof_hash|ref}) -> bool
budget_quote(Op, Context) -> J
explain(root, depth) -> EvidenceGraph
```

**Signals**: `ProofInvalid {proof, reason}`, `PromotionPassed {artifact}`, `ForkStarted {dna}`.

---

## 7) Holochain Wiring
- **New integrity entries**: `ModelCard`, `ProofArtifact`, `ToolClaim`.  
- **Paths**: `models/<name>/<version>`, `proofs/<type>/<hash>`.  
- **Coordinator guards**: extends `guarded()` to require/verifiy proofs if rules demand them.  
- **Host‑side verifiers**: circuits run outside Wasm; results recorded as `ProofArtifact` with verifier code hash.

---

## 8) Tryorama Scenarios (Gatekeeper v2)
- **zk‑attested model**: publish `ModelCard` + zk proof; add knowledge that cites it; verify search recall.  
- **budget stress**: run near J limit; expect `BudgetLow` signals but no rule violation.  
- **fork canary**: activate alt embedder; compare VRR/IR; promote only if ≥ baseline.

---

## 9) Immediate Commits (90‑minute path)
1. **Integrity**: add entries (`ModelCard`, `ProofArtifact`, `ToolClaim`) + validation stubs.  
2. **Coordinator**: extend `guarded()` to accept a `claims+proofs` envelope; add `attest_model` + `verify_proof` stubs.  
3. **CI**: add tryorama scenarios for zk‑attest publish → vector_search; budget stress.

---

## 10) Ethos (unchanged)
If it can’t be **proved**, it can’t be **promoted**. If it breaks the **rules**, it **stops itself**. If there’s contention, **forks compete** and evidence decides.

