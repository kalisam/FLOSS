# Symbolic-First Architecture - Part 2: Ontologies & Integration

## PART 4: BOOTSTRAP ONTOLOGIES

### Example 1: Base Ontology (Upper Ontology)

```rust
// Initial ontology setup - runs once on DNA initialization

fn bootstrap_base_ontology() -> ExternResult<()> {
    // Core types
    create_ontology_type(OntologyType {
        name: "Entity".to_string(),
        parent_types: vec![],
        required_properties: vec![],
        axioms: vec![],
    })?;
    
    create_ontology_type(OntologyType {
        name: "Concept".to_string(),
        parent_types: vec!["Entity".to_string()],
        required_properties: vec![
            PropertyConstraint {
                property: "label".to_string(),
                value_type: "String".to_string(),
                cardinality: Cardinality::AtLeastOne,
            }
        ],
        axioms: vec![],
    })?;
    
    create_ontology_type(OntologyType {
        name: "Agent".to_string(),
        parent_types: vec!["Entity".to_string()],
        required_properties: vec![],
        axioms: vec![],
    })?;
    
    // Core relations
    create_ontology_relation(OntologyRelation {
        name: "is_a".to_string(),
        domain: vec!["Entity".to_string()],
        range: vec!["Concept".to_string()],
        properties: RelationProperties {
            transitive: true,
            symmetric: false,
            asymmetric: true,
            reflexive: false,
            irreflexive: false,
            functional: false,
            inverse_functional: false,
        },
        axioms: vec![
            // Transitivity axiom: X is_a Y, Y is_a Z => X is_a Z
            LogicAxiom {
                id: "is_a_transitive".to_string(),
                premises: vec![
                    TriplePattern {
                        subject: PatternElement::Variable("?x".to_string()),
                        predicate: PatternElement::Constant("is_a".to_string()),
                        object: PatternElement::Variable("?y".to_string()),
                    },
                    TriplePattern {
                        subject: PatternElement::Variable("?y".to_string()),
                        predicate: PatternElement::Constant("is_a".to_string()),
                        object: PatternElement::Variable("?z".to_string()),
                    },
                ],
                conclusion: TriplePattern {
                    subject: PatternElement::Variable("?x".to_string()),
                    predicate: PatternElement::Constant("is_a".to_string()),
                    object: PatternElement::Variable("?z".to_string()),
                },
            },
        ],
    })?;
    
    create_ontology_relation(OntologyRelation {
        name: "part_of".to_string(),
        domain: vec!["Entity".to_string()],
        range: vec!["Entity".to_string()],
        properties: RelationProperties {
            transitive: true,
            symmetric: false,
            asymmetric: true,
            reflexive: false,
            irreflexive: false,
            functional: false,
            inverse_functional: false,
        },
        axioms: vec![
            // Transitivity: X part_of Y, Y part_of Z => X part_of Z
            LogicAxiom {
                id: "part_of_transitive".to_string(),
                premises: vec![
                    TriplePattern {
                        subject: PatternElement::Variable("?x".to_string()),
                        predicate: PatternElement::Constant("part_of".to_string()),
                        object: PatternElement::Variable("?y".to_string()),
                    },
                    TriplePattern {
                        subject: PatternElement::Variable("?y".to_string()),
                        predicate: PatternElement::Constant("part_of".to_string()),
                        object: PatternElement::Variable("?z".to_string()),
                    },
                ],
                conclusion: TriplePattern {
                    subject: PatternElement::Variable("?x".to_string()),
                    predicate: PatternElement::Constant("part_of".to_string()),
                    object: PatternElement::Variable("?z".to_string()),
                },
            },
        ],
    })?;
    
    Ok(())
}
```

### Example 2: Domain Ontology - AI/ML Knowledge

