use infinity_hal::{Domain, InfinityBridgeHal, MockBridge, SafetyError};

#[test]
fn gate2_safety_caps_enforced() {
    let b = MockBridge::default();
    let err = b.validate_output_safe(100.0, Domain::RF).err().unwrap();
    assert!(matches!(err, SafetyError::ExceedsLimit));
    assert!(b.validate_output_safe(80.0, Domain::Acoustic).is_ok());
}
