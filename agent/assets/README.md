# Assets Directory

This directory contains application assets like icons and images.

## Required Files

### Application Icons
- `icon.png` - Linux icon (512x512 recommended)
- `icon.ico` - Windows icon (256x256 recommended)
- `icon.icns` - macOS icon (512x512 recommended)

### UI Assets
- `netpilot-logo.png` - NetPilot logo for the header

## Icon Requirements

### For Distribution Builds
The application icons should be:
- **PNG**: 512x512 pixels for Linux AppImage
- **ICO**: Multi-size Windows icon (16, 32, 48, 64, 128, 256 pixels)
- **ICNS**: macOS icon bundle (16-1024 pixels)

### Creating Icons
You can create these from a single high-resolution PNG using tools like:
- `electron-icon-builder`
- `icon-gen`
- Online converters

### Temporary Solution
For development, you can use any PNG file as a temporary icon. The app will work without icons but won't look professional.

## Logo Assets
- Place the NetPilot logo as `netpilot-logo.png` (recommended: 128x128 or higher)
- If logo is not available, the app will hide the logo image gracefully 