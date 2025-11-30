import os
import json
import time
import random
import google.generativeai as genai
from google.api_core import exceptions
from dotenv import load_dotenv

load_dotenv()

class GeminiClient:
    def __init__(self):
        self.keys = self._load_keys()
        self.current_key_index = 0
        self.model_name = "gemini-2.0-flash" # Default model
        
    def _load_keys(self):
        keys_file = os.getenv("GEMINI_API_KEYS_FILE")
        if keys_file and os.path.exists(keys_file):
            with open(keys_file, "r") as f:
                return json.load(f)
        
        # Fallback to single env var
        key = os.getenv("GEMINI_API_KEY")
        if key:
            return [key]
            
        print("Warning: No Gemini API keys found.")
        return []

    def _get_next_key(self):
        if not self.keys:
            raise Exception("No API keys available.")
        
        key = self.keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.keys)
        return key

    def configure_genai(self, key):
        genai.configure(api_key=key)

    def generate_content(self, prompt, retries=3):
        """
        Generates content with key rotation and backoff.
        """
        for attempt in range(retries):
            try:
                key = self._get_next_key()
                self.configure_genai(key)
                model = genai.GenerativeModel(self.model_name)
                
                response = model.generate_content(prompt)
                return response.text
                
            except exceptions.ResourceExhausted:
                print(f"Quota exceeded for key ending in ...{key[-4:]}. Rotating...")
                time.sleep(2 ** attempt) # Exponential backoff
                continue
            except Exception as e:
                print(f"Error generating content: {e}")
                if attempt == retries - 1:
                    raise e
                time.sleep(1)
                
        raise Exception("Failed to generate content after retries.")

    def generate_json(self, prompt, retries=3):
        """
        Helper to generate JSON content.
        """
        full_prompt = f"{prompt}\n\nOutput strictly valid JSON."
        text = self.generate_content(full_prompt, retries)
        
        # Clean up markdown code blocks if present
        text = text.replace("```json", "").replace("```", "").strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON: {text}")
            raise

    def generate_audio(self, text, retries=3):
        """
        Generates audio from text.
        """
        # Note: This is a placeholder for the actual audio generation call.
        # As of now, the Python SDK might not have a direct 'generate_audio' helper 
        # that returns bytes in the same way as text.
        # We will assume we can ask the model to "read this" and get audio parts,
        # OR we might need to use a specific endpoint.
        # For now, let's try to prompt for audio and see if we get a part with mime_type audio/wav.
        
        prompt = f"Read the following text clearly and naturally:\n\n{text}"
        
        for attempt in range(retries):
            try:
                # Use specific TTS model
                model = genai.GenerativeModel("gemini-2.5-flash-preview-tts")
                
                # We need to request audio output if supported, or just check response parts
                # Some models might need specific config
                response = model.generate_content(prompt, generation_config={"response_modalities": ["AUDIO"]})
                
                # Check for audio parts
                for part in response.parts:
                    if hasattr(part, "inline_data") and part.inline_data.mime_type.startswith("audio"):
                        print(f"Found audio part: {part.inline_data.mime_type}, length: {len(part.inline_data.data)}")
                        return part.inline_data.data
                
                # If no audio part, maybe it's not supported by this model/prompt
                # For the sake of the exercise, if we can't get audio, we might mock it or fail.
                # Let's try to see if we can force it.
                print("No audio part found in response.")
                return None
                
            except exceptions.ResourceExhausted:
                print(f"Quota exceeded for key ending in ...{key[-4:]}. Rotating...")
                time.sleep(2 ** attempt)
                continue
            except Exception as e:
                print(f"Error generating audio: {e}")
                if attempt == retries - 1:
                    raise e
                time.sleep(1)
        
        raise Exception("Failed to generate audio after retries.")

client = GeminiClient()
