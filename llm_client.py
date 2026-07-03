import json
import time
from typing import Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError
from openai import OpenAI

# Import the new keys from your config file
from config import NVIDIA_API_KEY, DEFAULT_MODEL

# Type variable for Pydantic generics
T = TypeVar('T', bound=BaseModel)

# Initialize the OpenAI client pointing to NVIDIA's endpoints
client = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key=NVIDIA_API_KEY
)

def llm_call(
    prompt: str, 
    schema: Optional[Type[T]] = None, 
    temperature: float = 0.6,
    max_retries: int = 3
) -> str | T:
    """
    Core LLM execution using NVIDIA's API.
    If a Pydantic schema is provided, it forces structured JSON output.
    """
    messages = []
    
    # Force the 80B model into strict JSON extraction mode if needed
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
            # Fire the request to NVIDIA
            completion = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages,
                temperature=temperature,
                top_p=0.7,
                max_tokens=4096,
                stream=False
            )
            
            result_text = completion.choices[0].message.content.strip()
            
            # Clean up rogue markdown formatting if the model gets chatty
            if result_text.startswith("```json"):
                result_text = result_text.strip("```json").strip("```").strip()
            elif result_text.startswith("```"):
                result_text = result_text.strip("```").strip()

            # Enforce Pydantic validation before returning to the Orchestrator
            if schema:
                return schema.model_validate_json(result_text)
                
            return result_text

        except ValidationError as e:
            attempt += 1
            print(f"[WARNING] Model drifted from schema. Retrying... ({attempt}/{max_retries})")
            if attempt == max_retries:
                print(f"[FATAL] Schema validation failed. Raw Output:\n{result_text}")
                raise e
                
        except Exception as e:
            attempt += 1
            error_msg = str(e).lower()
            
            # If NVIDIA rate limits us or times out, use exponential backoff
            if "429" in error_msg or "timeout" in error_msg:
                wait_time = 2 ** attempt
                print(f"[WARNING] NVIDIA API stressed. Sleeping {wait_time}s... ({attempt}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"[ERROR] API Call Failed: {str(e)}")
                if attempt == max_retries:
                    raise e