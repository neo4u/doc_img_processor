//! Rust CLI mirror: compress via the Ghostscript engine (working). The lopdf
//! native engine is stubbed. Mirrors python/pdf_toolkit/cli/main.py.

use std::path::Path;
use std::process::exit;

use pdftoolkit::pdf_context::domain::CompressionTarget;
use pdftoolkit::pdf_context::infra_ghostscript::GhostscriptCompressor;
use pdftoolkit::pdf_context::ports::Compressor;
use pdftoolkit::shared_kernel::{ByteBudget, MediaFile};

fn usage() {
    println!(
        "pdftoolkit (rust) — mirror of the Python reference\n\n\
         usage:\n  pdftoolkit compress <in.pdf> <out.pdf> [targetKB]\n\n\
         engines: ghostscript (working), lopdf+image (stubbed — see DOMAIN.md)"
    );
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        usage();
        exit(1);
    }
    match args[1].as_str() {
        "compress" => {
            if args.len() < 4 {
                usage();
                exit(1);
            }
            let kb: u64 = args.get(4).and_then(|s| s.parse().ok()).unwrap_or(1000);
            let budget = match ByteBudget::kb(kb, 0.0) {
                Ok(b) => b,
                Err(e) => {
                    eprintln!("error: {e}");
                    exit(1);
                }
            };
            let src = MediaFile::new(args[2].as_str());
            if !src.exists() {
                eprintln!("error: no such file: {}", args[2]);
                exit(1);
            }
            let engine = GhostscriptCompressor::default();
            match engine.compress(&src, &CompressionTarget::with_budget(budget), Path::new(&args[3])) {
                Ok(r) => println!(
                    "{}: {}KB -> {}KB ({:.0}% off) dpi={} {}ms",
                    r.engine,
                    r.before_bytes / 1000,
                    r.after_bytes / 1000,
                    r.saved_pct(),
                    r.dpi_used,
                    r.elapsed_ms
                ),
                Err(e) => {
                    eprintln!("error: {e}");
                    exit(1);
                }
            }
        }
        _ => {
            usage();
            exit(1);
        }
    }
}
