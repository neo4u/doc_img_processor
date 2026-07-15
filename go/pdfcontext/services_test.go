package pdfcontext

import (
	"testing"

	"pdftoolkit/sharedkernel"
)

func TestPageRangeValidation(t *testing.T) {
	if _, err := NewPageRange(0, 3); err == nil {
		t.Error("expected error for start < 1")
	}
	if _, err := NewPageRange(5, 3); err == nil {
		t.Error("expected error for end < start")
	}
	r, err := NewPageRange(3, 5)
	if err != nil {
		t.Fatal(err)
	}
	if r.Len() != 3 || r.String() != "p3-5" {
		t.Errorf("got len=%d str=%q", r.Len(), r.String())
	}
}

func TestBudgetDecomposition(t *testing.T) {
	census := DocumentCensus{
		Images: []EmbeddedImage{
			{Xref: 1, RenderedAreaSqIn: 90},
			{Xref: 2, RenderedAreaSqIn: 10},
		},
	}
	got := AllocateBudget(census, 1000)
	if got[1] != 900 || got[2] != 100 {
		t.Errorf("expected 900/100 split, got %v", got)
	}
}

func TestTargetSizeSearchPicksLargestFittingQuality(t *testing.T) {
	floor := sharedkernel.QualityFloor{Metric: sharedkernel.SSIM, Threshold: 0.0}
	s := TargetSizeSearch{Lo: 20, Hi: 95, Floor: floor}
	// size grows linearly with quality; slice fits q<=60.
	encode := func(q int) (int64, sharedkernel.PerceptualScore) {
		return int64(q * 10), sharedkernel.PerceptualScore{Metric: sharedkernel.SSIM, Value: 0.99}
	}
	q, _, found := s.BestQuality(600, encode)
	if !found || q < 55 || q > 60 {
		t.Errorf("expected q near 60, got q=%d found=%v", q, found)
	}
}

func TestTargetSizeSearchRespectsFloor(t *testing.T) {
	floor := sharedkernel.QualityFloor{Metric: sharedkernel.SSIM, Threshold: 0.95}
	s := TargetSizeSearch{Lo: 20, Hi: 95, Floor: floor}
	// Everything fits, but score is always below floor -> not found.
	encode := func(q int) (int64, sharedkernel.PerceptualScore) {
		return 1, sharedkernel.PerceptualScore{Metric: sharedkernel.SSIM, Value: 0.90}
	}
	if _, _, found := s.BestQuality(1000, encode); found {
		t.Error("expected found=false when floor never satisfied")
	}
}

func TestEffectiveDpiScaleTo(t *testing.T) {
	// 6600 px over 8.5 in ≈ 776 dpi; cap 200 -> scale ≈ 0.2577
	e := sharedkernel.EffectiveDpi{Pixels: 6600, RenderedInches: 8.5}
	if s := e.ScaleTo(200); s <= 0.25 || s >= 0.26 {
		t.Errorf("scale ≈ 0.2577 expected, got %f", s)
	}
	// Never upscale.
	if s := e.ScaleTo(2000); s != 1.0 {
		t.Errorf("expected clamp to 1.0, got %f", s)
	}
}
