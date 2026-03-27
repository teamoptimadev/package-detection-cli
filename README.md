# 🛡️ Package Detector (PD) - Universal Security CLI

Package Detector acts as a security gatekeeper for developers, wrapping `npm` and `pip` installation commands to analyze packages for malicious behavior **before** they are installed locally.

## ✨ Features
-   **Multi-Registry Support:** Automatically handles NPM and PyPI ecosystems.
-   **Security Analysis:** Uses AST parsing and RAG-based threat modeling to detect risky patterns.
-   **Interactive Prompts:** Blocks high-risk packages and asks for user confirmation.
-   **Premium CLI UX:** Uses `rich` for beautiful reports and `questionary` for smooth interactions.

## 🚀 Installation

The recommended way to install Package Detector is using the provided installation script, which sets up an isolated virtual environment.

```bash
# Clone the repository (if not already there)
# cd package-detection-cli

# Run the installer
bash scripts/install.sh
```

**Post-installation:**
If `~/.local/bin` is not in your PATH, add it to your profile (`~/.zshrc` or `~/.bashrc`):
```bash
export PATH="$PATH:$HOME/.local/bin"
```

## 🛠️ Usage

### Basic Installation (Safe)
Intercept any installation command:
```bash
pd install react
# or
pd i numpy
```

### Explicit Registry
Force a specific registry if heuristic detection fails:
```bash
pd install --npm some-package
pd install --pip some-python-package
```

### Full Proxy Commands
Use `pd` as a prefix for standard installers:
```bash
pd npm install lodash
pd pip install flask
```

### Scanning (No Install)
Analyze a package without triggering the installer:
```bash
pd scan --registry npm cross-env
```

## ⚙️ How it Works
1.  **Command Intercept:** `pd` captures the package name and intent.
2.  **Download & Extract:** Downloads the package metadata and source code to a temporary sandbox.
3.  **Behavior Extraction:** Performs AST analysis to extract sensitive function calls and system interactions.
4.  **RAG Match:** Compares extracted behaviors against a vector database of known malicious patterns.
5.  **AI Reasoning:** A reasoning module summarizes the risk and provides a verdict (`SAFE`, `SUSPICIOUS`, `MALICIOUS`).
6.  **Gatekeeping:** If the verdict is risky, it prompts the user. If verified safe, it executes the system's actual `npm`/`pip` binary.

---
Built by Package Detector Team. Stay Safe! 🛡️
