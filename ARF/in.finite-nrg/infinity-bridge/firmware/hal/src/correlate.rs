#[derive(Debug, Clone, Copy, PartialEq)]
pub struct CorrelationResult {
    pub peak: f32,
    pub lag_samples: i64,
}

pub fn normalized_xcorr(a: &[f32], b: &[f32]) -> CorrelationResult {
    if a.is_empty() || b.is_empty() { return CorrelationResult { peak: 0.0, lag_samples: 0 }; }
    let n = a.len().min(b.len());
    let (a, b) = (&a[..n], &b[..n]);
    let mean = |x: &[f32]| x.iter().sum::<f32>() / x.len() as f32;
    let ma = mean(a);
    let mb = mean(b);
    let va = a.iter().map(|x| (x - ma)*(x - ma)).sum::<f32>().sqrt();
    let vb = b.iter().map(|x| (x - mb)*(x - mb)).sum::<f32>().sqrt();
    if va == 0.0 || vb == 0.0 {
        return CorrelationResult { peak: 0.0, lag_samples: 0 };
    }
    let mut best = (0.0f32, 0i64);
    let max_lag = (n as i64)/4;
    for lag in -max_lag..=max_lag {
        let mut num = 0.0f32;
        let den = va * vb;
        for i in 0..n {
            let j = i as i64 + lag;
            if j < 0 || j >= n as i64 { continue; }
            num += (a[i] - ma) * (b[j as usize] - mb);
        }
        let r = if den != 0.0 { num / den } else { 0.0 };
        if r.abs() > best.0.abs() { best = (r, lag); }
    }
    CorrelationResult { peak: best.0.clamp(-1.0, 1.0).abs(), lag_samples: best.1 }
}
