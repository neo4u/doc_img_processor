//! pdf context — ports (traits). Adapters in infra_*.rs implement these.

use std::path::Path;

use super::domain::{CompressionResult, CompressionTarget, DocumentCensus, SplitSpec};
use crate::shared_kernel::MediaFile;

pub trait Splitter {
    fn split(
        &self,
        source: &MediaFile,
        specs: &[SplitSpec],
        out_dir: &Path,
    ) -> Result<Vec<MediaFile>, String>;
}

pub trait PdfInspector {
    fn inspect(&self, source: &MediaFile) -> Result<DocumentCensus, String>;
}

/// A whole-document compressor. GS, lopdf-native, etc. all fit here.
pub trait Compressor {
    fn name(&self) -> &str;
    fn compress(
        &self,
        source: &MediaFile,
        target: &CompressionTarget,
        out: &Path,
    ) -> Result<CompressionResult, String>;
}
