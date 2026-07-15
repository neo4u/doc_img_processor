// Command pdftoolkit is the Go CLI mirror: inspect | compress | benchmark.
// Currently wired to the Ghostscript engine (working); the pdfcpu native engine
// is stubbed. Mirrors python/pdf_toolkit/cli/main.py.
package main

import (
	"fmt"
	"os"
	"strconv"

	"pdftoolkit/pdfcontext"
	"pdftoolkit/sharedkernel"
)

func usage() {
	fmt.Println(`pdftoolkit (go) — mirror of the Python reference

usage:
  pdftoolkit compress <in.pdf> <out.pdf> [targetKB]   compress via Ghostscript engine

engines: ghostscript (working), pdfcpu+xdraw (stubbed — see DOMAIN.md)`)
}

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(1)
	}
	switch os.Args[1] {
	case "compress":
		if len(os.Args) < 4 {
			usage()
			os.Exit(1)
		}
		kb := int64(1000)
		if len(os.Args) > 4 {
			if v, err := strconv.ParseInt(os.Args[4], 10, 64); err == nil {
				kb = v
			}
		}
		budget, err := sharedkernel.ByteBudgetKB(kb, 0)
		if err != nil {
			fail(err)
		}
		src := sharedkernel.MediaFile{Path: os.Args[2]}
		if !src.Exists() {
			fail(fmt.Errorf("no such file: %s", src.Path))
		}
		engine := pdfcontext.NewGhostscriptCompressor()
		res, err := engine.Compress(src, pdfcontext.DefaultTarget(budget), os.Args[3])
		if err != nil {
			fail(err)
		}
		fmt.Printf("%s: %dKB -> %dKB (%.0f%% off) dpi=%d %dms\n",
			res.Engine, res.BeforeBytes/1000, res.AfterBytes/1000, res.SavedPct(),
			res.DpiUsed, res.ElapsedMs)
	default:
		usage()
		os.Exit(1)
	}
}

func fail(err error) {
	fmt.Fprintln(os.Stderr, "error:", err)
	os.Exit(1)
}
