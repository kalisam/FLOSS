use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub enum SyncSource { Local, NTP, PTP, PPS10MHz }

#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
pub struct SyncQuality {
    pub score: f32,      // 0..1
    pub drift_ns: i64,   // instantaneous
    pub source: SyncSource,
}
impl SyncQuality {
    pub fn with_score(score: f32, drift_ns: i64, source: SyncSource) -> Self { Self { score, drift_ns, source } }
    pub fn is_acceptable(&self, max_drift_ns: i64, min_score: f32) -> bool {
        self.score >= min_score && self.drift_ns.abs() <= max_drift_ns
    }
}
