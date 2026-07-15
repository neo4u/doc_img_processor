package pdfcontext

import "pdftoolkit/sharedkernel"

// Domain services — pure orchestration, no library imports. Mirrors
// python/pdf_toolkit/pdf_context/services.py.

// EncodeFn maps an encoder quality to (byte size, perceptual score). Size must be
// monotonic non-decreasing in quality (true for JPEG/WebP).
type EncodeFn func(quality int) (int64, sharedkernel.PerceptualScore)

// TargetSizeSearch finds the largest encoder quality whose output fits sliceBytes
// while clearing the QualityFloor. ~7 probes for a 20..95 range.
type TargetSizeSearch struct {
	Lo, Hi int
	Floor  sharedkernel.QualityFloor
}

// BestQuality returns (quality, score, found). found=false means no quality both
// fit the slice and cleared the floor.
func (s TargetSizeSearch) BestQuality(sliceBytes int64, encode EncodeFn) (int, sharedkernel.PerceptualScore, bool) {
	lo, hi := s.Lo, s.Hi
	var bestQ int
	var bestScore sharedkernel.PerceptualScore
	found := false
	for hi-lo > 1 {
		q := (lo + hi) / 2
		size, score := encode(q)
		if size <= sliceBytes {
			if s.Floor.Accepts(score) {
				bestQ, bestScore, found = q, score, true
			}
			lo = q // try higher quality
		} else {
			hi = q // too big, lower quality
		}
	}
	return bestQ, bestScore, found
}

// AllocateBudget splits an image byte budget across images ∝ rendered area.
func AllocateBudget(census DocumentCensus, imageBudget int64) map[int]int64 {
	total := census.TotalRenderedArea()
	out := make(map[int]int64, len(census.Images))
	for _, img := range census.Images {
		v := int64(float64(imageBudget) * img.RenderedAreaSqIn / total)
		if v < 1 {
			v = 1
		}
		out[img.Xref] = v
	}
	return out
}
