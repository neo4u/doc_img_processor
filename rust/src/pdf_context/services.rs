//! pdf context — domain services. Pure; no external crates.
//! Mirrors python/pdf_toolkit/pdf_context/services.py.

use std::collections::HashMap;

use super::domain::DocumentCensus;
use crate::shared_kernel::{PerceptualScore, QualityFloor};

/// Finds the largest encoder quality whose output fits `slice_bytes` while clearing
/// the QualityFloor. `encode` maps quality -> (byte size, score); size must be
/// monotonic non-decreasing in quality.
pub struct TargetSizeSearch {
    pub lo: u32,
    pub hi: u32,
    pub floor: QualityFloor,
}

impl TargetSizeSearch {
    pub fn best_quality<F>(&self, slice_bytes: u64, mut encode: F) -> Option<(u32, PerceptualScore)>
    where
        F: FnMut(u32) -> (u64, PerceptualScore),
    {
        let (mut lo, mut hi) = (self.lo, self.hi);
        let mut best: Option<(u32, PerceptualScore)> = None;
        while hi - lo > 1 {
            let q = (lo + hi) / 2;
            let (size, score) = encode(q);
            if size <= slice_bytes {
                if self.floor.accepts(score) {
                    best = Some((q, score));
                }
                lo = q; // try higher quality
            } else {
                hi = q; // too big, lower quality
            }
        }
        best
    }
}

/// Splits an image byte budget across images ∝ rendered area.
pub fn allocate_budget(census: &DocumentCensus, image_budget: u64) -> HashMap<u32, u64> {
    let total = census.total_rendered_area();
    let mut out = HashMap::new();
    for img in &census.images {
        let v = ((image_budget as f64) * img.rendered_area_sqin / total) as u64;
        out.insert(img.xref, v.max(1));
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::pdf_context::domain::*;
    use crate::shared_kernel::*;

    #[test]
    fn page_range_validation() {
        assert!(PageRange::new(0, 3).is_err());
        assert!(PageRange::new(5, 3).is_err());
        let r = PageRange::new(3, 5).unwrap();
        assert_eq!(r.len(), 3);
        assert_eq!(r.label(), "p3-5");
    }

    fn img(xref: u32, area: f64) -> EmbeddedImage {
        EmbeddedImage {
            xref,
            page_index: 0,
            width: 0,
            height: 0,
            kind: ImageKind::Color,
            codec: Codec::Jpeg,
            effective_dpi: EffectiveDpi { pixels: 0, rendered_inches: 1.0 },
            rendered_area_sqin: area,
        }
    }

    #[test]
    fn budget_split_by_area() {
        let census = DocumentCensus {
            file: MediaFile::new("x"),
            page_count: 1,
            non_image_bytes: 0,
            images: vec![img(1, 90.0), img(2, 10.0)],
        };
        let got = allocate_budget(&census, 1000);
        assert_eq!(got[&1], 900);
        assert_eq!(got[&2], 100);
    }

    #[test]
    fn search_picks_largest_fitting_quality() {
        let floor = QualityFloor { metric: Metric::Ssim, threshold: 0.0 };
        let s = TargetSizeSearch { lo: 20, hi: 95, floor };
        let (q, _) = s
            .best_quality(600, |q| {
                (q as u64 * 10, PerceptualScore { metric: Metric::Ssim, value: 0.99 })
            })
            .unwrap();
        assert!((55..=60).contains(&q));
    }

    #[test]
    fn search_respects_floor() {
        let floor = QualityFloor { metric: Metric::Ssim, threshold: 0.95 };
        let s = TargetSizeSearch { lo: 20, hi: 95, floor };
        let got = s.best_quality(1000, |_q| {
            (1, PerceptualScore { metric: Metric::Ssim, value: 0.90 })
        });
        assert!(got.is_none());
    }

    #[test]
    fn effective_dpi_scale() {
        let e = EffectiveDpi { pixels: 6600, rendered_inches: 8.5 };
        let s = e.scale_to(200.0);
        assert!(s > 0.25 && s < 0.26);
        assert_eq!(e.scale_to(2000.0), 1.0);
    }
}