```rust
fn bootstrap_ai_ml_ontology() -> ExternResult<()> {
    // Types
    create_ontology_type(OntologyType {
        name: "AIModel".to_string(),
        parent_types: vec!["Concept".to_string()],
        required_properties: vec![
            PropertyConstraint {
                property: "architecture".to_string(),
                value_type: "String".to_string(),
                cardinality: Cardinality::ExactlyOne,
            },
            PropertyConstraint {
                property: "parameter_count".to_string(),
                value_type: "Integer".to_string(),
                cardinality: Cardinality::ExactlyOne,
            },
        ],
        axioms: vec![],
    })?;
    
    create_ontology_type(OntologyType {
        name: "LLM".to_string(),
        parent_types: vec!["AIModel".to_string()],
        required_properties: vec![
            PropertyConstraint {
                property: "context_window".to_string(),
                value_type: "Integer".to_string(),
                cardinality: Cardinality::ExactlyOne,
            },
        ],
        axioms: vec![],
    })?;
    
    create_ontology_type(OntologyType {
        name: "Dataset".to_string(),
        parent_types: vec!["Concept".to_string()],
        required_properties: vec![],
        axioms: vec![],
    })?;
    
    // Relations
    create_ontology_relation(OntologyRelation {
        name: "trained_on".to_string(),
        domain: vec!["AIModel".to_string()],
        range: vec!["Dataset".to_string()],
        properties: RelationProperties {
            transitive: false,
            symmetric: false,
            asymmetric: false,
            reflexive: false,
            irreflexive: true,
            functional: false,
            inverse_functional: false,
        },
        axioms: vec![],
    })?;
    
    create_ontology_relation(OntologyRelation {
        name: "improves_upon".to_string(),
        domain: vec!["AIModel".to_string()],
        range: vec!["AIModel".to_string()],
        properties: RelationProperties {
            transitive: true,
            symmetric: false,
            asymmetric: true,
            reflexive: false,
            irreflexive: true,
            functional: false,
            inverse_functional: false,
        },
        axioms: vec![
            // If model A improves upon B, and B improves upon C, then A improves upon C
            LogicAxiom {
                id: "improvement_transitivity".to_string(),
                premises: vec![
                    TriplePattern {
                        subject: PatternElement::Variable("?a".to_string()),
                        predicate: PatternElement::Constant("improves_upon".to_string()),
                        object: PatternElement::Variable("?b".to_string()),
                    },
                    TriplePattern {
                        subject: PatternElement::Variable("?b".to_string()),
                        predicate: PatternElement::Constant("improves_upon".to_string()),
                        object: PatternElement::Variable("?c".to_string()),
                    },
                ],
                conclusion: TriplePattern {
                    subject: PatternElement::Variable("?a".to_string()),
                    predicate: PatternElement::Constant("improves_upon".to_string()),
                    object: PatternElement::Variable("?c".to_string()),
                },
            },
        ],
    })?;
    
    create_ontology_relation(OntologyRelation {
        name: "capable_of".to_string(),
        domain: vec!["AIModel".to_string()],
        range: vec!["Task".to_string()],
        properties: RelationProperties {
            transitive: false,
            symmetric: false,
            asymmetric: false,
            reflexive: false,
            irreflexive: false,
            functional: false,
            inverse_functional: false,
        },
        axioms: vec![
            // Inheritance: if model A improves upon B, and B is capable of T, then A is capable of T
            LogicAxiom {
                id: "capability_inheritance".to_string(),
                premises: vec![
                    TriplePattern {
                        subject: PatternElement::Variable("?a".to_string()),
                        predicate: PatternElement::Constant("improves_upon".to_string()),
                        object: PatternElement::Variable("?b".to_string()),
                    },
                    TriplePattern {
                        subject: PatternElement::Variable("?b".to_string()),
                        predicate: PatternElement::Constant("capable_of".to_string()),
                        object: PatternElement::Variable("?task".to_string()),
                    },
                ],
                conclusion: TriplePattern {
                    subject: PatternElement::Variable("?a".to_string()),
                    predicate: PatternElement::Constant("capable_of".to_string()),
                    object: PatternElement::Variable("?task".to_string()),
                },
            },
        ],
    })?;
    
    Ok(())
}
```

### Example 3: Research Paper Ontology

