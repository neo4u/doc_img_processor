//! pdf context — Ghostscript engine (escalation/baseline). Uses std::process only,
//! so no external crates. Mirrors the Python and Go GS adapters.

use std::fs;
use std::path::Path;
use std::process::Command;
use std::time::Instant;

use super::domain::{CompressionResult, CompressionTarget};
use super::ports::Compressor;
use crate::shared_kernel::MediaFile;

pub struct GhostscriptCompressor {
    pub bin: String,
    pub iterations: u32,
}

impl Default for GhostscriptCompressor {
    fn default() -> Self {
        Self { bin: "gs".into(), iterations: 8 }
    }
}

impl GhostscriptCompressor {
    fn run(&self, src: &Path, dst: &Path, dpi: u32) -> Result<u64, String> {
        let status = Command::new(&self.bin)
            .args([
                "-sDEVICE=pdfwrite",
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                "-dPDFSETTINGS=/default",
                &format!("-dColorImageResolution={dpi}"),
                &format!("-dGrayImageResolution={dpi}"),
                &format!("-dMonoImageResolution={dpi}"),
                "-dDownsampleColorImages=true",
                "-dDownsampleGrayImages=true",
                &format!("-sOutputFile={}", dst.display()),
            ])
            .arg(src)
            .status()
            .map_err(|e| e.to_string())?;
        if !status.success() {
            return Err("ghostscript failed".into());
        }
        Ok(fs::metadata(dst).map_err(|e| e.to_string())?.len())
    }
}

impl Compressor for GhostscriptCompressor {
    fn name(&self) -> &str {
        "ghostscript"
    }

    fn compress(
        &self,
        source: &MediaFile,
        target: &CompressionTarget,
        out: &Path,
    ) -> Result<CompressionResult, String> {
        let start = Instant::now();
        let ceiling = target.budget.ceiling();
        let src_size = source.size_bytes();

        let make = |dpi: u32| -> CompressionResult {
            let after = fs::metadata(out).map(|m| m.len()).unwrap_or(0);
            CompressionResult {
                output: MediaFile::new(out),
                engine: "ghostscript".into(),
                before_bytes: src_size,
                after_bytes: after,
                dpi_used: dpi,
                quality_used: 0,
                score: None,
                elapsed_ms: start.elapsed().as_millis(),
                escalated: false,
            }
        };

        if src_size <= ceiling {
            fs::copy(&source.path, out).map_err(|e| e.to_string())?;
            return Ok(make(0));
        }

        let (mut lo, mut hi) = target.dpi_range;
        let mut best = lo;
        let tmp = std::env::temp_dir().join("pdftoolkit_gsprobe.pdf");
        for _ in 0..self.iterations {
            let mid = (lo + hi) / 2;
            let size = self.run(&source.path, &tmp, mid)?;
            if size <= ceiling {
                best = mid;
                lo = mid;
            } else {
                hi = mid;
            }
        }
        let _ = fs::remove_file(&tmp);
        self.run(&source.path, out, best)?;
        // Hard rule #1: never emit larger than input.
        if fs::metadata(out).map(|m| m.len()).unwrap_or(0) >= src_size {
            fs::copy(&source.path, out).map_err(|e| e.to_string())?;
            best = 0;
        }
        Ok(make(best))
    }
}
