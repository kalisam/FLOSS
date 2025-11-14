use hdk::prelude::*;
use serde::{Deserialize, Serialize};
use ontology_integrity::{KnowledgeTriple, validate_triple};
use sha2::{Sha256, Digest};
use rose_forest_integrity::BudgetEntry;

mod budget;
use budget::{consume_budget, get_budget_state, BudgetState};
use budget::{COST_TRANSMIT_UNDERSTANDING, COST_RECALL_UNDERSTANDINGS, COST_COMPOSE_MEMORIES, COST_VALIDATE_TRIPLE};

/// Entry types for the memory coordinator zome
#[hdk_entry_defs]
#[unit_enum(UnitEntryTypes)]
pub enum EntryTypes {
    Understanding(Understanding),
    ADR(ADR),
    MemoryComposition(MemoryComposition),
    KnowledgeTriple(KnowledgeTriple),
    BudgetEntry(BudgetEntry),
}

/// Link types for memory queries
#[hdk_link_types]
pub enum LinkTypes {
    AgentToUnderstanding,
    TripleToUnderstanding,
    ADRToUnderstanding,
    AgentBudget,
}

/// An understanding transmitted by an agent
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct Understanding {
    /// Content of the understanding
    pub content: String,

    /// Optional context
    pub context: Option<String>,

    /// Extracted knowledge triple
    pub triple: KnowledgeTriple,

    /// When this was created
    pub created_at: Timestamp,

    /// Agent who transmitted this
    pub agent: AgentPubKey,

    /// Content hash for deduplication
    pub content_hash: String,
}

/// Architecture Decision Record
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct ADR {
    /// ADR identifier
    pub id: String,

    /// Title/summary
    pub title: String,

    /// Full content
    pub content: String,

    /// Status (proposed, accepted, rejected, superseded)
    pub status: String,

    /// When decided
    pub decided_at: Timestamp,

    /// Who decided
    pub decided_by: AgentPubKey,
}

/// Result of memory composition
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct MemoryComposition {
    /// Agents involved in composition
    pub agents: Vec<AgentPubKey>,

    /// Composition strategy used
    pub strategy: String,

    /// Statistics from composition
    pub stats: CompositionStats,

    /// When composed
    pub composed_at: Timestamp,
}

#[derive(Serialize, Deserialize, Clone, PartialEq, Debug, SerializedBytes)]
pub struct CompositionStats {
    pub total_understandings: u32,
    pub new_understandings: u32,
    pub duplicate_skipped: u32,
}

/// Input for transmitting an understanding
#[derive(Serialize, Deserialize, Debug)]
pub struct UnderstandingInput {
    pub content: String,
    pub context: Option<String>,
}

/// Query for recalling understandings
#[derive(Serialize, Deserialize, Debug)]
pub struct RecallQuery {
    pub agent: Option<AgentPubKey>,
    pub content_contains: Option<String>,
    pub after_timestamp: Option<Timestamp>,
    pub limit: Option<usize>,
}

/// Statistics about validation
#[derive(Serialize, Deserialize, Debug)]
pub struct ValidationStats {
    pub total_understandings: usize,
    pub valid_triples: usize,
    pub invalid_triples: usize,
}

/// Transmit an understanding to the DHT
///
/// This function:
/// 1. Extracts a knowledge triple from the content
/// 2. Validates the triple against the ontology
/// 3. Creates an Understanding entry
/// 4. Creates links for efficient queries
/// 5. Returns the hash of the Understanding entry
#[hdk_extern]
pub fn transmit_understanding(input: UnderstandingInput) -> ExternResult<ActionHash> {
    // Get agent info early for budget check
    let agent_info = agent_info()?;
    let agent_key = agent_info.agent_latest_pubkey;

    // Check and consume budget (transmit + validate costs)
    let total_cost = COST_TRANSMIT_UNDERSTANDING + COST_VALIDATE_TRIPLE;
    consume_budget(&agent_key, total_cost)?;

    // Extract triple from content
    let triple = extract_triple(&input.content)?;

    // Validate triple against ontology
    validate_triple(&triple)
        .map_err(|e| wasm_error!(WasmErrorInner::Guest(format!("Ontology validation failed: {:?}", e))))?;

    // Create Understanding entry
    let understanding = Understanding {
        content: input.content.clone(),
        context: input.context,
        triple: triple.clone(),
        created_at: sys_time()?,
        agent: agent_key.clone(),
        content_hash: hash_content(&input.content),
    };

    // Commit Understanding to DHT
    let understanding_hash = create_entry(EntryTypes::Understanding(understanding.clone()))?;

    // Create link from agent to understanding (for recall by agent)
    create_link(
        agent_key.clone(),
        understanding_hash.clone(),
        LinkTypes::AgentToUnderstanding,
        ()
    )?;

    // Create the triple entry
    let triple_hash = create_entry(EntryTypes::KnowledgeTriple(triple.clone()))?;

    // Link triple to understanding (for semantic queries)
    create_link(
        triple_hash,
        understanding_hash.clone(),
        LinkTypes::TripleToUnderstanding,
        ()
    )?;

    debug!("Transmitted understanding with triple: subject={}, predicate={}, object={}",
           triple.subject, triple.predicate, triple.object);

    Ok(understanding_hash)
}