```rust
fn bootstrap_research_ontology() -> ExternResult<()> {
    // Types
    create_ontology_type(OntologyType {
        name: "ResearchPaper".to_string(),
        parent_types: vec!["Document".to_string()],
        required_properties: vec![
            PropertyConstraint {
                property: "title".to_string(),
                value_type: "String".to_string(),
                cardinality: Cardinality::ExactlyOne,
            },
            PropertyConstraint {
                property: "doi".to_string(),
                value_type: "String".to_string(),
                cardinality: Cardinality::AtMostOne,
            },
        ],
        axioms: vec![],
    })?;
    
    // Relations
    create_ontology_relation(OntologyRelation {
        name: "cites".to_string(),
        domain: vec!["ResearchPaper".to_string()],
        range: vec!["ResearchPaper".to_string()],
        properties: RelationProperties {
            transitive: false,  // Direct citations only
            symmetric: false,
            asymmetric: true,
            reflexive: false,
            irreflexive: true,
            functional: false,
            inverse_functional: false,
        },
        axioms: vec![],
    })?;
    
    create_ontology_relation(OntologyRelation {
        name: "contradicts".to_string(),
        domain: vec!["ResearchPaper".to_string(), "Claim".to_string()],
        range: vec!["ResearchPaper".to_string(), "Claim".to_string()],
        properties: RelationProperties {
            transitive: false,
            symmetric: true,  // If A contradicts B, then B contradicts A
            asymmetric: false,
            reflexive: false,
            irreflexive: true,  // Can't contradict itself
            functional: false,
            inverse_functional: false,
        },
        axioms: vec![
            // Symmetry axiom
            LogicAxiom {
                id: "contradiction_symmetry".to_string(),
                premises: vec![
                    TriplePattern {
                        subject: PatternElement::Variable("?a".to_string()),
                        predicate: PatternElement::Constant("contradicts".to_string()),
                        object: PatternElement::Variable("?b".to_string()),
                    },
                ],
                conclusion: TriplePattern {
                    subject: PatternElement::Variable("?b".to_string()),
                    predicate: PatternElement::Constant("contradicts".to_string()),
                    object: PatternElement::Variable("?a".to_string()),
                },
            },
        ],
    })?;
    
    create_ontology_relation(OntologyRelation {
        name: "supports".to_string(),
        domain: vec!["ResearchPaper".to_string()],
        range: vec!["Claim".to_string()],
        properties: RelationProperties {
            transitive: false,
            symmetric: false,
            asymmetric: false,
            reflexive: false,
            irreflexive: false,
            functional: false,
            inverse_functional: false,
        },
        axioms: vec![
            // Conflict detection: Can't support contradictory claims
            LogicAxiom {
                id: "no_contradictory_support".to_string(),
                premises: vec![
                    TriplePattern {
                        subject: PatternElement::Variable("?paper".to_string()),
                        predicate: PatternElement::Constant("supports".to_string()),
                        object: PatternElement::Variable("?claim1".to_string()),
                    },
                    TriplePattern {
                        subject: PatternElement::Variable("?paper".to_string()),
                        predicate: PatternElement::Constant("supports".to_string()),
                        object: PatternElement::Variable("?claim2".to_string()),
                    },
                    TriplePattern {
                        subject: PatternElement::Variable("?claim1".to_string()),
                        predicate: PatternElement::Constant("contradicts".to_string()),
                        object: PatternElement::Variable("?claim2".to_string()),
                    },
                ],
                conclusion: TriplePattern {
                    subject: PatternElement::Variable("?paper".to_string()),
                    predicate: PatternElement::Constant("has_internal_contradiction".to_string()),
                    object: PatternElement::Constant("true".to_string()),
                },
            },
        ],
    })?;
    
    Ok(())
}
```

---

## PART 5: INTEGRATION WITH EXISTING SYSTEM

### Migration Path from Neural-First to Symbolic-First

#### Phase 1: Add Validation Layer (Weeks 1-2)

**Current State:**
```rust
// Existing code
#[hdk_extern]
pub fn add_vector(input: VectorInput) -> ExternResult<VectorOutput> {
    // Just stores vectors without symbolic validation
    let vector = Vector::new(input.values);
    create_entry(&VectorEntry::from(vector))?;
    // ...
}
```

