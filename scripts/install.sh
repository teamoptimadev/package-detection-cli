#!/bin/bash
set -e

# Package Guard (PG) Installer - Clean Version
# -------------------------------------------
# Installs Package Guard into a dedicated ~/.package-guard directory.

INSTALL_DIR="$HOME/.package-detector"
VENV_DIR="$INSTALL_DIR/venv"
SRC_DIR="$INSTALL_DIR/src"
USER_BIN_DIR="$HOME/.local/bin" # Standard location for user-specific binaries

clear
echo "🛡️ Installing Package Detector (PD) Universal CLI..."

# 1. Setup structure
mkdir -p "$SRC_DIR"
mkdir -p "$USER_BIN_DIR"

# 2. Check for python3
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: python3 is not installed. Please install it to use Package Guard."
    exit 1
fi

# 3. Copy source files (excluding .git and venv)
echo "📂 Copying source files to $SRC_DIR..."
rsync -av --progress ./ "$SRC_DIR/" --exclude ".git" --exclude "venv" --exclude ".venv" --exclude "__pycache__"

# 4. Create internal venv
echo "🔧 Setting up virtual environment..."
python3 -m venv "$VENV_DIR"

# 5. Install dependencies
echo "📦 Installing dependencies (including ML models, this may take a few minutes)..."
"$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel
"$VENV_DIR/bin/pip" install -r "$SRC_DIR/requirements.txt"
# These are the CLI specific ones I added manually to pyproject.toml
"$VENV_DIR/bin/pip" install typer questionary 
# Install the project itself in editable mode inside the venv
"$VENV_DIR/bin/pip" install -e "$SRC_DIR"

# 6. Create binary wrapper script in user's path
echo "🛠️ Creating command wrapper..."
cat <<EOF > "$USER_BIN_DIR/pd"
#!/bin/bash
# Automatically use the internal venv
PYTHONPATH="$SRC_DIR:\$PYTHONPATH" "$VENV_DIR/bin/python3" "$SRC_DIR/pg/guard.py" "\$@"
EOF

chmod +x "$USER_BIN_DIR/pd"

# 7. Check if USER_BIN_DIR is in PATH
SYSPATH_HINT=""
if [[ ":$PATH:" != *":$USER_BIN_DIR:"* ]]; then
    SYSPATH_HINT="   Add this to your ~/.zshrc or ~/.bashrc to run 'pg' from anywhere:\n   export PATH=\"\$PATH:$USER_BIN_DIR\""
fi

echo "================================================================"
echo "██████╗  █████╗  ██████╗██╗  ██╗ █████╗  ██████╗ ███████╗"
echo "██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██╔══██╗██╔════╝ ██╔════╝"
echo "██████╔╝███████║██║     █████╔╝ ███████║██║  ███╗█████╗  "
echo "██╔═══╝ ██╔══██║██║     ██╔═██╗ ██╔══██║██║   ██║██╔══╝  "
echo "██║     ██║  ██║╚██████╗██║  ██╗██║  ██║╚██████╔╝███████╗"
echo "╚═╝     ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝"

echo "██████╗ ███████╗████████╗███████╗ ██████╗████████╗ ██████╗ ██████╗ "
echo "██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗"
echo "██║  ██║█████╗     ██║   █████╗  ██║        ██║   ██║   ██║██████╔╝"
echo "██║  ██║██╔══╝     ██║   ██╔══╝  ██║        ██║   ██║   ██║██╔══██╗"
echo "██████╔╝███████╗   ██║   ███████╗╚██████╗   ██║   ╚██████╔╝██║  ██║"
echo "╚═════╝ ╚══════╝   ╚═╝   ╚══════╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝"
echo "Package Detector (PD) installed successfully!"
echo "📍 Source Code:   $SRC_DIR"
echo "📍 Virtual Env:   $VENV_DIR"
echo "📍 Binary Alias:  $USER_BIN_DIR/pd"
if [ -n "$SYSPATH_HINT" ]; then
    echo -e "$SYSPATH_HINT"
fi
echo "================================================================"
echo "🚀 Try running: pd --help"
echo "================================================================"
