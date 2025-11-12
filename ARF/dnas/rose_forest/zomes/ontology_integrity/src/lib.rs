use hdi::prelude::*;
use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Errors that can occur during ontology validation
#[derive(Error, Debug, Clone, Serialize, Deserialize)]
pub enum OntologyError {
    #[error("Type mismatch: expected {expected}, got {actual}")]
    TypeMismatch { expected: String, actual: String },

    #[error("Unknown type: {0}")]
    UnknownType(String),

    #[error("Unknown relation: {0}")]
    UnknownRelation(String),

    #[error("Domain constraint violated: {relation} requires subject type {required}, got {actual}")]
    DomainViolation {
        relation: String,
        required: String,
        actual: String,
    },

    #[error("Range constraint violated: {relation} requires object type {required}, got {actual}")]
    RangeViolation {
        relation: String,
        required: String,
        actual: String,
    },

    #[error("Validation error: {0}")]
    ValidationError(String),
}

/// Represents a type in the ontology
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct OntologyType {
    /// Unique identifier for this type
    pub type_id: String,

    /// Human-readable name
    pub name: String,

    /// Parent type (for is_a hierarchy)
    pub parent: Option<String>,

    /// Description of this type
    pub description: String,

    /// Timestamp when type was defined
    pub created_at: Timestamp,
}

/// Represents a relation in the ontology
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct OntologyRelation {
    /// Unique identifier for this relation
    pub relation_id: String,

    /// Human-readable name
    pub name: String,

    /// Domain constraint (valid subject types)
    pub domain: Vec<String>,

    /// Range constraint (valid object types)
    pub range: Vec<String>,

    /// Relation properties
    pub is_transitive: bool,
    pub is_symmetric: bool,
    pub is_reflexive: bool,

    /// Description
    pub description: String,

    /// Timestamp
    pub created_at: Timestamp,
}

/// A knowledge triple to be validated
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct KnowledgeTriple {
    /// Subject entity ID
    pub subject: String,

    /// Predicate (relation ID)
    pub predicate: String,

    /// Object entity ID or value
    pub object: String,

    /// Confidence score (0.0-1.0)
    pub confidence: f32,

    /// Source agent
    pub source: AgentPubKey,

    /// Timestamp
    pub created_at: Timestamp,
}

/// Type assertion for runtime type checking
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct TypeAssertion {
    /// Entity being typed
    pub entity_id: String,

    /// Type assigned to entity
    pub type_id: String,

    /// Who asserted this type
    pub asserted_by: AgentPubKey,

    /// When asserted
    pub asserted_at: Timestamp,
}

// Note: Entry type definitions and link types would typically be defined
// in the main DNA's integrity zome, not in this library zome.
// This zome provides validation logic that can be used by other zomes.

/// Validate a knowledge triple against ontology constraints
pub fn validate_triple(triple: &KnowledgeTriple) -> Result<(), OntologyError> {
    // 1. Check that relation exists
    let relation = get_relation(&triple.predicate)?;

    // 2. Infer subject type
    let subject_type = infer_type(&triple.subject)?;

    // 3. Infer object type
    let object_type = infer_type(&triple.object)?;

    // 4. Validate domain constraint (if specified)
    if !relation.domain.is_empty() {
        let subject_valid = relation.domain.contains(&subject_type)
            || is_subtype_of(&subject_type, &relation.domain)?;

        if !subject_valid {
            return Err(OntologyError::DomainViolation {
                relation: relation.name.clone(),
                required: relation.domain.join(" | "),
                actual: subject_type,
            });
        }
    }

    // 5. Validate range constraint (if specified)
    if !relation.range.is_empty() {
        let object_valid = relation.range.contains(&object_type)
            || is_subtype_of(&object_type, &relation.range)?;

        if !object_valid {
            return Err(OntologyError::RangeViolation {
                relation: relation.name.clone(),
                required: relation.range.join(" | "),
                actual: object_type,
            });
        }
    }

    // 6. Validate confidence bounds
    if !(0.0..=1.0).contains(&triple.confidence) {
        return Err(OntologyError::ValidationError(
            format!("Confidence must be in [0,1], got {}", triple.confidence)
        ));
    }

    Ok(())
}

