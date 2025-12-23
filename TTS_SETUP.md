# Offline TTS Setup (Piper)

This system uses **Piper**, a fast, local neural TTS engine, to generate audio without API costs.

## Prerequisites

- **Mac/Linux**: You need a terminal.
- **Python 3.10+**: (Already assumed).

## 1. Install Piper

You have two options:
1. **Python Wrapper (Recommended)**: `pip install piper-tts`
2. **Standard Binary**: Download from [Piper GitHub Releases](https://github.com/rhasspy/piper/releases).

For this integration, we assume you are using the **binary** approach for maximum performance and isolation, OR the python package if available. 

### Method A: Manual Binary (Robust)
1. Download the latest release for your OS (e.g., `piper_macos_aarch64.tar.gz` for Apple Silicon).
2. Extract it to a known location, e.g., `/Users/varun/piper/`.
3. The executable is at `/Users/varun/piper/piper`.

### Method B: Python Package (Easier)
```bash
pip install piper-tts
```
*Note: The python package might be slower or have dependency conflicts.*

## 2. Download a Voice Model

Piper needs a `.onnx` model file and a `.json` config file.
We modify the tone by choosing the model. "Lessac" (en_US) is a good high-quality default.

1. Go to [HuggingFace - Rhasspy Piper Voices](https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/lessac/high).
2. Download:
   - `en_US-lessac-high.onnx`
   - `en_US-lessac-high.onnx.json`
3. Save them to: `app/storage/models/`
   - Create the directory: `mkdir -p app/storage/models`

## 3. Configure the System

Update your `.env` or check `app/config.py` defaults.

**Env Variables:**
```bash
export TTS_BACKEND="piper"
export PIPER_BINARY_PATH="/path/to/piper" # e.g., /Users/varun/piper/piper
export PIPER_MODEL_PATH="app/storage/models/en_US-lessac-high.onnx"
```

## 4. Run the Factory
```bash
python3 run_factory.py --limit 1
```

## Troubleshooting
- **Permission Denied**: `chmod +x /path/to/piper`
- **File Not Found**: Ensure you used absolute paths or correct relative paths.
