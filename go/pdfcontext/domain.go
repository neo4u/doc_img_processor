// Package pdfcontext is the pdf bounded context: splitting, PDF-level compression,
// and page/image census. Flat package (idiomatic Go); files split by DDD layer.
// Mirrors python/pdf_toolkit/pdf_context. See ../../DOMAIN.md.
package pdfcontext

import (
	"fmt"

	"pdftoolkit/sharedkernel"
)

// --- Enums -------------------------------------------------------------------

type ImageKind string

const (
	Bitonal   ImageKind = "bitonal"
	Grayscale ImageKind = "grayscale"
	Color     ImageKind = "color"
)

func (k ImageKind) IsContone() bool { return k != Bitonal }

type Codec string

const (
	JPEG    Codec = "jpeg"
	CCITTG4 Codec = "ccitt_g4"
	Flate   Codec = "flate"
	PNG     Codec = "png"
	JBIG2   Codec = "jbig2"
	Raw     Codec = "raw"
)

type ResampleFilter string

const (
	Nearest ResampleFilter = "nearest"
	Lanczos ResampleFilter = "lanczos"
)

// --- Value objects -----------------------------------------------------------

// PageRange is 1-indexed and inclusive.
type PageRange struct {
	Start int
	End   int
}

func NewPageRange(start, end int) (PageRange, error) {
	if start < 1 {
		return PageRange{}, fmt.Errorf("start must be >= 1, got %d", start)
	}
	if end < start {
		return PageRange{}, fmt.Errorf("end (%d) < start (%d)", end, start)
	}
	return PageRange{start, end}, nil
}

func SinglePage(p int) (PageRange, error) { return NewPageRange(p, p) }

func (r PageRange) Pages() []int {
	out := make([]int, 0, r.Len())
	for i := r.Start; i <= r.End; i++ {
		out = append(out, i)
	}
	return out
}

func (r PageRange) Len() int { return r.End - r.Start + 1 }

func (r PageRange) String() string {
	if r.Len() == 1 {
		return fmt.Sprintf("p%d", r.Start)
	}
	return fmt.Sprintf("p%d-%d", r.Start, r.End)
}

type SplitSpec struct {
	Name  string
	Range PageRange
}

// EmbeddedImage is one raster image on a page.
type EmbeddedImage struct {
	Xref             int
	PageIndex        int
	Width            int
	Height           int
	Kind             ImageKind
	Codec            Codec
	EffectiveDpi     sharedkernel.EffectiveDpi
	RenderedAreaSqIn float64
}

// Resample enforces hard rule #2: bitonal must not be interpolated into gray.
func (e EmbeddedImage) Resample() ResampleFilter {
	if e.Kind == Bitonal {
		return Nearest
	}
	return Lanczos
}

// DocumentCensus is the output of inspect: what's inside a PDF.
type DocumentCensus struct {
	File          sharedkernel.MediaFile
	PageCount     int
	Images        []EmbeddedImage
	NonImageBytes int64
}

func (c DocumentCensus) TotalRenderedArea() float64 {
	var total float64
	for _, img := range c.Images {
		total += img.RenderedAreaSqIn
	}
	if total == 0 {
		return 1.0
	}
	return total
}

func (c DocumentCensus) ImageBytesFraction() float64 {
	total := c.File.SizeBytes()
	if total == 0 {
		return 0
	}
	return float64(total-c.NonImageBytes) / float64(total)
}

type CompressionTarget struct {
	Budget       sharedkernel.ByteBudget
	QualityFloor sharedkernel.QualityFloor
	DpiCap       int
	DpiRange     [2]int
	QualityRange [2]int
}

func DefaultTarget(budget sharedkernel.ByteBudget) CompressionTarget {
	return CompressionTarget{
		Budget:       budget,
		QualityFloor: sharedkernel.DefaultQualityFloor(),
		DpiCap:       200,
		DpiRange:     [2]int{72, 300},
		QualityRange: [2]int{20, 95},
	}
}

type CompressionRecipe struct {
	Xref     int
	DpiTarget int
	Quality  int
	Codec    Codec
	Resample ResampleFilter
}

type CompressionResult struct {
	Output      sharedkernel.MediaFile
	Engine      string
	BeforeBytes int64
	AfterBytes  int64
	DpiUsed     int
	QualityUsed int
	Score       *sharedkernel.PerceptualScore
	ElapsedMs   int64
	Escalated   bool
}

func (r CompressionResult) Ratio() float64 {
	if r.BeforeBytes == 0 {
		return 1.0
	}
	return float64(r.AfterBytes) / float64(r.BeforeBytes)
}

func (r CompressionResult) SavedPct() float64 { return 100 * (1 - r.Ratio()) }

// --- Domain events -----------------------------------------------------------

type CompressionAttempted struct {
	File       string
	Engine     string
	AfterBytes int64
}

type BudgetMissed struct {
	File       string
	Engine     string
	AfterBytes int64
	Ceiling    int64
}

type QualityFloorViolated struct {
	File  string
	Score sharedkernel.PerceptualScore
	Floor sharedkernel.QualityFloor
}
