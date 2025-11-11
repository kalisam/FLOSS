use infinity_hal::{InfinityBridgeHal, MockBridge};

#[test]
fn gate3_truth_test_example() {
    let b = MockBridge::default();
    let a: Vec<f32> = (0..1024).map(|i| ((i as f32)/50.0).sin()).collect();
    let mut bvec: Vec<f32> = vec![0.0; 1024];
    for i in 3..1024 { bvec[i] = a[i-3] + (i as f32).sin()*1e-4; }
    let res = b.correlate_local(&a, &bvec);
    assert!(res.peak > 0.7, "peak={}", res.peak);
    assert!(res.lag_samples.abs() <= 10, "lag={}", res.lag_samples);
}