**New State:**
```rust
#[hdk_extern]
pub fn add_knowledge_vector(input: KnowledgeVectorInput) -> ExternResult<ActionHash> {
    // Step 1: REQUIRE symbolic triple
    if input.triple.is_none() {
        return Err(wasm_error!("Must provide knowledge triple with vector"));
    }
    
    // Step 2: Validate triple symbolically FIRST
    let triple = input.triple.unwrap();
    validate_triple_against_ontology(&triple)?;
    
    // Step 3: Create knowledge triple (validation happens in integrity zome)
    let triple_hash = create_entry(EntryTypes::KnowledgeTriple(triple))?;
    
    // Step 4: THEN add vector as index
    let vector = Vector::new(input.embedding);
    let vector_entry = VectorEntry {
        id: uuid::Uuid::new_v4().to_string(),
        values: vector.values,
        dimensions: vector.dimensions,
        metadata: Some(HashMap::from([
            ("knowledge_triple".to_string(), triple_hash.to_string())
        ])),
        created_at: sys_time()?,
    };
    
    create_entry(EntryTypes::VectorEntry(vector_entry))?;
    
    // Link vector to triple
    create_link(triple_hash.clone(), vector_entry.id, LinkTypes::VectorIndex, ())?;
    
    Ok(triple_hash)
}
```

#### Phase 2: Ontology Bootstrap (Weeks 2-3)

1. Deploy base ontology DNA
2. Initialize core types and relations
3. Add domain-specific ontologies (AI, research, etc.)
4. Create migration tool to convert existing embeddings → triples

```rust
// Migration tool
#[hdk_extern]
pub fn migrate_existing_vectors_to_triples(batch_size: usize) -> ExternResult<MigrationReport> {
    let mut report = MigrationReport {
        total: 0,
        successful: 0,
        failed: 0,
        errors: vec![],
    };
    
    // Get all existing vectors
    let vector_hashes = get_all_vector_hashes()?;
    report.total = vector_hashes.len();
    
    for hash in vector_hashes {
        // Fetch vector
        let vector_entry = must_get_vector_entry(&hash)?;
        
        // Use LLM to extract symbolic triple from vector metadata/content
        match extract_triple_from_vector(&vector_entry) {
            Ok(candidate_triple) => {
                // Validate with committee
                match validate_with_committee(&candidate_triple, 5).await {
                    Ok(validated_triple) => {
                        // Create knowledge triple
                        match create_entry(EntryTypes::KnowledgeTriple(validated_triple)) {
                            Ok(triple_hash) => {
                                // Link to existing vector
                                create_link(triple_hash, hash, LinkTypes::VectorIndex, ())?;
                                report.successful += 1;
                            },
                            Err(e) => {
                                report.failed += 1;
                                report.errors.push(format!("Failed to create triple: {}", e));
                            }
                        }
                    },
                    Err(e) => {
                        report.failed += 1;
                        report.errors.push(format!("Validation failed: {}", e));
                    }
                }
            },
            Err(e) => {
                report.failed += 1;
                report.errors.push(format!("Extraction failed: {}", e));
            }
        }
    }
    
    Ok(report)
}
```

#### Phase 3: Query Translation (Weeks 3-4)

Wrap existing search with symbolic layer:

```rust
#[hdk_extern]
pub fn search_knowledge(query: UnifiedSearchQuery) -> ExternResult<SearchResults> {
    match query {
        // Symbolic query - PREFERRED
        UnifiedSearchQuery::Formal(formal_query) => {
            // Pure symbolic reasoning
            let bindings = execute_formal_query(&formal_query)?;
            
            // Convert to results
            Ok(SearchResults {
                results: bindings_to_results(bindings)?,
                query_type: QueryType::Symbolic,
                confidence: 1.0,  // Formal results have perfect confidence
            })
        },
        
        // Natural language - convert to formal
        UnifiedSearchQuery::NaturalLanguage(nl_query) => {
            // Try to parse into formal query
            match parse_nl_to_formal(&nl_query) {
                Ok(formal_query) => {
                    // Recursive call with formal query
                    search_knowledge(UnifiedSearchQuery::Formal(formal_query))
                },
                Err(_) => {
                    // Fall back to semantic search
                    semantic_search_with_symbolic_rerank(&nl_query)
                }
            }
        },
        
        // Vector search - for when symbolic fails
        UnifiedSearchQuery::VectorSimilarity(embedding) => {
            // Get vector results
            let similar_vectors = vector_similarity_search(&embedding, 50)?;
            
            // Fetch associated triples
            let mut results = vec![];
            for vector_hash in similar_vectors {
                if let Some(triple_hash) = get_linked_triple(&vector_hash)? {
                    if let Some(triple) = get_triple(&triple_hash)? {
                        results.push(SearchResult {
                            triple,
                            confidence: triple.confidence,  // Use symbolic confidence
                            relevance_score: 0.0,  // Would compute from vector distance
                        });
                    }
                }
            }
            
            Ok(SearchResults {
                results,
                query_type: QueryType::Semantic,
                confidence: 0.7,  // Semantic results have lower confidence
            })
        },
    }
}
```

