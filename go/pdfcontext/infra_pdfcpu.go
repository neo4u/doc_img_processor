package pdfcontext

import (
	"fmt"

	"pdftoolkit/sharedkernel"
)

// Planned Go stack (mirrors the Python pikepdf composite):
//   - github.com/pdfcpu/pdfcpu  — split/merge/optimize + image extract/replace (Apache-2.0)
//   - golang.org/x/image/draw   — CatmullRom/ApproxBiLinear resize (Lanczos-equivalent)
//   - image/jpeg (stdlib)       — re-encode
// These are stubs so `go build` stays dependency-free until the adapters land.
// TODO(port): implement using pdfcpu; share the per-image decision with
// TargetSizeSearch + AllocateBudget, exactly like image_context.recompress_to_slice.

var errNotImplemented = fmt.Errorf("not implemented: pending pdfcpu adapter (see DOMAIN.md)")

// PdfcpuSplitter will split via pdfcpu's page-range API.
type PdfcpuSplitter struct{}

func (PdfcpuSplitter) Split(sharedkernel.MediaFile, []SplitSpec, string) ([]sharedkernel.MediaFile, error) {
	return nil, errNotImplemented
}

// PdfcpuInspector will build a DocumentCensus (effective DPI from page geometry).
type PdfcpuInspector struct{}

func (PdfcpuInspector) Inspect(sharedkernel.MediaFile) (DocumentCensus, error) {
	return DocumentCensus{}, errNotImplemented
}

// NativeCompressor will be the license-clean primary engine (pdfcpu + x/image).
type NativeCompressor struct {
	Escalation Compressor // Ghostscript, fired on BudgetMissed
}

func (NativeCompressor) Name() string { return "pdfcpu+xdraw" }

func (NativeCompressor) Compress(sharedkernel.MediaFile, CompressionTarget, string) (CompressionResult, error) {
	return CompressionResult{}, errNotImplemented
}
