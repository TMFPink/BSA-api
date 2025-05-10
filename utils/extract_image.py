import base64
import openai
from openai import OpenAI
import json
import os
from django.conf import settings

def encode_image_to_base64(image_file):
    """Convert image file to base64 encoding for API submission"""
    image_file.seek(0)  # Reset file pointer to beginning
    return base64.b64encode(image_file.read()).decode('utf-8')

def extract_bill_data(image_file):
    """
    Process bill image through OpenAI Vision API to extract structured data
    """
    base64_image = encode_image_to_base64(image_file)
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    print("API Key:", settings.OPENAI_API_KEY)
    
    try:
        response = client.chat.completions.create(
            
            messages=[
                {
                    "role": "system",
                    "content": """You are a bill processing assistant. Extract information from bill images into structured data.
                    Return ONLY valid JSON with the following structure:
                    {
                        "billName": "Store or Restaurant Name",
                        "category": "Food", (Detect a category in these "Food", "Entertainment", "Transport", "Others". based on the bill)
                        "total_amount": 123.45, (just the number without currency symbol)
                        "date": "2025-05-07T12:34:56Z", (ISO format date, guess current date if not found)
                        "billDetails": [
                            {"description": "Item 1 name", "amount": 10.99},
                            {"description": "Item 2 name", "amount": 15.99}
                        ]
                    }"""
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract the details from this bill image and return them in JSON format."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
                
            ],
            model="gpt-4.1-mini",
            temperature=0,
        )
        result = response.choices[0].message.content.strip()
        
        
        
        # Clean up the response to ensure it's valid JSON
        if result.startswith("```json"):
            result = result[7:]
        if result.endswith("```"):
            result = result[:-3]
            
        return json.loads(result.strip())
    
    except Exception as e:
        # Log the error in production
        return {
            "error": f"Failed to process bill: {str(e)}",
        }