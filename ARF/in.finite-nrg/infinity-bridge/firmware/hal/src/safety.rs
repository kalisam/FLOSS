use crate::{Domain, SafetyError};

pub const MAX_SPL_DB: f32 = 120.0;
pub const MAX_RF_EIRP_DBM: f32 = 30.0;
pub const MAX_OPTICAL_CLASS: u8 = 1;

pub fn validate_output_level(level: f32, domain: Domain) -> Result<(), SafetyError> {
    match domain {
        Domain::Acoustic if level > MAX_SPL_DB => Err(SafetyError::ExceedsLimit),
        Domain::RF if level > MAX_RF_EIRP_DBM => Err(SafetyError::ExceedsLimit),
        Domain::Optical if level as u8 > MAX_OPTICAL_CLASS => Err(SafetyError::ExceedsLimit),
        _ => Ok(()),
    }
}
