// Package imagecontext is the image bounded context: standalone image compression,
// format conversion, quality metrics. Mirrors python/pdf_toolkit/image_context.
package imagecontext

import "pdftoolkit/sharedkernel"

type ImageFormat string

const (
	JPEG ImageFormat = "jpeg"
	PNG  ImageFormat = "png"
	WebP ImageFormat = "webp"
	AVIF ImageFormat = "avif"
)

// Ports -----------------------------------------------------------------------

// ImageCodec decodes, resizes and re-encodes raster images. The concrete type of
// the decoded image is adapter-specific (image.Image for the x/image adapter),
// so it travels as `any` through the port — mirrors the Python duck-typed port.
type ImageCodec interface {
	Decode(data []byte) (any, error)
	Resize(img any, width, height int, resample string) (any, error)
	Encode(img any, format ImageFormat, quality int) ([]byte, error)
}

type QualityMeter interface {
	Score(original, candidate []byte) (sharedkernel.PerceptualScore, error)
}
