from __future__ import annotations

from pathlib import Path
import struct
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRAND_DIR = (
    PROJECT_ROOT / "custom_components" / "crypto_portfolio" / "brand"
)


def png_dimensions(path: Path) -> tuple[int, int]:
    """Return dimensions from a PNG IHDR chunk."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError(f"{path} is not a valid PNG")
    return struct.unpack(">II", data[16:24])


class BrandAssetsTest(unittest.TestCase):
    def test_icon_dimensions(self) -> None:
        self.assertEqual(png_dimensions(BRAND_DIR / "icon.png"), (256, 256))
        self.assertEqual(png_dimensions(BRAND_DIR / "icon@2x.png"), (512, 512))


if __name__ == "__main__":
    unittest.main()
