// Package sharedkernel holds value objects used by both the pdf and image contexts.
// Mirrors python/pdf_toolkit/shared_kernel and rust/src/shared_kernel. See ../../DOMAIN.md.
package sharedkernel

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
)

type Metric string

const (
	SSIM        Metric = "ssim"
	DSSIM       Metric = "dssim"
	Butteraugli Metric = "butteraugli"
)

// HigherIsBetter reports whether a larger value means better quality.
func (m Metric) HigherIsBetter() bool { return m == SSIM }

// MediaFile is a file on disk; identity is its content hash.
type MediaFile struct{ Path string }

func (f MediaFile) Exists() bool {
	_, err := os.Stat(f.Path)
	return err == nil
}

func (f MediaFile) SizeBytes() int64 {
	fi, err := os.Stat(f.Path)
	if err != nil {
		return 0
	}
	return fi.Size()
}

func (f MediaFile) ContentHash() (string, error) {
	b, err := os.ReadFile(f.Path)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(b)
	return hex.EncodeToString(sum[:]), nil
}

// ByteBudget is a target size with an optional over-tolerance fraction.
type ByteBudget struct {
	TargetBytes   int64
	OverTolerance float64
}

func NewByteBudget(target int64, tol float64) (ByteBudget, error) {
	if target <= 0 {
		return ByteBudget{}, fmt.Errorf("target_bytes must be positive")
	}
	if tol < 0 {
		return ByteBudget{}, fmt.Errorf("over_tolerance must be >= 0")
	}
	return ByteBudget{target, tol}, nil
}

func ByteBudgetKB(kb int64, tol float64) (ByteBudget, error) { return NewByteBudget(kb*1000, tol) }

func (b ByteBudget) Ceiling() int64  { return int64(float64(b.TargetBytes) * (1 + b.OverTolerance)) }
func (b ByteBudget) Contains(n int64) bool { return n <= b.Ceiling() }

type PerceptualScore struct {
	Metric Metric
	Value  float64
}

func (s PerceptualScore) IsAtLeast(threshold float64) bool {
	if s.Metric.HigherIsBetter() {
		return s.Value >= threshold
	}
	return s.Value <= threshold
}

// QualityFloor is a perceptual acceptance threshold enforced as a domain invariant.
type QualityFloor struct {
	Metric    Metric
	Threshold float64
}

func DefaultQualityFloor() QualityFloor { return QualityFloor{SSIM, 0.90} }

func (q QualityFloor) Accepts(s PerceptualScore) bool { return s.IsAtLeast(q.Threshold) }

// EffectiveDpi is resolution as rendered on the page — from geometry, never metadata.
type EffectiveDpi struct {
	Pixels         int
	RenderedInches float64
}

func (e EffectiveDpi) Value() float64 {
	if e.RenderedInches <= 0 {
		return 0
	}
	return float64(e.Pixels) / e.RenderedInches
}

// ScaleTo returns the (<=1.0) factor to reach targetDpi.
func (e EffectiveDpi) ScaleTo(targetDpi float64) float64 {
	v := e.Value()
	if v <= 0 {
		return 1.0
	}
	if s := targetDpi / v; s < 1.0 {
		return s
	}
	return 1.0
}
