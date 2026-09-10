from pathlib import Path

from PIL import Image, ImageFilter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT_ROOT / 'scripts' / 'source' / 'profile_image.png'
OUTPUT = PROJECT_ROOT / 'frontend' / 'public' / 'profile-frames'

STYLE_ROWS = {
    'ember': 160,
    'moon': 344,
    'speed': 526,
    'wave': 710,
    'nature': 894,
}
STAGE_COLUMNS = [197, 382, 570, 758, 960, 1184, 1388]
CROP_SIZE = 200


def background_alpha(pixel):
    red, green, blue = pixel
    channel_gap = max(pixel) - min(pixel)
    brightness = (red + green + blue) / 3

    # The source's checkerboard is neutral gray. Colored and luminous frame
    # pixels retain alpha, while the baked checkerboard becomes transparent.
    if channel_gap <= 5 and 232 <= brightness <= 255:
        return 0
    if channel_gap <= 10 and 238 <= brightness <= 255:
        return 35
    return min(255, max(0, channel_gap * 10))


def extract_frame(source, center_x, center_y):
    half = CROP_SIZE // 2
    crop = source.crop(
        (center_x - half, center_y - half, center_x + half, center_y + half)
    ).convert('RGB')
    alpha = Image.new('L', crop.size)
    alpha.putdata([background_alpha(pixel) for pixel in crop.getdata()])
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.35))
    crop.putalpha(alpha)
    return crop


def main():
    source = Image.open(SOURCE).convert('RGB')
    OUTPUT.mkdir(parents=True, exist_ok=True)

    for style, center_y in STYLE_ROWS.items():
        style_dir = OUTPUT / style
        style_dir.mkdir(parents=True, exist_ok=True)
        for stage, center_x in enumerate(STAGE_COLUMNS):
            frame = extract_frame(source, center_x, center_y)
            frame.save(style_dir / f'stage-{stage}.png', optimize=True)

    print(f'Created {len(STYLE_ROWS) * len(STAGE_COLUMNS)} profile frames in {OUTPUT}')


if __name__ == '__main__':
    main()
