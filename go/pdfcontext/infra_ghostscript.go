package pdfcontext

import (
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"time"

	"pdftoolkit/sharedkernel"
)

// GhostscriptCompressor is the escalation/baseline engine: binary-searches
// -dColorImageResolution to sit just under the byte budget. Mirrors the Python
// adapter. External `gs` dependency confined here.
type GhostscriptCompressor struct {
	Bin        string
	Iterations int
}

func NewGhostscriptCompressor() GhostscriptCompressor {
	return GhostscriptCompressor{Bin: "gs", Iterations: 8}
}

func (g GhostscriptCompressor) Name() string { return "ghostscript" }

func (g GhostscriptCompressor) run(src, dst string, dpi int) (int64, error) {
	d := strconv.Itoa(dpi)
	args := []string{
		"-sDEVICE=pdfwrite", "-dNOPAUSE", "-dQUIET", "-dBATCH", "-dPDFSETTINGS=/default",
		"-dColorImageResolution=" + d, "-dGrayImageResolution=" + d, "-dMonoImageResolution=" + d,
		"-dDownsampleColorImages=true", "-dDownsampleGrayImages=true",
		"-sOutputFile=" + dst, src,
	}
	if err := exec.Command(g.Bin, args...).Run(); err != nil {
		return 0, err
	}
	fi, err := os.Stat(dst)
	if err != nil {
		return 0, err
	}
	return fi.Size(), nil
}

func (g GhostscriptCompressor) Compress(src sharedkernel.MediaFile, t CompressionTarget, out string) (CompressionResult, error) {
	start := time.Now()
	ceiling := t.Budget.Ceiling()
	srcSize := src.SizeBytes()

	res := func(dpi int) CompressionResult {
		var after int64
		if fi, err := os.Stat(out); err == nil {
			after = fi.Size()
		}
		return CompressionResult{
			Output: sharedkernel.MediaFile{Path: out}, Engine: g.Name(),
			BeforeBytes: srcSize, AfterBytes: after, DpiUsed: dpi,
			ElapsedMs: time.Since(start).Milliseconds(),
		}
	}

	if srcSize <= ceiling { // already fits
		if err := copyFile(src.Path, out); err != nil {
			return CompressionResult{}, err
		}
		return res(0), nil
	}

	lo, hi := t.DpiRange[0], t.DpiRange[1]
	best := lo
	tmp := filepath.Join(os.TempDir(), "pdftoolkit_gsprobe.pdf")
	for i := 0; i < g.Iterations; i++ {
		mid := (lo + hi) / 2
		size, err := g.run(src.Path, tmp, mid)
		if err != nil {
			return CompressionResult{}, err
		}
		if size <= ceiling {
			best = mid
			lo = mid
		} else {
			hi = mid
		}
	}
	_ = os.Remove(tmp)
	if _, err := g.run(src.Path, out, best); err != nil {
		return CompressionResult{}, err
	}
	// Hard rule #1: never emit larger than input.
	if fi, err := os.Stat(out); err == nil && fi.Size() >= srcSize {
		if err := copyFile(src.Path, out); err != nil {
			return CompressionResult{}, err
		}
		best = 0
	}
	return res(best), nil
}

func copyFile(src, dst string) error {
	b, err := os.ReadFile(src)
	if err != nil {
		return err
	}
	return os.WriteFile(dst, b, 0o644)
}
