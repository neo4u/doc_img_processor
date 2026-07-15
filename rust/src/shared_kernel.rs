//! Shared kernel — value objects used by both the pdf and image contexts.
//! Mirrors python/pdf_toolkit/shared_kernel and go/sharedkernel.

use std::fs;
use std::path::PathBuf;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Metric {
    Ssim,
    Dssim,
    Butteraugli,
}

impl Metric {
    pub fn higher_is_better(&self) -> bool {
        matches!(self, Metric::Ssim)
    }
}

/// A file on disk; identity is its content hash.
#[derive(Clone, Debug)]
pub struct MediaFile {
    pub path: PathBuf,
}

impl MediaFile {
    pub fn new<P: Into<PathBuf>>(p: P) -> Self {
        Self { path: p.into() }
    }
    pub fn exists(&self) -> bool {
        self.path.exists()
    }
    pub fn size_bytes(&self) -> u64 {
        fs::metadata(&self.path).map(|m| m.len()).unwrap_or(0)
    }
}

/// A target size with an optional over-tolerance fraction.
#[derive(Clone, Copy, Debug)]
pub struct ByteBudget {
    pub target_bytes: u64,
    pub over_tolerance: f64,
}

impl ByteBudget {
    pub fn new(target_bytes: u64, over_tolerance: f64) -> Result<Self, String> {
        if target_bytes == 0 {
            return Err("target_bytes must be positive".into());
        }
        if over_tolerance < 0.0 {
            return Err("over_tolerance must be >= 0".into());
        }
        Ok(Self { target_bytes, over_tolerance })
    }
    pub fn kb(kb: u64, tol: f64) -> Result<Self, String> {
        Self::new(kb * 1000, tol)
    }
    pub fn ceiling(&self) -> u64 {
        (self.target_bytes as f64 * (1.0 + self.over_tolerance)) as u64
    }
    pub fn contains(&self, n: u64) -> bool {
        n <= self.ceiling()
    }
}

#[derive(Clone, Copy, Debug)]
pub struct PerceptualScore {
    pub metric: Metric,
    pub value: f64,
}

impl PerceptualScore {
    pub fn is_at_least(&self, threshold: f64) -> bool {
        if self.metric.higher_is_better() {
            self.value >= threshold
        } else {
            self.value <= threshold
        }
    }
}

/// A perceptual acceptance threshold enforced as a domain invariant.
#[derive(Clone, Copy, Debug)]
pub struct QualityFloor {
    pub metric: Metric,
    pub threshold: f64,
}

impl Default for QualityFloor {
    fn default() -> Self {
        Self { metric: Metric::Ssim, threshold: 0.90 }
    }
}

impl QualityFloor {
    pub fn accepts(&self, s: PerceptualScore) -> bool {
        s.is_at_least(self.threshold)
    }
}

/// Resolution as rendered on the page — from geometry, never metadata.
#[derive(Clone, Copy, Debug)]
pub struct EffectiveDpi {
    pub pixels: u32,
    pub rendered_inches: f64,
}

impl EffectiveDpi {
    pub fn value(&self) -> f64 {
        if self.rendered_inches <= 0.0 {
            0.0
        } else {
            self.pixels as f64 / self.rendered_inches
        }
    }
    /// Factor (<= 1.0) to reach `target_dpi`; never upscales.
    pub fn scale_to(&self, target_dpi: f64) -> f64 {
        let v = self.value();
        if v <= 0.0 {
            return 1.0;
        }
        let s = target_dpi / v;
        if s < 1.0 {
            s
        } else {
            1.0
        }
    }
}
