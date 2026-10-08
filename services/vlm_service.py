import os
from google import genai
import PIL.Image
from config.settings import settings

class VLMService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key:
            print("WARNING: GEMINI_API_KEY not found in settings. VLM will not work.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)
            self.model = 'gemini-3.7-flash'

    def describe_image(self, image_path: str) -> str:
        if not self.client:
            return ""
            
        try:
            import time
            img = PIL.Image.open(image_path)
            
            models_to_try = ['gemini-3.8-flash', 'gemini-3.7-flash', 'gemini-3.6-flash', 'gemini-3.5-flash']
            
            for model_name in models_to_try:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=[
                            "Describe this image in detail. Focus on extracting and explaining any diagrams, charts, equations, tables, or key textual information present. Be concise and factual. Do not output anything if the image is mostly blank or purely decorative.",
                            img
                        ]
                    )
                    return response.text
                except Exception as e:
                    error_msg = str(e).lower()
                    if any(err in error_msg for err in ["429", "quota", "503", "unavailable"]):
                        print(f"Gemini API ({model_name}) busy. Failing over to next model...")
                        time.sleep(2)
                        continue
                    else:
                        raise e
            
            print(f"All Gemini models failed or overloaded for {image_path}.")
            return ""
        except Exception as e:
            print(f"VLM Error on {image_path}: {e}")
            return ""

vlm_service = VLMService()
