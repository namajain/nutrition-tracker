import os
import json
import openai
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
if API_KEY:
    openai.api_key = API_KEY

class AIService:
    @staticmethod
    def analyze_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
        if not API_KEY:
            # Fallback mock response if no key
            return {
                "name": "Mock AI Recipe (No Key)",
                "ingredients": [
                    {"name": "Chicken Breast", "quantity": 150, "unit": "g", "confidence": 0.9},
                    {"name": "Rice", "quantity": 200, "unit": "g", "confidence": 0.85}
                ],
                "nutrition_estimate": {
                    "energy_kcal": 450,
                    "protein_g": 35,
                    "carbs_g": 50,
                    "fat_g": 5
                }
            }

        client = openai.OpenAI(api_key=API_KEY)
        
        # Load prompt from file
        try:
            with open(os.path.join(os.path.dirname(__file__), "prompts", "image_analysis.md"), "r") as f:
                prompt = f.read()
        except FileNotFoundError:
             # Fallback if file missing
             prompt = """
             You are a precise food analyst. Given a meal photo, output JSON only with the following structure:
             ... (fallback text)
             """

        try:
            import base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                response_format={ "type": "json_object" }
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"AI Error: {e}")
            return {"error": str(e)}

