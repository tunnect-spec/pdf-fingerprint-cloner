"""
Generates a modern application icon (PDF badge with fingerprint shield)
and saves as icon.ico (multi-resolution for Windows) and icon.png.
"""

from PIL import Image, ImageDraw

def create_app_icon():
    sizes = [256, 128, 64, 48, 32, 16]
    images = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Scale factor
        s = size / 256.0

        # Background rounded rectangle (Dark Navy/Slate)
        margin = int(12 * s)
        draw.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=int(40 * s),
            fill=(30, 30, 46, 255),
            outline=(137, 180, 250, 255),
            width=max(1, int(4 * s))
        )

        # Central Shield / Document shape (Blue)
        doc_x1, doc_y1 = int(58 * s), int(48 * s)
        doc_x2, doc_y2 = int(198 * s), int(208 * s)
        draw.rounded_rectangle(
            [doc_x1, doc_y1, doc_x2, doc_y2],
            radius=int(18 * s),
            fill=(49, 50, 68, 255),
            outline=(180, 190, 254, 255),
            width=max(1, int(3 * s))
        )

        # Decorative fingerprint/lines inside doc
        line_color = (166, 227, 161, 255) # Mint green
        for y_offset in [85, 115, 145, 175]:
            y = int(y_offset * s)
            draw.line(
                [(int(85 * s), y), (int(170 * s), y)],
                fill=line_color,
                width=max(1, int(4 * s))
            )

        # "PDF" badge at top right
        badge_x1, badge_y1 = int(140 * s), int(35 * s)
        badge_x2, badge_y2 = int(220 * s), int(75 * s)
        draw.rounded_rectangle(
            [badge_x1, badge_y1, badge_x2, badge_y2],
            radius=int(10 * s),
            fill=(243, 139, 168, 255), # Red/Coral
        )

        images.append(img)

    # Save 256px as PNG
    images[0].save("icon.png", format="PNG")

    # Save as Windows ICO (contains 16, 32, 48, 64, 128, 256)
    images[0].save("icon.ico", format="ICO", sizes=[(s, s) for s in sizes])
    print("Icons created: icon.png and icon.ico")

if __name__ == "__main__":
    create_app_icon()
