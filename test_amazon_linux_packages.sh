#!/bin/bash
#
# Test Amazon Linux 3 Package Availability
# This script checks which packages are available before installation
#

echo "🔍 Testing Amazon Linux 3 Package Availability"
echo "=============================================="

# List of packages to test
packages=(
    "wget"
    "unzip" 
    "curl"
    "xorg-x11-server-Xvfb"
    "gtk3-devel"
    "nss-devel"
    "xorg-x11-xauth"
    "dbus-glib-devel"
    "dbus-glib"
    "alsa-lib"
    "libXtst"
    "libXrandr"
    "libXScrnSaver"
    "libXcomposite"
    "libXcursor"
    "libXdamage"
    "libXext"
    "libXfixes"
    "libXi"
    "libXrender"
    "liberation-fonts"
    "liberation-fonts-common"
    "xdg-utils"
    "at-spi2-atk"
    "at-spi2-core"
    "cups-libs"
    "gtk3"
    "libdrm"
    "libxkbcommon"
    "libxshmfence"
    "mesa-libgbm"
    "vulkan-loader"
)

echo "Testing package availability..."
echo ""

available_packages=()
missing_packages=()

for package in "${packages[@]}"; do
    if dnf list available "$package" &>/dev/null || dnf list installed "$package" &>/dev/null; then
        echo "✅ $package - Available"
        available_packages+=("$package")
    else
        echo "❌ $package - Not found"
        missing_packages+=("$package")
    fi
done

echo ""
echo "📊 Summary:"
echo "✅ Available: ${#available_packages[@]} packages"
echo "❌ Missing: ${#missing_packages[@]} packages"

if [ ${#missing_packages[@]} -gt 0 ]; then
    echo ""
    echo "❌ Missing packages:"
    for pkg in "${missing_packages[@]}"; do
        echo "   - $pkg"
    done
    
    echo ""
    echo "🔍 Searching for alternatives..."
    for pkg in "${missing_packages[@]}"; do
        echo "Searching for: $pkg"
        dnf search "$pkg" 2>/dev/null | head -5
        echo ""
    done
fi

echo ""
echo "💡 To install available packages:"
echo "sudo dnf install -y \\"
for pkg in "${available_packages[@]}"; do
    echo "    $pkg \\"
done | sed '$ s/ \\$//'

echo ""
echo "🎯 Test complete!"
