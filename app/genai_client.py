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
        self.tts_model_name = os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
        
    def _load_keys(self):
        # Load from GEMINI_API_KEYS env var (JSON list)
        keys_env = os.getenv("GEMINI_API_KEYS")
        if keys_env:
            try:
                keys = json.loads(keys_env)
                if isinstance(keys, list) and len(keys) > 0:
                    return keys
            except json.JSONDecodeError:
                print("Warning: Failed to parse GEMINI_API_KEYS as JSON.")

        raise ValueError("No Gemini API keys found. Set GEMINI_API_KEYS (JSON list) in .env")

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
                key = self._get_next_key()
                self.configure_genai(key)
                
                # Use specific TTS model
                model = genai.GenerativeModel(self.tts_model_name)
                
                # We need to request audio output if supported, or just check response parts
                # Some models might need specific config
                response = model.generate_content(prompt, generation_config={"response_modalities": ["AUDIO"]})

                audio_bytes = self._extract_audio_bytes(response)
                if audio_bytes:
                    return audio_bytes

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

    def _extract_audio_bytes(self, response):
        """
        Attempts to extract audio bytes from common response shapes.
        """
        # Direct parts
        parts = getattr(response, "parts", None)
        if parts:
            for part in parts:
                inline = getattr(part, "inline_data", None)
                if inline and getattr(inline, "mime_type", "").startswith("audio"):
                    data = getattr(inline, "data", None)
                    if data:
                        print(f"Found audio part: {inline.mime_type}, length: {len(data)}")
                        return data

        # Candidate-based parts
        candidates = getattr(response, "candidates", None)
        if candidates:
            for candidate in candidates:
                content = getattr(candidate, "content", None)
                cand_parts = getattr(content, "parts", None) if content else None
                if not cand_parts:
                    continue
                for part in cand_parts:
                    inline = getattr(part, "inline_data", None)
                    if inline and getattr(inline, "mime_type", "").startswith("audio"):
                        data = getattr(inline, "data", None)
                        if data:
                            print(f"Found audio part: {inline.mime_type}, length: {len(data)}")
                            return data

        return None

client = GeminiClient()
