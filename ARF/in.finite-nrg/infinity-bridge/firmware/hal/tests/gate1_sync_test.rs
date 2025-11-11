use infinity_hal::{sync::*, MockBridge, InfinityBridgeHal};

#[test]
fn gate1_sync_sanity_blocks_when_low_confidence() {
    let mut b = MockBridge::default();
    assert!(b.get_time_sync_quality().is_acceptable(100_000, 0.8));
    b.sync = SyncQuality::with_score(0.5, 2_000_000, SyncSource::NTP);
    assert!(!b.get_time_sync_quality().is_acceptable(100_000, 0.8));
}