/// Recall understandings from the DHT based on query criteria
///
/// This function:
/// 1. Queries the DHT for links from agent to understandings
/// 2. Applies filters (content search, timestamp, etc.)
/// 3. Returns matching understandings
/// 4. Charges budget based on number of results returned
#[hdk_extern]
pub fn recall_understandings(query: RecallQuery) -> ExternResult<Vec<Understanding>> {
    // Get agent info for budget check
    let current_agent = agent_info()?.agent_latest_pubkey;

    let mut results = vec![];

    // Query by agent
    if let Some(agent) = query.agent {
        let links = get_links(
            GetLinksInputBuilder::try_new(agent, LinkTypes::AgentToUnderstanding)?
                .build()
        )?;

        for link in links {
            if let Some(understanding) = get_understanding(link.target.into())? {
                // Apply filters
                if matches_query(&understanding, &query) {
                    results.push(understanding);
                }
            }
        }
    } else {
        // If no agent specified, search the current agent's understandings
        let agent_info = agent_info()?;
        let links = get_links(
            GetLinksInputBuilder::try_new(agent_info.agent_latest_pubkey, LinkTypes::AgentToUnderstanding)?
                .build()
        )?;

        for link in links {
            if let Some(understanding) = get_understanding(link.target.into())? {
                if matches_query(&understanding, &query) {
                    results.push(understanding);
                }
            }
        }
    }

    // Limit results
    if let Some(limit) = query.limit {
        results.truncate(limit);
    }

    // Charge budget based on number of results (0.1 RU per result)
    let recall_cost = COST_RECALL_UNDERSTANDINGS * results.len() as f32;
    consume_budget(&current_agent, recall_cost)?;

    Ok(results)
}

/// Compose memories from another agent
///
/// This function:
/// 1. Gets all understandings from the other agent
/// 2. Merges them with the current agent's understandings
/// 3. Deduplicates based on content hash
/// 4. Creates a MemoryComposition entry to track the composition
/// 5. Charges budget for the composition operation
#[hdk_extern]
pub fn compose_memories(other_agent: AgentPubKey) -> ExternResult<MemoryComposition> {
    let agent_info = agent_info()?;
    let my_agent = agent_info.agent_latest_pubkey;

    // Check and consume budget for composition
    consume_budget(&my_agent, COST_COMPOSE_MEMORIES)?;

    // Get my understandings
    let my_understandings = recall_understandings(RecallQuery {
        agent: Some(my_agent.clone()),
        content_contains: None,
        after_timestamp: None,
        limit: None,
    })?;

    // Get other agent's understandings
    let other_understandings = recall_understandings(RecallQuery {
        agent: Some(other_agent.clone()),
        content_contains: None,
        after_timestamp: None,
        limit: None,
    })?;

    // Build set of my content hashes for quick lookup
    let my_hashes: std::collections::HashSet<String> = my_understandings
        .iter()
        .map(|u| u.content_hash.clone())
        .collect();

    // Merge (simple: add non-duplicates)
    let mut new_count = 0;
    let mut dup_count = 0;

    for understanding in other_understandings.iter() {
        // Check if duplicate
        if my_hashes.contains(&understanding.content_hash) {
            dup_count += 1;
        } else {
            // Import understanding (create entry for current agent)
            let new_understanding = Understanding {
                content: understanding.content.clone(),
                context: understanding.context.clone(),
                triple: understanding.triple.clone(),
                created_at: sys_time()?,
                agent: my_agent.clone(),
                content_hash: understanding.content_hash.clone(),
            };

            let hash = create_entry(EntryTypes::Understanding(new_understanding))?;

            // Create link from current agent to understanding
            create_link(
                my_agent.clone(),
                hash,
                LinkTypes::AgentToUnderstanding,
                ()
            )?;

            new_count += 1;
        }
    }

    // Create composition entry
    let composition = MemoryComposition {
        agents: vec![my_agent.clone(), other_agent],
        strategy: "merge".to_string(),
        stats: CompositionStats {
            total_understandings: (my_understandings.len() + new_count) as u32,
            new_understandings: new_count as u32,
            duplicate_skipped: dup_count as u32,
        },
        composed_at: sys_time()?,
    };

    create_entry(EntryTypes::MemoryComposition(composition.clone()))?;

    debug!("Composed memories: {} new, {} duplicates skipped", new_count, dup_count);

    Ok(composition)
}

