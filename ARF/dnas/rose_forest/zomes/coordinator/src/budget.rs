use hdk::prelude::*;
use rose_forest_integrity::BudgetEntry;

// Bio-aware budget parameters based on the manifesto
// Represents a unit of cognitive output, calibrated to the idea of ~3 major cognitive pulses per day
pub const COST_ADD_KNOWLEDGE: f32 = 33.0;
// Represents a unit of cognitive linking, a less intensive action
pub const COST_LINK_EDGE: f32 = 3.0;
// Represents the cost of creating a significant thoughtform
pub const COST_CREATE_THOUGHT_CREDENTIAL: f32 = 10.0;

// Memory operation costs (VVS spec requirements)
// Cost to transmit an understanding to the DHT
pub const COST_TRANSMIT_UNDERSTANDING: f32 = 1.0;
// Cost per result when recalling understandings
pub const COST_RECALL_UNDERSTANDINGS: f32 = 0.1;
// Cost to compose memories from another agent
pub const COST_COMPOSE_MEMORIES: f32 = 5.0;
// Cost to validate a knowledge triple
pub const COST_VALIDATE_TRIPLE: f32 = 2.0;

// Total cognitive budget per window, reflecting the idea of a daily cognitive capacity
pub const MAX_RU_PER_WINDOW: f32 = 100.0;
// A 24-hour window for budget replenishment, aligning with natural human cycles
pub const BUDGET_WINDOW_SECONDS: u64 = 86400;

pub fn consume_budget(agent: &AgentPubKey, cost: f32) -> ExternResult<()> {
    let mut budget_state = get_budget_state(agent)?;

    if budget_state.remaining_ru < cost {
        return Err(wasm_error!(WasmErrorInner::Guest("E_BUDGET_EXCEEDED: Agent budget exceeded.".into())));
    }

    budget_state.remaining_ru -= cost;
    update_budget_entry(agent, budget_state.remaining_ru, budget_state.window_start)?; // Update the budget entry
    Ok(())
}

pub fn get_budget_state(agent: &AgentPubKey) -> ExternResult<BudgetState> {
    let now = sys_time()?;
    let agent_address = agent.clone();

    let path = Path::from(format!("agent_budget.{}", agent_address));
    let links = get_links(GetLinksInputBuilder::try_new(path.path_entry_hash()?, LinkTypes::AgentBudget)?.build())?;

    let mut latest_budget: Option<BudgetEntry> = None;
    let mut latest_timestamp: Option<Timestamp> = None;

    for link in links {
        if let Some(record) = get(link.target.clone(), GetOptions::default())? {
            if let Some(budget_entry) = record.entry().to_app_option::<BudgetEntry>()? {
                if latest_timestamp.is_none() || budget_entry.window_start > latest_timestamp.unwrap() {
                    latest_budget = Some(budget_entry);
                    latest_timestamp = Some(budget_entry.window_start);
                }
            }
        }
    }

    match latest_budget {
        Some(budget) if (now.as_seconds() - budget.window_start.as_seconds()) < BUDGET_WINDOW_SECONDS => {
            Ok(BudgetState { agent: agent_address, remaining_ru: budget.remaining_ru, window_start: budget.window_start })
        },
        _ => {
            // Initialize or reset budget
            let new_budget = BudgetState { agent: agent_address, remaining_ru: MAX_RU_PER_WINDOW, window_start: now };
            create_budget_entry(agent, new_budget.remaining_ru, new_budget.window_start)?; // Create a new budget entry
            Ok(new_budget)
        }
    }
}

fn create_budget_entry(agent: &AgentPubKey, remaining_ru: f32, window_start: Timestamp) -> ExternResult<ActionHash> {
    let budget_entry = BudgetEntry { agent: agent.clone(), remaining_ru, window_start };
    let hash = create_entry(&budget_entry)?;
    let path = Path::from(format!("agent_budget.{}", agent.clone()));
    create_link(path.path_entry_hash()?, hash.clone(), LinkTypes::AgentBudget, ())?;
    Ok(hash)
}

fn update_budget_entry(agent: &AgentPubKey, remaining_ru: f32, window_start: Timestamp) -> ExternResult<ActionHash> {
    let budget_entry = BudgetEntry { agent: agent.clone(), remaining_ru, window_start };
    let hash = create_entry(&budget_entry)?;
    let path = Path::from(format!("agent_budget.{}", agent.clone()));
    create_link(path.path_entry_hash()?, hash.clone(), LinkTypes::AgentBudget, ())?;
    Ok(hash)
}

pub struct BudgetState {
    pub agent: AgentPubKey,
    pub remaining_ru: f32,
    pub window_start: Timestamp,
}

/// BudgetEngine manages resource units (RU) for autonomous operations
/// Implements resource-bounded autonomy with graceful degradation
pub struct BudgetEngine;

impl BudgetEngine {
    /// Reserve resource units (RU) for an operation
    /// Returns an error if insufficient budget is available
    pub fn reserve_ru(agent: &AgentPubKey, amount: f32) -> ExternResult<()> {
        let budget_state = get_budget_state(agent)?;

        if budget_state.remaining_ru >= amount {
            // Consume the budget by updating the state
            consume_budget(agent, amount)?;
            Ok(())
        } else {
            Err(wasm_error!(WasmErrorInner::Guest(
                format!(
                    "E_INSUFFICIENT_RU: need {:.2} RU, have {:.2} RU. Budget resets at {:?}",
                    amount,
                    budget_state.remaining_ru,
                    budget_state.window_start.as_seconds() + BUDGET_WINDOW_SECONDS
                )
            )))
        }
    }

    /// Allocate additional budget to an agent
    /// Used for budget replenishment or granting additional resources
    pub fn allocate_budget(agent: &AgentPubKey, amount: f32) -> ExternResult<()> {
        let budget_state = get_budget_state(agent)?;
        let new_total = budget_state.remaining_ru + amount;

        // Cap at maximum budget to prevent abuse
        let capped_total = new_total.min(MAX_RU_PER_WINDOW * 2.0); // Allow 2x max for special cases

        update_budget_entry(agent, capped_total, budget_state.window_start)?;
        Ok(())
    }

    /// Get current budget status for an agent
    pub fn get_status(agent: &AgentPubKey) -> ExternResult<BudgetState> {
        get_budget_state(agent)
    }

    /// Check if an agent has sufficient budget for an operation
    pub fn has_budget(agent: &AgentPubKey, amount: f32) -> ExternResult<bool> {
        let budget_state = get_budget_state(agent)?;
        Ok(budget_state.remaining_ru >= amount)
    }
}