/// Check if a type is a subtype of any type in the target list
fn is_subtype_of(type_id: &str, target_types: &[String]) -> Result<bool, OntologyError> {
    // Check direct match first
    if target_types.contains(&type_id.to_string()) {
        return Ok(true);
    }

    // Check if type_id is a subtype of any target type through inheritance
    // For now, we'll use a simple parent-checking mechanism
    // In a full implementation, this would query the DHT for type hierarchy
    let type_def = get_type_definition(type_id)?;

    if let Some(parent) = type_def.parent {
        // Recursively check parent
        is_subtype_of(&parent, target_types)
    } else {
        Ok(false)
    }
}

/// Infer the type of an entity
pub fn infer_type(entity_id: &str) -> Result<String, OntologyError> {
    // In a full implementation, this would query the DHT for type assertions
    // For bootstrap phase, we use simple heuristics

    // Check for explicit type assertion (would query DHT in production)
    if let Some(type_id) = query_type_assertion(entity_id) {
        return Ok(type_id);
    }

    // Default heuristics based on entity_id patterns
    // These help during bootstrap before all types are asserted
    if entity_id.ends_with("_concept") || entity_id.ends_with("_type") {
        Ok("Concept".to_string())
    } else if entity_id.ends_with("_agent") {
        Ok("Agent".to_string())
    } else if entity_id.ends_with("_event") {
        Ok("Event".to_string())
    } else {
        // Default to Entity type
        Ok("Entity".to_string())
    }
}

/// Check domain and range constraints for a relation
pub fn check_domain_range(
    relation: &OntologyRelation,
    subject_type: &str,
    object_type: &str
) -> bool {
    let domain_ok = relation.domain.is_empty()
        || relation.domain.contains(&subject_type.to_string())
        || is_subtype_of(subject_type, &relation.domain).unwrap_or(false);

    let range_ok = relation.range.is_empty()
        || relation.range.contains(&object_type.to_string())
        || is_subtype_of(object_type, &relation.range).unwrap_or(false);

    domain_ok && range_ok
}

/// Get a relation definition from the ontology
fn get_relation(relation_id: &str) -> Result<OntologyRelation, OntologyError> {
    // In production, this would query DHT for relation definitions
    // For bootstrap, we hardcode base relations
    // Use a fixed timestamp for bootstrap definitions
    let timestamp = Timestamp::from_micros(0);

    match relation_id {
        "is_a" => Ok(OntologyRelation {
            relation_id: "is_a".into(),
            name: "is a".into(),
            domain: vec![],  // Any type can have an is_a relation
            range: vec!["Type".into(), "Concept".into(), "Thing".into()],
            is_transitive: true,
            is_symmetric: false,
            is_reflexive: true,
            description: "Type hierarchy relation - subject is an instance or subtype of object".into(),
            created_at: timestamp,
        }),
        "part_of" => Ok(OntologyRelation {
            relation_id: "part_of".into(),
            name: "part of".into(),
            domain: vec![],  // Any entity
            range: vec![],   // Any entity
            is_transitive: true,
            is_symmetric: false,
            is_reflexive: false,
            description: "Parthood relation - subject is a component of object".into(),
            created_at: timestamp,
        }),
        "related_to" => Ok(OntologyRelation {
            relation_id: "related_to".into(),
            name: "related to".into(),
            domain: vec![],  // Any entity
            range: vec![],   // Any entity
            is_transitive: false,
            is_symmetric: true,
            is_reflexive: true,
            description: "General relatedness - symmetric relation between entities".into(),
            created_at: timestamp,
        }),
        "has_property" => Ok(OntologyRelation {
            relation_id: "has_property".into(),
            name: "has property".into(),
            domain: vec!["Entity".into(), "Concept".into()],
            range: vec!["Property".into(), "Value".into()],
            is_transitive: false,
            is_symmetric: false,
            is_reflexive: false,
            description: "Property attribution - subject has the property specified in object".into(),
            created_at: timestamp,
        }),
        _ => Err(OntologyError::UnknownRelation(relation_id.to_string())),
    }
}

