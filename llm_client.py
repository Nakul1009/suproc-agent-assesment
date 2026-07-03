import os
import json
from typing import Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError
from huggingface_hub import InferenceClient

from config import HF_TOKEN, DEFAULT_MODEL

# Type variable for Pydantic generics
T = TypeVar('T', bound=BaseModel)

# Initialize client globally to maintain connection pooling
client = InferenceClient(api_key=HF_TOKEN)

def llm_call(
    prompt: str, 
    schema: Optional[Type[T]] = None, 
    temperature: float = 0.7
) -> str | T:
    """
    Core LLM execution. 
    If a Pydantic schema is provided, it forces structured JSON output.
    """
    messages = []
    
    # If we need structured data, we lock the model into a strict data-extraction persona
    if schema:
        schema_json = schema.model_json_schema()
        system_msg = (
            "You are a strict data-extraction engine. "
            "You must output ONLY valid JSON matching this exact schema. "
            "Do not wrap the output in markdown blocks. Do not add conversational text.\n"
            f"Schema: {json.dumps(schema_json)}"
        )
        messages.append({"role": "system", "content": system_msg})
        
    messages.append({"role": "user", "content": prompt})

    try:
        completion = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            temperature=temperature,
        )
        
        result_text = completion.choices[0].message.content.strip()
        
        # If the model disobeys and wraps the JSON in markdown, strip it
        if result_text.startswith("```json"):
            result_text = result_text.strip("```json").strip("```").strip()
        elif result_text.startswith("```"):
            result_text = result_text.strip("```").strip()

        # Enforce Pydantic validation
        if schema:
            return schema.model_validate_json(result_text)
            
        return result_text

    except ValidationError as e:
        print(f"[ERROR] LLM failed to adhere to schema. Raw output:\n{result_text}")
        raise e
    except Exception as e:
        print(f"[ERROR] LLM Call Failed: {str(e)}")
        raise e