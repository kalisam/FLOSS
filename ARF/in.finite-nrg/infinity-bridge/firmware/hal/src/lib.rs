pub mod sync;
pub mod safety;
pub mod transport;
pub mod correlate;

use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub enum Domain { RF, Optical, Acoustic }

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub enum Transport { USB3, GigE, UDP, ZMQ }

#[derive(Debug, Serialize, Deserialize)]
pub struct SensorPacket<'a> {
    pub bridge_id: &'a str,
    pub domain: Domain,
    pub tai_timestamp_ns: u64,
    pub sample_rate_hz: u32,
    pub payload_le: &'a [u8],
}

#[derive(thiserror::Error, Debug)]
pub enum TimeSyncError {
    #[error("sync source not available")] NotAvailable,
    #[error("clock drift exceeds threshold")] Drift,
}

#[derive(thiserror::Error, Debug)]
pub enum SafetyError {
    #[error("requested output exceeds limit")] ExceedsLimit,
    #[error("unsafe condition detected")] Unsafe,
}

#[derive(thiserror::Error, Debug)]
pub enum TransportError {
    #[error("transport send failed")] SendFailed,
    #[error("transport not ready")] NotReady,
}

pub trait InfinityBridgeHal {
    fn get_time_sync_quality(&self) -> sync::SyncQuality;
    fn get_timestamp_ns(&self) -> Result<u64, TimeSyncError>;
    fn validate_output_safe(&self, level: f32, domain: Domain) -> Result<(), SafetyError>;
    fn emergency_shutdown(&mut self);
    fn send_packet(&mut self, packet: &SensorPacket) -> Result<(), TransportError>;
    fn preferred_transport(&self) -> Transport;
    fn correlate_local(&self, a: &[f32], b: &[f32]) -> correlate::CorrelationResult {
        correlate::normalized_xcorr(a, b)
    }
}

pub struct MockBridge {
    pub id: String,
    pub sync: sync::SyncQuality,
}

impl Default for MockBridge {
    fn default() -> Self {
        Self {
            id: "mock-001".into(),
            sync: sync::SyncQuality::with_score(0.95, 1000, sync::SyncSource::PTP),
        }
    }
}

impl InfinityBridgeHal for MockBridge {
    fn get_time_sync_quality(&self) -> sync::SyncQuality { self.sync }
    fn get_timestamp_ns(&self) -> Result<u64, TimeSyncError> { Ok(42_000_000_000) }
    fn validate_output_safe(&self, level: f32, domain: Domain) -> Result<(), SafetyError> {
        safety::validate_output_level(level, domain)
    }
    fn emergency_shutdown(&mut self) { }
    fn send_packet(&mut self, _packet: &SensorPacket) -> Result<(), TransportError> { Ok(()) }
    fn preferred_transport(&self) -> Transport { Transport::GigE }
}
