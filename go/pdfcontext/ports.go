package pdfcontext

import "pdftoolkit/sharedkernel"

// Ports (interfaces). Adapters in infra_*.go implement these — mirrors the Python
// ABCs and Rust traits of the same names.

type Splitter interface {
	Split(source sharedkernel.MediaFile, specs []SplitSpec, outDir string) ([]sharedkernel.MediaFile, error)
}

type PdfInspector interface {
	Inspect(source sharedkernel.MediaFile) (DocumentCensus, error)
}

type PdfCodec interface {
	ExtractImage(source sharedkernel.MediaFile, xref int) ([]byte, string, error)
	StructuralOptimize(source sharedkernel.MediaFile, out string) (sharedkernel.MediaFile, error)
}

// Compressor is a whole-document compressor. GS, pdfcpu-native, etc. all fit here.
type Compressor interface {
	Name() string
	Compress(source sharedkernel.MediaFile, target CompressionTarget, out string) (CompressionResult, error)
}