/// Get current budget status for the calling agent
#[hdk_extern]
pub fn budget_status(_: ()) -> ExternResult<BudgetState> {
    let agent_key = agent_info()?.agent_latest_pubkey;
    get_budget_state(&agent_key)
}

/// Get validation statistics for all understandings
#[hdk_extern]
pub fn get_validation_stats(_: ()) -> ExternResult<ValidationStats> {
    let agent_info = agent_info()?;

    // Get all understandings for current agent
    let understandings = recall_understandings(RecallQuery {
        agent: Some(agent_info.agent_latest_pubkey),
        content_contains: None,
        after_timestamp: None,
        limit: None,
    })?;

    let total = understandings.len();
    let valid = understandings.len(); // All stored understandings passed validation

    Ok(ValidationStats {
        total_understandings: total,
        valid_triples: valid,
        invalid_triples: 0,
    })
}

/// Create an ADR (Architecture Decision Record)
#[hdk_extern]
pub fn create_adr(adr: ADR) -> ExternResult<ActionHash> {
    let hash = create_entry(EntryTypes::ADR(adr))?;
    Ok(hash)
}

/// Get an ADR by hash
#[hdk_extern]
pub fn get_adr(hash: ActionHash) -> ExternResult<Option<ADR>> {
    let record = get(hash, GetOptions::default())?;
    match record {
        Some(rec) => {
            let adr: Option<ADR> = rec.entry().to_app_option()?;
            Ok(adr)
        }
        None => Ok(None),
    }
}

// ===== Helper Functions =====

/// Get an understanding by hash
fn get_understanding(hash: ActionHash) -> ExternResult<Option<Understanding>> {
    let record = get(hash, GetOptions::default())?;
    match record {
        Some(rec) => {
            let understanding: Option<Understanding> = rec.entry().to_app_option()?;
            Ok(understanding)
        }
        None => Ok(None),
    }
}

/// Check if an understanding matches the query criteria
fn matches_query(understanding: &Understanding, query: &RecallQuery) -> bool {
    // Filter by content
    if let Some(ref contains) = query.content_contains {
        if !understanding.content.to_lowercase().contains(&contains.to_lowercase()) {
            return false;
        }
    }

    // Filter by timestamp
    if let Some(after) = query.after_timestamp {
        if understanding.created_at < after {
            return false;
        }
    }

    true
}

