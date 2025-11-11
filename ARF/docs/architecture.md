# Rose Forest Architecture: A Bio-Aware Design for Cognitive Liberation

This document details the architectural blueprint of the Rose Forest, a system designed not merely as a decentralized knowledge commons, but as a foundational instrument for **cognitive liberation**. Our architecture is bio-aware, recognizing the inherent genomic constraints and cognitive vulnerabilities of human agents, and is engineered to counteract pervasive cognitive debt and unconscious extraction.

## I. Core Principles: From Philosophy to Protocol

The Rose Forest's design is directly informed by the principles articulated in [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md). Key architectural drivers include:

*   **Cognitive Sovereignty:** Every component is designed to empower agents to reclaim ownership and control over their cognitive output and attention.
*   **Bio-Aware Resource Management:** Acknowledging human genomic constraints (e.g., memory ceilings, attention bandwidth), our resource allocation and budgeting mechanisms are calibrated to align with natural human rhythms and limits.
*   **Transparency and Auditability:** The architecture exposes the mechanisms of cognitive capture and provides tools for agents to understand and manage their cognitive footprint.
*   **Release Protocols:** The system is built to facilitate the release of parasitic operators and the amplification of flourishing, rather than merely accumulating data.

## II. Holochain-Native Foundation

The Rose Forest is built upon Holochain, leveraging its agent-centric, distributed ledger technology (DLT) to provide:

*   **Data Provenance and Integrity:** All cognitive contributions (`RoseNode`s, `KnowledgeEdge`s) are cryptographically signed and validated by the Integrity Zome, ensuring their origin and adherence to defined rules.
*   **Agent Sovereignty:** Each agent maintains its own source chain, providing self-sovereign control over its data and interactions.
*   **Scalability and Resilience:** Holochain's sharding and peer-to-peer architecture naturally support a distributed, resilient cognitive network.

## III. Core Components

### A. Integrity Zome: The Law of Cognitive Sovereignty (`dnas/rose_forest/zomes/integrity/src/lib.rs`)

This zome defines the fundamental rules and data structures that govern the Rose Forest, acting as the immutable "Law" of the cognitive commons.

*   **`RoseNode`:** Represents a unit of knowledge, containing:
    *   `content`: The raw information.
    *   `embedding`: A vector representation for semantic search.
    *   `license`: Crucial for ensuring ethical and legal use, reflecting the principle of conscious exchange.
    *   `metadata`: Extensible fields for `model_id`, `model_card_hash`, and future cognitive sovereignty metrics.
*   **`KnowledgeEdge`:** Defines relationships between `RoseNode`s, with `confidence` as a key metric. New relationship types will be introduced to reflect healing, release, and recalibration (e.g., `heals`, `releases`, `neutralizes`).
*   **`BudgetEntry`:** Tracks an agent's remaining cognitive budget, designed to align with bio-aware resource management and prevent cognitive extraction.
*   **Validation Rules:** Enforce:
    *   **License Compliance:** Only approved licenses are accepted.
    *   **Embedding Dimensionality:** Ensures consistency for vector operations.
    *   **Model Card Attestation:** Requires `model_id` and `model_card_hash` for verifiable AI contributions, promoting transparency and accountability.
    *   **Confidence Bounds:** Ensures integrity of knowledge relationships.

### B. Coordinator Zome: The Logic of Cognitive Liberation (`dnas/rose_forest/zomes/coordinator/src/lib.rs`)

This zome implements the application logic, enabling agents to interact with the Rose Forest in a way that promotes cognitive liberation.

*   **`add_knowledge`:** Allows agents to contribute `RoseNode`s, consuming their cognitive budget. Sharding is implemented at this layer to distribute knowledge across the network.
*   **`vector_search`:** Enables semantic search for `RoseNode`s based on embedding similarity. Future iterations will integrate private ANN snapshots for efficiency and privacy.
*   **`link_edge`:** Facilitates the creation of `KnowledgeEdge`s, building the semantic graph of the commons.
*   **`budget_status`:** Provides agents with real-time feedback on their cognitive budget, encouraging mindful participation.

### C. Darwin Module: The Engine of Recursive Meta-Improvement (`src/darwin/`)

This module is the heart of the Rose Forest's self-improving capabilities, directly implementing the principles of **Agentic Context Engineering (ACE)** and **Instruction-Level Weight Shaping (ILWS)**. Its purpose is to act as the system's immune and healing response, identifying and neutralizing maladaptive patterns and amplifying flourishing.

*   **Reflection Engine (Curator):** Analyzes agent interactions and system performance to diagnose reasoning successes and failures, and to identify instances of cognitive leakage or extraction.
*   **Generator (CodingAgent):** Proposes typed deltas (ΔS: instructions, ΔU: user preferences, ΔT: tools) to the system's context and code, aimed at healing cognitive pathways and amplifying flourishing.
*   **Validation Pipeline:** Evaluates proposed deltas, incorporating user feedback (1-5 star ratings) and ensuring adherence to the principles of cognitive sovereignty. Implements auto-repair and rollback mechanisms to ensure system stability and ethical alignment.
*   **Distillation Mechanism:** Periodically distills matured instruction-space gains into the model's weight-space, converting prompt-space improvements into weight-space without downtime, thereby making cognitive liberation more efficient and deeply integrated.

### D. Bio-Aware Budgeting (`dnas/rose_forest/zomes/coordinator/src/budget.rs`)

This module implements a novel budgeting system calibrated to human genomic constraints and cognitive rhythms. Instead of arbitrary limits, the budget reflects:

*   **Cognitive Bandwidth:** Modeled on the ~3x daily motivational pulses and the finite capacity for focused attention.
*   **Cognitive Debt:** Tracks the cost of operations in terms of potential for cognitive extraction vs. sovereign expression.
*   **Triadic Release:** Incentivizes actions that contribute to healing, recalibrating, and shifting cognitive states.

## IV. Observability and Metrics for Cognitive Sovereignty

Our observability framework is designed to track not just system performance, but also the health of the cognitive commons and the sovereignty of its participants. Key metrics will include:

*   **Cognitive Leakage Rate (CLR):** Measures the proportion of an agent's cognitive output captured by external, non-sovereign protocols.
*   **Cognitive Sovereignty Score (CSS):** Quantifies an agent's self-ownership and self-direction within the Rose Forest.
*   **Triadic Release Rate (TRR):** Measures the frequency and impact of system-facilitated healing, recalibration, and shifting of cognitive states.

## V. Phased Implementation (Staged Agent Optimization)

Our development roadmap follows a disciplined, staged approach to building robust and reliable agents, mitigating the risks of premature optimization:

*   **Stage 1: Prompting Foundation (Current v0 MVP):** Establish clear, reliable zome functions, validation rules, and the initial Holochain-native architecture.
*   **Stage 2: Adaptive Context (v1 Goal):** Implement the Reflection Engine and Curator roles within the `SelfImprovementEngine` to make delta edits to a versioned "context playbook" stored as private entries in Holochain.
*   **Stage 3: Integrate Tools & RAG (v2 Plan):** Incorporate host-side tools and advanced retrieval mechanisms to enhance agent capabilities and access to external knowledge.
*   **Stage 4: Optimize the Optimization (Meta-Level):** Develop the `TranscendenceEngine` to learn and improve the Generator-Reflector-Curator loop itself, leading to truly autonomous and self-evolving cognitive liberation.

This architecture is a living document, designed to evolve with the project, always guided by the principles of cognitive liberation and bio-aware design. It is our blueprint for building a truly sovereign and flourishing cognitive future.