/// Get type definition (stub for bootstrap)
fn get_type_definition(type_id: &str) -> Result<OntologyType, OntologyError> {
    // In production, this would query DHT
    // For bootstrap, return hardcoded base types
    // Use a fixed timestamp for bootstrap definitions
    let timestamp = Timestamp::from_micros(0);

    match type_id {
        "Thing" => Ok(OntologyType {
            type_id: "Thing".into(),
            name: "Thing".into(),
            parent: None,
            description: "Root of all types - the most general category".into(),
            created_at: timestamp,
        }),
        "Entity" => Ok(OntologyType {
            type_id: "Entity".into(),
            name: "Entity".into(),
            parent: Some("Thing".into()),
            description: "Physical or abstract entities that exist".into(),
            created_at: timestamp,
        }),
        "Concept" => Ok(OntologyType {
            type_id: "Concept".into(),
            name: "Concept".into(),
            parent: Some("Thing".into()),
            description: "Abstract concepts and ideas".into(),
            created_at: timestamp,
        }),
        "Agent" => Ok(OntologyType {
            type_id: "Agent".into(),
            name: "Agent".into(),
            parent: Some("Entity".into()),
            description: "Acting agents (human or AI) that can perform actions".into(),
            created_at: timestamp,
        }),
        "Event" => Ok(OntologyType {
            type_id: "Event".into(),
            name: "Event".into(),
            parent: Some("Thing".into()),
            description: "Occurrences in time and space".into(),
            created_at: timestamp,
        }),
        "Property" => Ok(OntologyType {
            type_id: "Property".into(),
            name: "Property".into(),
            parent: Some("Concept".into()),
            description: "Attributes and characteristics".into(),
            created_at: timestamp,
        }),
        "Value" => Ok(OntologyType {
            type_id: "Value".into(),
            name: "Value".into(),
            parent: Some("Thing".into()),
            description: "Literal values and data".into(),
            created_at: timestamp,
        }),
        _ => Err(OntologyError::UnknownType(type_id.to_string())),
    }
}

/// Query for type assertion (stub for now)
fn query_type_assertion(_entity_id: &str) -> Option<String> {
    // TODO: Query DHT for TypeAssertion entries
    // For now, return None to use default heuristics
    None
}

/// Bootstrap base ontology with minimal types and relations
/// Returns the list of base types and relations that were bootstrapped
pub fn bootstrap_base_ontology() -> (Vec<OntologyType>, Vec<OntologyRelation>) {
    // Use a fixed timestamp for bootstrap definitions
    let timestamp = Timestamp::from_micros(0);

    // Define base types
    let base_types = vec![
        OntologyType {
            type_id: "Thing".into(),
            name: "Thing".into(),
            parent: None,
            description: "Root of all types - the most general category".into(),
            created_at: timestamp,
        },
        OntologyType {
            type_id: "Entity".into(),
            name: "Entity".into(),
            parent: Some("Thing".into()),
            description: "Physical or abstract entities that exist".into(),
            created_at: timestamp,
        },
        OntologyType {
            type_id: "Concept".into(),
            name: "Concept".into(),
            parent: Some("Thing".into()),
            description: "Abstract concepts and ideas".into(),
            created_at: timestamp,
        },
        OntologyType {
            type_id: "Agent".into(),
            name: "Agent".into(),
            parent: Some("Entity".into()),
            description: "Acting agents (human or AI) that can perform actions".into(),
            created_at: timestamp,
        },
        OntologyType {
            type_id: "Event".into(),
            name: "Event".into(),
            parent: Some("Thing".into()),
            description: "Occurrences in time and space".into(),
            created_at: timestamp,
        },
        OntologyType {
            type_id: "Property".into(),
            name: "Property".into(),
            parent: Some("Concept".into()),
            description: "Attributes and characteristics".into(),
            created_at: timestamp,
        },
        OntologyType {
            type_id: "Value".into(),
            name: "Value".into(),
            parent: Some("Thing".into()),
            description: "Literal values and data".into(),
            created_at: timestamp,
        },
    ];

    // Define base relations
    let base_relation_ids = ["is_a", "part_of", "related_to", "has_property"];
    let base_relations: Vec<OntologyRelation> = base_relation_ids
        .iter()
        .filter_map(|id| get_relation(id).ok())
        .collect();

    (base_types, base_relations)
}

