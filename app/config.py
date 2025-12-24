import os

def load_config():
    """
    Loads configuration from .env file and environment variables.
    Precedence: Environment Variables > .env file
    Returns a dictionary of configuration values.
    """
    config = {}
    
    # Load from .env file if it exists
    env_path = os.path.join(os.getcwd(), '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        except Exception:
            # Silently ignore errors reading .env as it's optional
            pass

    # Override with actual environment variables
    # We only copy keys that seem relevant or copy all?
    # Requirement says "load configuration". Usually we want all current env vars 
    # visible to the app plus what was in .env.
    # To keep it safe and expected, we will just start with .env values 
    # and update with os.environ items that overlap or strictly strictly just os.environ?
    # Simple approach: Return os.environ updated with .env (but env vars take precedence)
    
    # Actually, better approach for a bootstrap:
    # 1. Start with values from .env
    # 2. Update with values from os.environ
    
    final_config = config.copy()
    final_config.update(os.environ)

    # Ensure required keys for consumers (optional for main execution to prevent crash if missing)
    # These will be accessed by consumers directly
    if 'ELEVENLABS_API_KEY' not in final_config:
        final_config['ELEVENLABS_API_KEY'] = 'ddba197d41d4cb7c28d933e795742d736d627df188094bdf5040a2f1150da9ff'
    if 'ELEVENLABS_VOICE_ID' not in final_config:
        final_config['ELEVENLABS_VOICE_ID'] = '21m00Tcm4TlvDq8ikWAM' # Default pre-made voice

    # TTS Settings
    if 'TTS_BACKEND' not in final_config:
        final_config['TTS_BACKEND'] = 'system'
    
    # Piper defaults (assumes user followed setup or valid paths)
    if 'PIPER_BINARY_PATH' not in final_config:
        final_config['PIPER_BINARY_PATH'] = 'piper' # Assume in PATH by default
        
    if 'PIPER_MODEL_PATH' not in final_config:
        # relative to project root
        final_config['PIPER_MODEL_PATH'] = os.path.join(os.getcwd(), 'app', 'storage', 'models', 'en_US-lessac-high.onnx')

    return final_config