#### Phase 4: LLM Integration as Tool (Weeks 4-6)

```rust
// LLM becomes an ASSISTANT to symbolic reasoning

#[hdk_extern]
pub fn answer_question_with_ai(question: String) -> ExternResult<AnswerWithProvenance> {
    // Step 1: Parse question into formal query (LLM assists)
    let formal_query = natural_language_to_formal_query(question)?;
    
    // Step 2: Execute formal query (SYMBOLIC - primary)
    let knowledge_bindings = query_knowledge(formal_query)?;
    
    // Step 3: Check if we have sufficient knowledge
    if knowledge_bindings.is_empty() {
        return Ok(AnswerWithProvenance {
            answer: "Insufficient knowledge in graph to answer this question.".to_string(),
            triples: vec![],
            confidence: 0.0,
            reasoning_chain: vec![],
        });
    }
    
    // Step 4: Use LLM to FORMAT answer (not generate truth)
    let answer_text = format_knowledge_as_natural_language(&knowledge_bindings)?;
    
    // Step 5: Return answer WITH FULL PROVENANCE
    Ok(AnswerWithProvenance {
        answer: answer_text,
        triples: knowledge_bindings.iter()
            .flat_map(|b| b.triples.clone())
            .collect(),
        confidence: compute_binding_confidence(&knowledge_bindings),
        reasoning_chain: extract_reasoning_chain(&knowledge_bindings)?,
    })
}

#[derive(Serialize, Deserialize)]
pub struct AnswerWithProvenance {
    /// Natural language answer (LLM formatted)
    pub answer: String,
    
    /// ALL triples used to construct answer
    pub triples: Vec<KnowledgeTriple>,
    
    /// Confidence based on symbolic reasoning
    pub confidence: f32,
    
    /// Logical reasoning chain
    pub reasoning_chain: Vec<ReasoningStep>,
}

#[derive(Serialize, Deserialize)]
pub struct ReasoningStep {
    pub rule_applied: String,
    pub premises: Vec<ActionHash>,
    pub conclusion: ActionHash,
    pub proof: String,
}
```

---

## PART 6: EXAMPLE WORKFLOWS

### Workflow 1: Human Adds Knowledge

```
1. User: "Claude Sonnet 4.5 improves upon Claude Sonnet 4"

2. System: Parse into formal triple
   - Subject: claude://model/sonnet-4.5
   - Predicate: improves_upon
   - Object: claude://model/sonnet-4

3. System: Check ontology
   - ✓ "improves_upon" exists
   - ✓ Domain: AIModel (check if claude://model/sonnet-4.5 is AIModel)
   - ✓ Range: AIModel (check if claude://model/sonnet-4 is AIModel)

4. System: Create triple with provenance
   - Derivation: HumanAsserted
   - Confidence: 1.0
   - Agent: user's public key

5. System: Validation in integrity zome
   - ✓ All type constraints satisfied
   - ✓ License is FOSS
   - ✓ No contradictions with existing knowledge

6. System: Create entry, generate embedding for search index

7. System: Trigger inference engine
   - Check for applicable axioms
   - If Sonnet-4 capable_of("reasoning"), infer Sonnet-4.5 capable_of("reasoning")
   - Create new triples via LogicalInference
```

### Workflow 2: LLM Extracts Knowledge