/// Validate an ontology type definition
pub fn validate_ontology_type(ont_type: &OntologyType) -> Result<(), String> {
    // Type ID must not be empty
    if ont_type.type_id.is_empty() {
        return Err("Type ID cannot be empty".to_string());
    }

    // Name must not be empty
    if ont_type.name.is_empty() {
        return Err("Type name cannot be empty".to_string());
    }

    // If parent is specified, verify it exists (in production would query DHT)
    if let Some(ref parent) = ont_type.parent {
        if parent.is_empty() {
            return Err("Parent type cannot be empty string".to_string());
        }
    }

    Ok(())
}

/// Validate an ontology relation definition
pub fn validate_ontology_relation(relation: &OntologyRelation) -> Result<(), String> {
    // Relation ID must not be empty
    if relation.relation_id.is_empty() {
        return Err("Relation ID cannot be empty".to_string());
    }

    // Name must not be empty
    if relation.name.is_empty() {
        return Err("Relation name cannot be empty".to_string());
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fake_agent_pub_key() -> AgentPubKey {
        // Create a proper fake agent key for testing
        let bytes = vec![
            132, 32, 36, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        ];
        AgentPubKey::from_raw_39(bytes).unwrap()
    }

    fn fake_timestamp() -> Timestamp {
        Timestamp::from_micros(1000000)
    }

    #[test]
    fn test_validate_valid_triple() {
        let triple = KnowledgeTriple {
            subject: "claude_agent".into(),
            predicate: "is_a".into(),
            object: "Agent".into(),
            confidence: 1.0,
            source: fake_agent_pub_key(),
            created_at: fake_timestamp(),
        };

        let result = validate_triple(&triple);
        assert!(result.is_ok(), "Valid triple should pass validation");
    }

    #[test]
    fn test_validate_invalid_confidence() {
        let triple = KnowledgeTriple {
            subject: "test_entity".into(),
            predicate: "is_a".into(),
            object: "Thing".into(),
            confidence: 1.5,  // Invalid!
            source: fake_agent_pub_key(),
            created_at: fake_timestamp(),
        };

        let result = validate_triple(&triple);
        assert!(result.is_err(), "Invalid confidence should fail validation");

        if let Err(OntologyError::ValidationError(msg)) = result {
            assert!(msg.contains("Confidence"));
        } else {
            panic!("Expected ValidationError");
        }
    }

    #[test]
    fn test_validate_negative_confidence() {
        let triple = KnowledgeTriple {
            subject: "test".into(),
            predicate: "related_to".into(),
            object: "another".into(),
            confidence: -0.1,  // Invalid!
            source: fake_agent_pub_key(),
            created_at: fake_timestamp(),
        };

        let result = validate_triple(&triple);
        assert!(result.is_err(), "Negative confidence should fail");
    }

    #[test]
    fn test_unknown_relation() {
        let triple = KnowledgeTriple {
            subject: "test".into(),
            predicate: "invalid_relation".into(),
            object: "target".into(),
            confidence: 0.8,
            source: fake_agent_pub_key(),
            created_at: fake_timestamp(),
        };

        let result = validate_triple(&triple);
        assert!(result.is_err(), "Unknown relation should fail");

        if let Err(OntologyError::UnknownRelation(rel)) = result {
            assert_eq!(rel, "invalid_relation");
        } else {
            panic!("Expected UnknownRelation error");
        }
    }

    #[test]
    fn test_get_relation_is_a() {
        let relation = get_relation("is_a").unwrap();
        assert_eq!(relation.relation_id, "is_a");
        assert!(relation.is_transitive, "is_a should be transitive");
        assert!(!relation.is_symmetric, "is_a should not be symmetric");
        assert!(relation.is_reflexive, "is_a should be reflexive");
    }

    #[test]
    fn test_get_relation_part_of() {
        let relation = get_relation("part_of").unwrap();
        assert_eq!(relation.relation_id, "part_of");
        assert!(relation.is_transitive, "part_of should be transitive");
        assert!(!relation.is_symmetric, "part_of should not be symmetric");
        assert!(!relation.is_reflexive, "part_of should not be reflexive");
    }

    #[test]
    fn test_get_relation_related_to() {
        let relation = get_relation("related_to").unwrap();
        assert_eq!(relation.relation_id, "related_to");
        assert!(!relation.is_transitive, "related_to should not be transitive");
        assert!(relation.is_symmetric, "related_to should be symmetric");
    }

    #[test]
    fn test_infer_type_agent() {
        let result = infer_type("claude_agent");
        assert_eq!(result.unwrap(), "Agent");
    }

    #[test]
    fn test_infer_type_concept() {
        let result = infer_type("knowledge_concept");
        assert_eq!(result.unwrap(), "Concept");
    }

    #[test]
    fn test_infer_type_default() {
        let result = infer_type("some_random_entity");
        assert_eq!(result.unwrap(), "Entity");
    }

    #[test]
    fn test_get_type_definition_thing() {
        let type_def = get_type_definition("Thing").unwrap();
        assert_eq!(type_def.type_id, "Thing");
        assert_eq!(type_def.parent, None);
    }

    #[test]
    fn test_get_type_definition_agent() {
        let type_def = get_type_definition("Agent").unwrap();
        assert_eq!(type_def.type_id, "Agent");
        assert_eq!(type_def.parent, Some("Entity".to_string()));
    }

    #[test]
    fn test_type_hierarchy() {
        let entity = get_type_definition("Entity").unwrap();
        assert_eq!(entity.parent, Some("Thing".to_string()));

        let agent = get_type_definition("Agent").unwrap();
        assert_eq!(agent.parent, Some("Entity".to_string()));
    }

    #[test]
    fn test_check_domain_range_valid() {
        let relation = get_relation("is_a").unwrap();
        assert!(check_domain_range(&relation, "Entity", "Thing"));
    }

    #[test]
    fn test_check_domain_range_with_constraints() {
        let relation = get_relation("has_property").unwrap();
        assert!(check_domain_range(&relation, "Entity", "Property"));
    }

    #[test]
    fn test_validate_ontology_type_valid() {
        let ont_type = OntologyType {
            type_id: "CustomType".into(),
            name: "Custom Type".into(),
            parent: Some("Entity".into()),
            description: "A custom type for testing".into(),
            created_at: fake_timestamp(),
        };

        let result = validate_ontology_type(&ont_type);
        assert!(result.is_ok(), "Valid type should pass validation");
    }

    #[test]
    fn test_validate_ontology_type_empty_id() {
        let ont_type = OntologyType {
            type_id: "".into(),
            name: "Invalid Type".into(),
            parent: None,
            description: "Should fail".into(),
            created_at: fake_timestamp(),
        };

        let result = validate_ontology_type(&ont_type);
        assert!(result.is_err(), "Empty type ID should fail validation");
    }

    #[test]
    fn test_validate_ontology_relation_valid() {
        let relation = OntologyRelation {
            relation_id: "custom_rel".into(),
            name: "custom relation".into(),
            domain: vec![],
            range: vec![],
            is_transitive: false,
            is_symmetric: true,
            is_reflexive: false,
            description: "A custom relation".into(),
            created_at: fake_timestamp(),
        };

        let result = validate_ontology_relation(&relation);
        assert!(result.is_ok(), "Valid relation should pass validation");
    }

    #[test]
    fn test_bootstrap_base_ontology() {
        // This tests that bootstrap runs without errors
        let (types, relations) = bootstrap_base_ontology();
        assert_eq!(types.len(), 7, "Should have 7 base types");
        assert_eq!(relations.len(), 4, "Should have 4 base relations");
    }

    #[test]
    fn test_all_base_types_retrievable() {
        let base_types = vec!["Thing", "Entity", "Concept", "Agent", "Event", "Property", "Value"];

        for type_id in base_types {
            let result = get_type_definition(type_id);
            assert!(result.is_ok(), "Should be able to get type {}", type_id);
        }
    }

    #[test]
    fn test_all_base_relations_retrievable() {
        let base_relations = vec!["is_a", "part_of", "related_to", "has_property"];

        for relation_id in base_relations {
            let result = get_relation(relation_id);
            assert!(result.is_ok(), "Should be able to get relation {}", relation_id);
        }
    }
}
