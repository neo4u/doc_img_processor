"""SheetLayoutService — pure math, exhaustively tested (LLD §9)."""

from __future__ import annotations

import pytest

from pdf_toolkit.photo_context.domain import SHEETS, LayoutError, SheetSpec
from pdf_toolkit.photo_context.services import SheetLayoutService


def test_2x2_on_4x6_is_exactly_6_up_zero_gutter():
    layout = SheetLayoutService.layout(2.0, 2.0, SHEETS["4x6"])
    assert (layout.cols, layout.rows) == (2, 3)
    assert layout.count == 6
    assert layout.cell_w == layout.cell_h == 600
    assert layout.x_offsets == [0, 600]
    assert layout.y_offsets == [0, 600, 1200]


def test_2x2_on_6x4_landscape_is_3_by_2():
    layout = SheetLayoutService.layout(2.0, 2.0, SHEETS["6x4"])
    assert (layout.cols, layout.rows) == (3, 2)
    assert layout.count == 6


def test_gutters_are_uniform_and_grid_is_centered():
    # 1.5" photos on 4x6: 450 px cells → 2 cols (300 px leftover), 4 rows (0 leftover)
    layout = SheetLayoutService.layout(1.5, 1.5, SHEETS["4x6"])
    assert (layout.cols, layout.rows) == (2, 4)
    # leftover 300 px over 3 gaps = 100 px gutters; first cell starts at 100
    assert layout.x_offsets == [100, 650]


def test_margin_shrinks_usable_area():
    # 0.25" margin each side on 4x6 leaves 3.5" width → one 2" column only
    layout = SheetLayoutService.layout(2.0, 2.0, SHEETS["4x6"], margin_in=0.25)
    assert layout.cols == 1


def test_photo_larger_than_sheet_raises():
    with pytest.raises(LayoutError):
        SheetLayoutService.layout(5.0, 5.0, SHEETS["4x6"])


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        SheetLayoutService.layout(0, 2.0, SHEETS["4x6"])
    with pytest.raises(ValueError):
        SheetLayoutService.layout(2.0, 2.0, SHEETS["4x6"], margin_in=-1)
    with pytest.raises(ValueError):
        SheetSpec(name="bad", width_in=0, height_in=6)


if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main([__file__, "-q"]))
