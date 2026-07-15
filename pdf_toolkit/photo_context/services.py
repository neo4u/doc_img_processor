"""photo context — domain services. Pure tiling math, no library imports."""

from __future__ import annotations

from pdf_toolkit.photo_context.domain import LayoutError, SheetLayout, SheetSpec


class SheetLayoutService:
    """Tile identical photos onto a sheet; leftover space becomes uniform gutters.

    Gutters double as cut lanes. The canonical case — 2×2 in photos on a
    4×6 in sheet @300 DPI — yields exactly 2 cols × 3 rows with zero gutter,
    matching commercial passport-photo strips.
    """

    @staticmethod
    def layout(
        photo_w_in: float,
        photo_h_in: float,
        sheet: SheetSpec,
        margin_in: float = 0.0,
    ) -> SheetLayout:
        if photo_w_in <= 0 or photo_h_in <= 0:
            raise ValueError("photo print size must be positive")
        if margin_in < 0:
            raise ValueError("margin must be >= 0")

        cell_w = round(photo_w_in * sheet.dpi)
        cell_h = round(photo_h_in * sheet.dpi)
        usable_w = sheet.width_px - 2 * round(margin_in * sheet.dpi)
        usable_h = sheet.height_px - 2 * round(margin_in * sheet.dpi)

        cols = usable_w // cell_w
        rows = usable_h // cell_h
        if cols < 1 or rows < 1:
            raise LayoutError(
                f"a {photo_w_in}×{photo_h_in} in photo does not fit on a "
                f"{sheet.width_in}×{sheet.height_in} in sheet with {margin_in} in margin"
            )

        # Distribute leftover space as uniform gutters around/between cells,
        # which centers the grid: n cells → n+1 gaps.
        def offsets(n_cells: int, cell: int, total: int) -> list[int]:
            leftover = total - n_cells * cell
            gap = leftover // (n_cells + 1)
            start = (total - (n_cells * cell + (n_cells - 1) * gap)) // 2
            return [start + i * (cell + gap) for i in range(n_cells)]

        margin_px = round(margin_in * sheet.dpi)
        xs = [margin_px + x for x in offsets(int(cols), cell_w, usable_w)]
        ys = [margin_px + y for y in offsets(int(rows), cell_h, usable_h)]

        return SheetLayout(
            sheet=sheet,
            cols=int(cols),
            rows=int(rows),
            cell_w=cell_w,
            cell_h=cell_h,
            x_offsets=xs,
            y_offsets=ys,
        )
