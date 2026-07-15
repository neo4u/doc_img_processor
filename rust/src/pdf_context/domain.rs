//! pdf context — domain layer. Mirrors python/pdf_toolkit/pdf_context/domain.

use crate::shared_kernel::{ByteBudget, EffectiveDpi, MediaFile, PerceptualScore, QualityFloor};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ImageKind {
    Bitonal,
    Grayscale,
    Color,
}

impl ImageKind {
    pub fn is_contone(&self) -> bool {
        !matches!(self, ImageKind::Bitonal)
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Codec {
    Jpeg,
    CcittG4,
    Flate,
    Png,
    Jbig2,
    Raw,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ResampleFilter {
    Nearest,
    Lanczos,
}

/// 1-indexed, inclusive.
#[derive(Clone, Copy, Debug)]
pub struct PageRange {
    pub start: u32,
    pub end: u32,
}

impl PageRange {
    pub fn new(start: u32, end: u32) -> Result<Self, String> {
        if start < 1 {
            return Err(format!("start must be >= 1, got {start}"));
        }
        if end < start {
            return Err(format!("end ({end}) < start ({start})"));
        }
        Ok(Self { start, end })
    }
    pub fn single(p: u32) -> Result<Self, String> {
        Self::new(p, p)
    }
    pub fn pages(&self) -> Vec<u32> {
        (self.start..=self.end).collect()
    }
    pub fn len(&self) -> u32 {
        self.end - self.start + 1
    }
    pub fn is_empty(&self) -> bool {
        false
    }
    pub fn label(&self) -> String {
        if self.len() == 1 {
            format!("p{}", self.start)
        } else {
            format!("p{}-{}", self.start, self.end)
        }
    }
}

#[derive(Clone, Debug)]
pub struct SplitSpec {
    pub name: String,
    pub range: PageRange,
}

/// One raster image on a page.
#[derive(Clone, Copy, Debug)]
pub struct EmbeddedImage {
    pub xref: u32,
    pub page_index: u32,
    pub width: u32,
    pub height: u32,
    pub kind: ImageKind,
    pub codec: Codec,
    pub effective_dpi: EffectiveDpi,
    pub rendered_area_sqin: f64,
}

impl EmbeddedImage {
    /// Hard rule #2: bitonal must not be interpolated into gray.
    pub fn resample(&self) -> ResampleFilter {
        if matches!(self.kind, ImageKind::Bitonal) {
            ResampleFilter::Nearest
        } else {
            ResampleFilter::Lanczos
        }
    }
}

/// Output of inspect: what's inside a PDF.
#[derive(Clone, Debug)]
pub struct DocumentCensus {
    pub file: MediaFile,
    pub page_count: u32,
    pub images: Vec<EmbeddedImage>,
    pub non_image_bytes: u64,
}

impl DocumentCensus {
    pub fn total_rendered_area(&self) -> f64 {
        let t: f64 = self.images.iter().map(|i| i.rendered_area_sqin).sum();
        if t == 0.0 {
            1.0
        } else {
            t
        }
    }
}

#[derive(Clone, Copy, Debug)]
pub struct CompressionTarget {
    pub budget: ByteBudget,
    pub quality_floor: QualityFloor,
    pub dpi_cap: u32,
    pub dpi_range: (u32, u32),
    pub quality_range: (u32, u32),
}

impl CompressionTarget {
    pub fn with_budget(budget: ByteBudget) -> Self {
        Self {
            budget,
            quality_floor: QualityFloor::default(),
            dpi_cap: 200,
            dpi_range: (72, 300),
            quality_range: (20, 95),
        }
    }
}

#[derive(Clone, Copy, Debug)]
pub struct CompressionRecipe {
    pub xref: u32,
    pub dpi_target: u32,
    pub quality: u32,
    pub codec: Codec,
    pub resample: ResampleFilter,
}

#[derive(Clone, Debug)]
pub struct CompressionResult {
    pub output: MediaFile,
    pub engine: String,
    pub before_bytes: u64,
    pub after_bytes: u64,
    pub dpi_used: u32,
    pub quality_used: u32,
    pub score: Option<PerceptualScore>,
    pub elapsed_ms: u128,
    pub escalated: bool,
}

impl CompressionResult {
    pub fn ratio(&self) -> f64 {
        if self.before_bytes == 0 {
            1.0
        } else {
            self.after_bytes as f64 / self.before_bytes as f64
        }
    }
    pub fn saved_pct(&self) -> f64 {
        100.0 * (1.0 - self.ratio())
    }
}
