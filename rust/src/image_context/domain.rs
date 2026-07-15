//! image context — domain layer. Mirrors python/pdf_toolkit/image_context.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ImageFormat {
    Jpeg,
    Png,
    WebP,
    Avif,
}
