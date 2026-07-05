import json
import time
from typing import Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError
from openai import OpenAI

from config import OLLAMA_BASE_URL, DEFAULT_MODEL

# Type variable for Pydantic generics
T = TypeVar('T', bound=BaseModel)

# Initialize the OpenAI client pointing to LOCAL OLLAMA
client = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama" # The SDK requires a string here, but Ollama ignores it
)

def llm_call(
    prompt: str, 
    schema: Optional[Type[T]] = None, 
    temperature: float = 0.1, # DROPPED TEMPERATURE: crucial for small local models
    max_retries: int = 3
) -> str | T:
    """
    Core LLM execution using local Ollama.
    """
    messages = []
    
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

    attempt = 0
    while attempt < max_retries:
        try:
            # Fire the request to localhost
            completion = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages,
                temperature=temperature, # Kept low for deterministic JSON
                stream=False
            )
            
            result_text = completion.choices[0].message.content.strip()
            
            # Clean up rogue markdown formatting
            if result_text.startswith("```json"):
                result_text = result_text.strip("```json").strip("```").strip()
            elif result_text.startswith("```"):
                result_text = result_text.strip("```").strip()

            # Enforce Pydantic validation
            if schema:
                return schema.model_validate_json(result_text)
                
            return result_text

        except ValidationError as e:
            attempt += 1
            print(f"[WARNING] Local model drifted from schema. Retrying... ({attempt}/{max_retries})")
            if attempt == max_retries:
                print(f"[FATAL] Schema validation failed after {max_retries} attempts. Raw Output:\n{result_text}")
                raise e
                
        except Exception as e:
            attempt += 1
            print(f"[ERROR] Ollama API Call Failed: {str(e)}. Is Ollama running?")
            time.sleep(1) # Short sleep before retry
            if attempt == max_retries:
                raise e