```
1. User uploads research paper PDF

2. System: Extract text content

3. System: Call LLM extractor
   "Extract knowledge triples from this text using the AI/ML ontology"

4. LLM returns candidates:
   [
     {subject: "GPT-4", predicate: "trained_on", object: "WebText-2024"},
     {subject: "GPT-4", predicate: "capable_of", object: "mathematical_reasoning"},
     ...
   ]

5. System: Validate EACH candidate
   - Select 5 random validator agents from DHT
   - Each validator checks:
     * Is predicate in ontology?
     * Are types correct?
     * Does this make sense semantically?
   
6. System: Require 3+ approvals
   - Candidate 1: 4/5 approve ✓ → Create with 0.8 confidence
   - Candidate 2: 2/5 approve ✗ → Reject
   - Candidate 3: 5/5 approve ✓ → Create with 1.0 confidence

7. System: Create triples with LLMExtracted provenance
   - Store validator list
   - Store prompt hash
   - Store model ID

8. System: Lower confidence than human assertions
   - These can be challenged/improved later
```

### Workflow 3: Symbolic Query & Inference

```
1. User: "What models can perform mathematical reasoning?"

2. System: Parse to formal query
   FormalQuery::TriplePattern({
     subject: Variable("?model"),
     predicate: Constant("capable_of"),
     object: Constant("mathematical_reasoning")
   })

3. System: Execute query on KG
   - Find direct matches
   - GPT-4 capable_of mathematical_reasoning
   - Claude-Opus-4 capable_of mathematical_reasoning

4. System: Apply inference
   - Check for improves_upon relations
   - GPT-4.5 improves_upon GPT-4
   - Apply capability_inheritance axiom
   - Infer: GPT-4.5 capable_of mathematical_reasoning

5. System: Return results with provenance
   [
     {
       model: "GPT-4",
       confidence: 1.0,
       source: "direct_assertion",
       triple_hash: "abc123"
     },
     {
       model: "GPT-4.5",
       confidence: 1.0,
       source: "logical_inference",
       proof: "(improves_upon GPT-4) ∧ (capable_of mathematical_reasoning GPT-4) → (capable_of mathematical_reasoning GPT-4.5)"
     }
   ]

6. User can verify:
   - Click on proof to see reasoning chain
   - Click on triple_hash to see original assertion
   - Full transparency
```

### Workflow 4: Contradiction Detection

```
1. Agent A asserts: "LLMs are conscious"

2. Agent B asserts: "LLMs are not conscious"

3. System detects potential contradiction:
   - Same subject (LLMs)
   - Same predicate (is)
   - Opposite objects (conscious vs not_conscious)

4. System queries ontology:
   - Are "conscious" and "not_conscious" marked as contradictory?
   - Yes (via logical_negation relation)

5. System creates contradiction triple:
   {
     subject: triple_1,
     predicate: "contradicts",
     object: triple_2,
     confidence: 1.0,
     derivation: LogicalInference(negation_axiom)
   }

6. System flags for community resolution:
   - Lower confidence on both triples
   - Request evidence
   - Collect votes
   - Eventually converge on consensus
```

---

## PART 7: KEY DIFFERENCES FROM CURRENT SYSTEM

### Current (Neural-First):
1. Store embedding → retrieve by similarity → hope it's relevant
2. LLM generates answer → maybe it's true, maybe not
3. No formal validation
4. Confidence scores arbitrary
5. Can't explain reasoning
6. Hallucinations go undetected

### New (Symbolic-First):
1. Store triple → validate against ontology → THEN index for search
2. Query KG formally → get provable answer → LLM formats it
3. Every claim validated
4. Confidence from logical proofs
5. Full reasoning chains
6. Contradictions detected automatically

### Migration Benefits:
1. **Backward compatible**: Existing vectors become search indices
2. **Incremental**: Can migrate data gradually
3. **Performance**: Symbolic queries often FASTER than vector search
4. **Transparency**: Every answer traceable to source
5. **Accuracy**: Ontology validation prevents garbage in
6. **Scalability**: Formal queries compose better than prompts

---

## NEXT STEPS FOR IMPLEMENTATION

1. **Read** `/mnt/skills/public/` for implementation guidance
2. **Bootstrap** base ontology (Week 1)
3. **Add** validation layer to existing zomes (Week 1-2)
4. **Test** with small dataset (Week 2)
5. **Migrate** existing vectors (Week 3)
6. **Deploy** to production gradually (Week 4+)

The key: **Every piece of knowledge that enters must pass symbolic validation**. 
Neural/LLM components become ASSISTANTS, not AUTHORITIES.
