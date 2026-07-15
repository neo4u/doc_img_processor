//! image context — ports (traits).

use super::domain::ImageFormat;
use crate::pdf_context::domain::ResampleFilter;
use crate::shared_kernel::PerceptualScore;

/// Decodes, resizes and re-encodes raster images. The decoded image type is
/// adapter-specific (an associated type), mirroring Python's duck-typed port.
pub trait ImageCodec {
    type Image;
    fn decode(&self, data: &[u8]) -> Result<Self::Image, String>;
    fn resize(
        &self,
        img: &Self::Image,
        width: u32,
        height: u32,
        resample: ResampleFilter,
    ) -> Result<Self::Image, String>;
    fn encode(&self, img: &Self::Image, format: ImageFormat, quality: u32) -> Result<Vec<u8>, String>;
}

pub trait QualityMeter {
    fn score(&self, original: &[u8], candidate: &[u8]) -> Result<PerceptualScore, String>;
}