/// Extract a knowledge triple from content using pattern matching
///
/// This is a simplified version that uses regex patterns.
/// In production, this could use LLM-based extraction.
fn extract_triple(content: &str) -> ExternResult<KnowledgeTriple> {
    let agent_info = agent_info()?;
    let agent_key = agent_info.agent_latest_pubkey;

    // Pattern 1: "X is a Y" or "X is an Y"
    if let Some((subject, object)) = extract_is_a_pattern(content) {
        return Ok(KnowledgeTriple {
            subject,
            predicate: "is_a".to_string(),
            object,
            confidence: 1.0,
            source: agent_key,
            created_at: sys_time()?,
        });
    }

    // Pattern 2: "X improves Y" or "X improves upon Y"
    if let Some((subject, object)) = extract_improves_pattern(content) {
        return Ok(KnowledgeTriple {
            subject,
            predicate: "improves_upon".to_string(),
            object,
            confidence: 0.9,
            source: agent_key,
            created_at: sys_time()?,
        });
    }

    // Pattern 3: "X can do Y" / "X is capable of Y"
    if let Some((subject, object)) = extract_capable_pattern(content) {
        return Ok(KnowledgeTriple {
            subject,
            predicate: "capable_of".to_string(),
            object,
            confidence: 0.8,
            source: agent_key,
            created_at: sys_time()?,
        });
    }

    // Default: treat as statement
    // Subject = agent, predicate = stated, object = content hash
    Ok(KnowledgeTriple {
        subject: format!("agent_{}", &agent_key.to_string()[..8]),
        predicate: "stated".to_string(),
        object: format!("content_{}", hash_content(content)),
        confidence: 1.0,
        source: agent_key,
        created_at: sys_time()?,
    })
}

/// Extract "X is a Y" pattern
fn extract_is_a_pattern(content: &str) -> Option<(String, String)> {
    // Simple pattern matching for "X is a/an Y"
    let words: Vec<&str> = content.split_whitespace().collect();

    for i in 0..words.len().saturating_sub(3) {
        if words[i + 1] == "is" && (words[i + 2] == "a" || words[i + 2] == "an") {
            let subject = words[i].trim_matches(|c: char| !c.is_alphanumeric() && c != '-');
            let object = words[i + 3].trim_matches(|c: char| !c.is_alphanumeric() && c != '-');

            if !subject.is_empty() && !object.is_empty() {
                return Some((subject.to_string(), object.to_string()));
            }
        }
    }

    None
}

/// Extract "X improves Y" pattern
fn extract_improves_pattern(content: &str) -> Option<(String, String)> {
    let words: Vec<&str> = content.split_whitespace().collect();

    for i in 0..words.len().saturating_sub(2) {
        if words[i + 1] == "improves" {
            let subject = words[i].trim_matches(|c: char| !c.is_alphanumeric() && c != '-');

            // Check if next word is "upon"
            let obj_idx = if i + 2 < words.len() && words[i + 2] == "upon" {
                i + 3
            } else {
                i + 2
            };

            if obj_idx < words.len() {
                let object = words[obj_idx].trim_matches(|c: char| !c.is_alphanumeric() && c != '-');
                if !subject.is_empty() && !object.is_empty() {
                    return Some((subject.to_string(), object.to_string()));
                }
            }
        }
    }

    None
}

/// Extract "X capable of Y" pattern
fn extract_capable_pattern(content: &str) -> Option<(String, String)> {
    let words: Vec<&str> = content.split_whitespace().collect();

    for i in 0..words.len().saturating_sub(3) {
        if words[i + 1] == "is" && words[i + 2] == "capable" && i + 3 < words.len() && words[i + 3] == "of" {
            let subject = words[i].trim_matches(|c: char| !c.is_alphanumeric() && c != '-');

            if i + 4 < words.len() {
                let object = words[i + 4].trim_matches(|c: char| !c.is_alphanumeric() && c != '-');
                if !subject.is_empty() && !object.is_empty() {
                    return Some((subject.to_string(), object.to_string()));
                }
            }
        }
    }

    None
}

/// Hash content using SHA-256
fn hash_content(content: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(content.as_bytes());
    format!("{:x}", hasher.finalize())[..16].to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extract_is_a_pattern() {
        let result = extract_is_a_pattern("GPT-4 is a LLM");
        assert!(result.is_some());
        let (subject, object) = result.unwrap();
        assert_eq!(subject, "GPT-4");
        assert_eq!(object, "LLM");
    }

    #[test]
    fn test_extract_improves_pattern() {
        let result = extract_improves_pattern("Claude-4.5 improves Claude-4");
        assert!(result.is_some());
        let (subject, object) = result.unwrap();
        assert_eq!(subject, "Claude-4.5");
        assert_eq!(object, "Claude-4");
    }

    #[test]
    fn test_hash_content() {
        let hash1 = hash_content("test content");
        let hash2 = hash_content("test content");
        let hash3 = hash_content("different content");

        assert_eq!(hash1, hash2);
        assert_ne!(hash1, hash3);
        assert_eq!(hash1.len(), 16);
    }
}
