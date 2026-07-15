//! pdf context — native engine stub (license-clean primary, to be built).
//!
//! Planned Rust stack (mirrors the Python pikepdf composite):
//!   - lopdf              parse/rewrite the PDF object model (MIT)
//!   - image + fast_image_resize   decode / Lanczos resize
//!   - mozjpeg            optimal JPEG encode
//!   - dssim              perceptual metric (QualityMeter)
//! Share the per-image decision with TargetSizeSearch + allocate_budget, exactly
//! like image_context::recompress_to_slice in Python. See ../../DOMAIN.md.

use std::path::Path;

use super::domain::{CompressionResult, CompressionTarget, DocumentCensus, SplitSpec};
use super::ports::{Compressor, PdfInspector, Splitter};
use crate::shared_kernel::MediaFile;

const NOT_IMPL: &str = "not implemented: pending lopdf adapter (see DOMAIN.md)";

pub struct LopdfSplitter;

impl Splitter for LopdfSplitter {
    fn split(&self, _: &MediaFile, _: &[SplitSpec], _: &Path) -> Result<Vec<MediaFile>, String> {
        Err(NOT_IMPL.into())
    }
}

pub struct LopdfInspector;

impl PdfInspector for LopdfInspector {
    fn inspect(&self, _: &MediaFile) -> Result<DocumentCensus, String> {
        Err(NOT_IMPL.into())
    }
}

pub struct NativeCompressor;

impl Compressor for NativeCompressor {
    fn name(&self) -> &str {
        "lopdf+image"
    }
    fn compress(
        &self,
        _: &MediaFile,
        _: &CompressionTarget,
        _: &Path,
    ) -> Result<CompressionResult, String> {
        Err(NOT_IMPL.into())
    }
}
