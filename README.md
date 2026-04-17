# Universal Dev Environment Manager

A professional, cross-platform desktop application that lets developers **search, select, and install** programming languages, compilers, SDKs, and developer tools from a comprehensive catalog — all from a single, beautiful GUI.

---

## ✨ Features

| Feature | Details |
|---|---|
| **50+ Tools** | Languages, compilers, SDKs, frameworks, AI/ML, mobile & web dev |
| **Instant Search** | Type to filter the tool list in real time |
| **Category Filter** | Dropdown to filter by Languages, Compilers, SDKs, Frameworks, etc. |
| **Smart Install** | Install button stays disabled until ≥1 item is selected |
| **Cross-Platform** | Windows (winget), Linux (apt), macOS (Homebrew) |
| **Auto Detection** | Skips tools that are already installed |
| **PATH Management** | Automatically configures environment variables |
| **Live Progress** | Progress bar, status label, and colour-coded log console |
| **Thread-Safe** | Installations run in background threads — GUI never freezes |
| **Configurable** | All tools loaded dynamically from `tools.json` |

---

## 🛠️ Supported Tool Categories

| Category | Examples |
|---|---|
| **Languages** | Python, Java, Go, Rust, Kotlin, Swift, PHP, Ruby, C#, Dart, Scala, Haskell, Perl, Lua, Julia, Zig, Nim, Elixir, OCaml, Groovy, V, Crystal, COBOL |
| **Compilers** | GCC, G++, Clang, MinGW, MSYS2, NASM, Fortran, Cargo, npm, pip |
| **SDKs** | .NET SDK, Git, VS Code, CMake, Docker, kubectl, Terraform, AWS CLI, Google Cloud SDK |
| **Frameworks** | Yarn, Deno, Bun, TypeScript |
| **AI / Data Science** | TensorFlow, PyTorch, CUDA Toolkit, R, Julia, MATLAB Runtime |
| **Mobile Development** | Android SDK, Flutter, React Native CLI |
| **Web Development** | Solidity |

---

## 📁 Project Structure

```
UniversalDevManager/
├── main.py            # Entry point
├── gui.py             # Tkinter GUI (dark theme, search, categories)
├── installer.py       # Installation engine
├── utils.py           # OS detection, PATH, logging, helpers
├── tools.json         # Tool catalog (50+ entries)
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Windows**: `winget` (ships with Windows 10 / 11)
- **Linux**: `apt` (Debian / Ubuntu)
- **macOS**: `brew` (Homebrew) — auto-installed if missing

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Application

```bash
python main.py
```

For admin / elevated mode (recommended on Windows):

```bash
python main.py --elevate
```

---

## 🖥️ GUI Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ⚡ Universal Dev Environment Manager               Windows • Admin    │
├──────────────────────────────────────────────────────────────────────────┤
│  🔍 Search…                                 Category: [All         ▾]  │
│                                                          3 selected    │
├──────────────────────────────────────────────────────────────────────────┤
│  ☐  Python            General-purpose programming language   Languages │
│  ☐  GCC               GNU C compiler                        Compilers │
│  ☐  Java (OpenJDK)    JDK for Java development               Languages│
│  ☐  Node.js           JavaScript runtime built on V8         Languages │
│  ☐  Rust              Systems programming language           Languages │
│  ☐  Go                Compiled language by Google             Languages│
│  …  (scrollable)                                                       │
├──────────────────────────────────────────────────────────────────────────┤
│  [⚡ Install Selected]  [☑ Select All]  [☐ Clear]  [↻ Refresh]  [✕]   │
├──────────────────────────────────────────────────────────────────────────┤
│  Node.js · Installing…              ▓▓▓▓▓▓▓▓░░░░░░░░░░░  45%         │
├──────────────────────────────────────────────────────────────────────────┤
│  > ── Python (1/3) ──                                                  │
│  > ✓ Python is already installed. Skipping.                            │
│  > ── Node.js (2/3) ──                                                 │
│  > Installing Node.js…                                                 │
│  > Running: winget install --id OpenJS.NodeJS.LTS …                    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuration

Edit `tools.json` to add, remove, or modify tools. Each entry:

```json
{
  "key": "python",
  "name": "Python",
  "description": "General-purpose programming language",
  "category": "Languages",
  "detect_cmd": "python --version",
  "detect_cmd_alt": "python3 --version",
  "install_command_windows": "winget install --id Python.Python.3.12 ...",
  "install_command_linux": "sudo apt-get install -y python3",
  "install_command_mac": "brew install python",
  "path_dirs_windows": ["%LOCALAPPDATA%\\Programs\\Python\\Python312"],
  "path_required": true
}
```

### Adding a New Tool

1. Add a new JSON object to `tools.json`
2. Click **↻ Refresh** in the GUI (or restart)
3. The tool appears in the list instantly

---

## 📦 Building an Executable

### Windows

```bash
pyinstaller --onefile --windowed --name UniversalDevManager main.py
```

### macOS / Linux

```bash
pyinstaller --onefile --name UniversalDevManager main.py
```

Output appears in the `dist/` folder.

---

## 📝 Logging

All activity is recorded to **`installer.log`**:

- Application start
- Tool detection results
- Installation commands and output
- PATH modifications
- Errors and warnings

---

## 🔒 Security

- Tools are **never reinstalled** if already detected
- All downloads use official package managers (winget, apt, brew)
- No third-party download servers
- PATH changes use the Windows Registry API (not truncation-prone `setx`)

---

## 📄 License

Provided as-is for educational and professional use. Free to modify and distribute.
