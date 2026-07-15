//! image context — native adapters stub.
//!
//! Planned: the `image` + `fast_image_resize` crates for decode/Lanczos resize,
//! `mozjpeg` for optimal JPEG, and `dssim` for the QualityMeter. Rust has the
//! strongest native image-codec ecosystem of the three languages. See DOMAIN.md.

use super::domain::ImageFormat;
use super::ports::{ImageCodec, QualityMeter};
use crate::pdf_context::domain::ResampleFilter;
use crate::shared_kernel::PerceptualScore;

const NOT_IMPL: &str = "not implemented: pending image-crate adapter (see DOMAIN.md)";

pub struct ImageCrateCodec;

impl ImageCodec for ImageCrateCodec {
    type Image = Vec<u8>; // placeholder until the `image` crate lands

    fn decode(&self, _: &[u8]) -> Result<Self::Image, String> {
        Err(NOT_IMPL.into())
    }
    fn resize(&self, _: &Self::Image, _: u32, _: u32, _: ResampleFilter) -> Result<Self::Image, String> {
        Err(NOT_IMPL.into())
    }
    fn encode(&self, _: &Self::Image, _: ImageFormat, _: u32) -> Result<Vec<u8>, String> {
        Err(NOT_IMPL.into())
    }
}

pub struct DssimMeter;

impl QualityMeter for DssimMeter {
    fn score(&self, _: &[u8], _: &[u8]) -> Result<PerceptualScore, String> {
        Err(NOT_IMPL.into())
    }
}
