package imagecontext

import (
	"fmt"

	"pdftoolkit/sharedkernel"
)

// Planned adapters (mirror the Python Pillow + numpy-SSIM adapters):
//   - golang.org/x/image/draw     — CatmullRom resize (Lanczos-equivalent)
//   - image/jpeg, image/png       — encode (stdlib)
//   - a numpy-free box-window SSIM — QualityMeter
// Stubs keep `go build` dependency-free until the adapters land.
// TODO(port): implement XDrawCodec.Resize with draw.CatmullRom.Scale.

var errNotImplemented = fmt.Errorf("not implemented: pending x/image adapter (see DOMAIN.md)")

type XDrawCodec struct{}

func (XDrawCodec) Decode([]byte) (any, error)                  { return nil, errNotImplemented }
func (XDrawCodec) Resize(any, int, int, string) (any, error)   { return nil, errNotImplemented }
func (XDrawCodec) Encode(any, ImageFormat, int) ([]byte, error) { return nil, errNotImplemented }

type BoxSsimMeter struct{}

func (BoxSsimMeter) Score([]byte, []byte) (sharedkernel.PerceptualScore, error) {
	return sharedkernel.PerceptualScore{}, errNotImplemented
}
