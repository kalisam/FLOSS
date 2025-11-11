use crate::{SensorPacket, TransportError};

pub trait TransportSink {
    fn send(&mut self, pkt: &SensorPacket) -> Result<(), TransportError>;
}
