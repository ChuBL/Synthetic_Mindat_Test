"""
generate_diverse_queries.py

Generate diverse natural language queries by combining parameter recipes and style recipes.

Run:
python generate_diverse_queries.py
"""
import time
import json
import os
from pathlib import Path
from openai import AzureOpenAI
import tqdm
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List

load_dotenv(override=True)

# Azure OpenAI configuration
azure_endpoint = os.getenv("AZURE_OPENAI_API_ENDPOINT")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")
deployment_name = os.getenv("AZURE_DEPLOYMENT_NAME")

client = AzureOpenAI(
    azure_endpoint=azure_endpoint,
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=api_version,
)

# Fixed parameter recipes
all_param_recipes = [
    # --- Single Parameters ---
    # "hardness_min only (e.g., 'show me minerals harder than 6')",
    # "hardness_max only (e.g., 'find minerals with hardness below 3')",
    # "crystal_system (single value) (e.g., 'I need 'Isometric' minerals')",
    # "el_inc (single element) (e.g., 'what contains Gold (Au)?')",
    # "el_exc (single element) (e.g., 'find minerals without any Iron (Fe)')",
    # "ima: false (e.g., 'show me all minerals, even non-IMA ones')",
    # "ima: true (explicit) (e.g., 'I only want IMA-approved minerals')",
    # --- Parameter Combinations (AND logic) ---
    "hardness_min and hardness_max (e.g., 'find minerals with hardness between 5 and 7')",
    "crystal_system (multiple values, OR logic) (e.g., 'find minerals that are 'Hexagonal' or 'Tetragonal')",
    "el_inc (multiple elements, AND logic) (e.g., 'must contain both Fe and Cu')",
    "el_exc (multiple elements, OR logic) (e.g., 'show me minerals that dont have 'S' or 'O'')",
    "crystal_system and el_inc (e.g., 'show me 'Monoclinic' minerals that have 'Pb')",
    "hardness_min and el_exc (e.g., 'I want minerals harder than 4 that do not have 'S'')",
    "el_inc and el_exc (e.g., 'minerals that have 'Cu' but not 'Fe'')",
    # --- Complex & Edge Cases ---
    "all parameters (complex) (e.g., 'find IMA-approved 'Triclinic' minerals, hardness 2-3, with 'Li' but no 'F'')",
    # "hardness range with only one bound (e.g., 'minerals with hardness of at least 8')",
    "chemical elements using full names (e.g., 'find minerals with 'Iron' and 'Copper'')"
]

# Invalid parameter recipes for RuleValidator testing
invalid_param_recipes = [
    
    # ========================================
    # SINGLE RULE VIOLATIONS
    # ========================================
    
    # --- rule_schema violations (unexpected fields) ---
    "Unexpected fields (e.g., 'find red minerals with hardness 5', 'show minerals with density > 3', 'minerals from California with high luster')",
    
    # --- rule_hardness_range violations ---
    "hardness out of valid range [1-10] (e.g., 'find minerals with hardness greater than 12', 'find minerals with hardness less than 0', 'hardness greater than -1', 'hardness less than 11')",
    "hardness_min exceeds hardness_max (e.g., 'find minerals with hardness greater than 8 but less than 4', 'hardness greater than 7 but less than 2', 'min hardness 9, max hardness 3')",
    
    # --- rule_crystal_system violations ---
    "Invalid crystal system names (e.g., 'find Cubic minerals', 'Rectangular or Pentagonal systems', 'Square crystal structure')",
    
    # --- rule_chemical_element violations ---
    "Invalid element symbols (e.g., 'minerals with Xx', 'contains Ironium and Copperium', 'with Fe, Cu, and Zz', 'exclude Goldenium and Yy')",
    
    # --- rule_element_conflict violations ---
    "Same elements in both el_inc and el_exc (e.g., 'minerals with Fe but without Iron', 'contains Copper but exclude Cu', 'with Ag but exclude Sliver', 'include Gold exclude Au')",
    
    # Irrelevant queries with misleading keywords
    "Irrelevant queries with mineral-related keywords (e.g., 'I visited an iron bridge yesterday, it was very hard and had a cubic structure', 'My breakfast contains minerals like Iron, Calcium and Zinc for hardness of bones', 'The crystal display in the museum excluded gold and silver pieces', 'I need a hard mineral water brand, preferably one without sulfur smell')",
    # ========================================
    # COMBINATION VIOLATIONS (2 rules)
    # ========================================
    
    "Unexpected field + hardness violations (e.g., 'find red minerals with hardness 15', 'blue minerals with hardness greater than 11 but less than 5')",
    "Unexpected field + invalid crystal system or element (e.g., 'find shiny Cubic minerals', 'colorful minerals with Ironium', 'transparent minerals exclude Oxygen')",
    
    "Hardness violations + invalid crystal system or element (e.g., 'Pentagonal minerals with hardness 12', 'minerals with Xx and hardness greater than 9 but less than 3', 'Cubic system with Iron, hardness 0')",
    
    "Invalid crystal system + invalid element or conflict (e.g., 'Cubic minerals with Xx', 'Rectangular system with Fe but exclude Iron', 'Pentagonal minerals containing Gold but not Au')",
    
    "Invalid element + element conflict (e.g., 'minerals with Xx and Fe but exclude Iron', 'contains Ironium and Copper but excludes Cu')",
    
    # ========================================
    # COMBINATION VIOLATIONS (3 rules)
    # ========================================
    
    # "Unexpected field + hardness violations + invalid crystal system or element (e.g., 'red Cubic minerals with hardness 15', 'shiny minerals with Ironium and hardness greater than 10 but less than 3')",
    
    # "Hardness violations + invalid crystal system + invalid element or conflict (e.g., 'Cubic minerals with Xx and hardness 12', 'Rectangular minerals with Iron but exclude Fe, hardness greater than 8 but less than 2')",
    
    # "Unexpected field + invalid crystal system + element conflict (e.g., 'blue Pentagonal minerals with Fe but exclude Iron', 'shiny Cubic minerals with Gold exclude Au')",
    
    # ========================================
    # EDGE CASES & ROBUSTNESS
    # ========================================
    
    # "Case mixing and format variations (e.g., 'minerals with FE, cu but exclude Iron, Copper', 'heXAgonal or TeTRagonal systems with GOLD but not au')",
    # "Multiple spelling/format errors (e.g., 'find minearls with Hexgonal system, hardnes twelve, and Ironium exclude Oxygen')",
]

# Fixed style recipes
all_style_recipes = [
    # --- Formal / "Happy Path" ---
    "Formal and precise (e.g., 'Requesting all minerals with Mohs hardness from 6.5 to 7.0.', 'Could you please find minerals containing Iron and Zinc?', 'Find all the 'Amorphous' minerals.')",
    # "Clear and polite (e.g., 'Could you please find minerals containing Iron and Zinc?')",
    # "Structured as a clear question (e.g., 'What are all the 'Amorphous' minerals?')",
    # # --- Informal / Conversational ---
    "Casual and common (e.g., 'show me stuff with copper', 'I'm looking for lead minerals, they should be pretty soft, like maybe 3 or less.')",
    # "Uses common language/synonyms (e.g., 'what's the crystal shape for things with Fe?', 'I want 'hard' minerals.')",
    # "Slightly wordy/rambling (e.g., 'I'm looking for minerals, they should be pretty hard, like maybe 7 or more.')",
    # # --- Robustness & Error Injection (The "Issues") ---
    "Contains 1-2 spelling errors (e.g., 'find minerals with hardnes > 5', 'find minearls with 'Triclinc' sstem', 'need minerals w/ hardness btw 4 and 5', 'iron copper minerals hardness 2')",
    # "Contains typos/keyboard errors (e.g., 'find minearls with 'Triclinc' sstem')",
    # "Uses abbreviations or slang (e.g., 'need minerals w/ hardness btw 4 and 5', 'stuff that has Au')",
    # "Grammatically awkward or fragmented (e.g., 'minerals exclude sulfur hard 4', 'iron copper minerals hardness 2')",
    # "Ambiguous value (e.g., 'I need hard minerals, like 5, 6, or 7', 'find minerals with a hardness of around 4')",
    # "Case insensitivity test (e.g., 'show me minerals with 'fe' and 'cu'', 'crystal system is 'hexagonal'')",
    # "Implicit values (e.g., 'find minerals' -> implies ima:true, 'hard minerals' -> implies hardness_min)"
]

# Fixed function schema for all records
FIXED_FUNCTION_SCHEMA = {
    "name": "mindat_geomaterial",
    "description": "Retrieve the mineral datasets from Mindat geomaterial endpoint",
    "parameters": {
        "type": "dict",
        "properties": {
            "ima": {
                "type": "boolean",
                "description": "Only IMA-approved names, should be True by default except for user-specified otherwise"
            },
            "hardness_min": {
                "type": "float",
                "description": "Mohs hardness from"
            },
            "hardness_max": {
                "type": "float",
                "description": "Mohs hardness to"
            },
            "crystal_system": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["Amorphous", "Hexagonal", "Icosahedral", "Isometric", "Monoclinic", 
                            "Orthorhombic", "Tetragonal", "Triclinic", "Trigonal"]
                },
                "description": "Crystal system (csystem): multiple choice (OR)"
            },
            "el_inc": {
                "type": "string",
                "description": "Chemical elements must include, e.g., 'Fe,Cu'"
            },
            "el_exc": {
                "type": "string",
                "description": "Chemical elements must exclude, e.g., 'Fe,Cu'"
            }
        },
        "required": []
    }
}


# Pydantic model for structured output
class QueryList(BaseModel):
    queries: List[str]


def load_prompt_template(prompt_path: str) -> str:
    """Load prompt template from file."""
    with open(prompt_path, "r") as f:
        return f.read().strip()


def extract_max_id_from_file(file_path: str, id_prefix: str) -> int:
    """
    Extract the maximum ID from an existing JSONL file.
    
    Args:
        file_path: Path to the existing JSONL file
        id_prefix: ID prefix to match (e.g., "Mindat_v1" or "Mindat_invalid_v1")
        
    Returns:
        Maximum ID found in the file with matching prefix, or -1 if file doesn't exist or is empty
    """
    if not os.path.exists(file_path):
        return -1
    
    max_id = -1
    try:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    # Extract numeric ID from format "{id_prefix}_{id}"
                    if "id" in record:
                        id_str = record["id"]
                        # Check if the ID starts with the expected prefix
                        if id_str.startswith(f"{id_prefix}_"):
                            # Extract number after the prefix
                            numeric_part = id_str[len(id_prefix) + 1:]
                            numeric_id = int(numeric_part)
                            max_id = max(max_id, numeric_id)
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Warning: Could not parse line: {line[:50]}... Error: {e}")
                    continue
    except Exception as e:
        print(f"Warning: Error reading file {file_path}: {e}")
        return -1
    
    return max_id


def generate_queries_with_structured_output(
    prompt_template: str,
    param_recipe: str,
    style_recipe: str,
    num_queries: int,
    model_name: str = deployment_name,
    temperature: float = 1.0,
    max_tokens: int = 3072
) -> List[str]:
    """
    Generate multiple queries using structured output.
    
    Args:
        prompt_template: Template string with {params}, {style}, and {num_queries} placeholders
        param_recipe: Parameter recipe string
        style_recipe: Style recipe string
        num_queries: Number of queries to generate
        model_name: Model name to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens for generation
        
    Returns:
        List of generated query strings
    """
    # Format the prompt with parameters, style, and number of queries
    formatted_prompt = prompt_template.format(
        params=param_recipe,
        style=style_recipe,
        num_queries=num_queries
    )
    
    try:
        # Call API with structured output
        completion = client.beta.chat.completions.parse(
            model=model_name,
            messages=[
                {"role": "user", "content": formatted_prompt}
            ],
            response_format=QueryList,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Extract queries from structured response
        query_list = completion.choices[0].message.parsed
        return query_list.queries
        
    except Exception as e:
        print(f"Error generating queries: {e}")
        return []


def create_training_record(query: str, record_id: int, id_prefix: str) -> dict:
    """
    Create a training record in the required format.
    
    Args:
        query: Generated natural language query
        record_id: Sequential ID for the record
        id_prefix: Prefix for the record ID (e.g., "Mindat_v1" or "Mindat_invalid_v1")
        
    Returns:
        Dictionary in the required training format
    """
    return {
        "id": f"{id_prefix}_{record_id}",
        "question": [[{"role": "user", "content": query}]],
        "function": [FIXED_FUNCTION_SCHEMA]
    }


def generate_diverse_training_data(
    prompt_path: str,
    output_dir: str,
    output_filename: str,
    param_recipes: List[str],
    style_recipes: List[str],
    id_prefix: str,
    num_queries_per_combination: int,
    model_name: str = deployment_name,
    temperature: float = 1.0,
    max_tokens: int = 3072
):
    """
    Generate diverse training data by iterating through all parameter-style combinations.
    
    Args:
        prompt_path: Path to prompt template file
        output_dir: Directory to save output
        output_filename: Name of output JSONL file
        param_recipes: List of parameter recipes to use
        style_recipes: List of style recipes to use
        id_prefix: Prefix for record IDs (e.g., "Mindat_v1" or "Mindat_invalid_v1")
        num_queries_per_combination: Number of queries to generate per combination
        model_name: Model name to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens for generation
    """
    # Load prompt template
    prompt_template = load_prompt_template(prompt_path)
    
    # Ensure prompt has required placeholders and add num_queries instruction
    if "{params}" not in prompt_template or "{style}" not in prompt_template:
        raise ValueError("Prompt template must contain {params} and {style} placeholders")
    
    # Append instruction about number of queries to generate
    prompt_template += f"\n\nGenerate exactly {{num_queries}} diverse queries following the above criteria."
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)
    
    # Check if output file exists and extract maximum ID
    max_existing_id = extract_max_id_from_file(output_path, id_prefix)
    
    if max_existing_id >= 0:
        # File exists with valid IDs
        record_id = max_existing_id + 1
        file_mode = "a"  # Append mode
        print(f"Existing file found: {output_path}")
        print(f"Maximum existing ID with prefix '{id_prefix}': {max_existing_id}")
        print(f"Starting new records from ID: {record_id}")
    else:
        # File doesn't exist or has no valid IDs with this prefix
        record_id = 0
        file_mode = "w"  # Write mode (overwrite)
        print(f"No existing file found or no records with prefix '{id_prefix}'")
        print(f"Starting new records from ID: {record_id}")
    
    # Calculate total combinations
    total_combinations = len(param_recipes) * len(style_recipes)
    print(f"\nTotal combinations: {total_combinations}")
    print(f"Queries per combination: {num_queries_per_combination}")
    print(f"Total queries to generate: {total_combinations * num_queries_per_combination}")
    
    # Open output file in appropriate mode
    with open(output_path, file_mode) as f:
        # Iterate through all combinations
        for param_recipe in tqdm.tqdm(param_recipes, desc="Parameter recipes"):
            for style_recipe in tqdm.tqdm(style_recipes, desc="Style recipes", leave=False):
                
                # Generate queries for this combination
                queries = generate_queries_with_structured_output(
                    prompt_template=prompt_template,
                    param_recipe=param_recipe,
                    style_recipe=style_recipe,
                    num_queries=num_queries_per_combination,
                    model_name=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # Create training records for each generated query
                for query in queries:
                    record = create_training_record(query, record_id, id_prefix)
                    # Write as JSONL (one JSON per line)
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    record_id += 1
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
    
    print(f"\nGeneration complete!")
    print(f"Total records generated in this run: {record_id - (max_existing_id + 1) if max_existing_id >= 0 else record_id}")
    print(f"Total records in file with prefix '{id_prefix}': {record_id}")
    print(f"Output saved to: {output_path}")


def main():
    """Main execution function."""
    
    # ========================================
    # USER CONFIGURATION
    # ========================================
    
    # Select parameter recipes: choose ONE of the following
    # - all_param_recipes: for valid/happy path queries
    # - invalid_param_recipes: for invalid queries to test RuleValidator
    selected_param_recipes = invalid_param_recipes  # Change this to invalid_param_recipes for invalid queries
    
    # Select style recipes (applies to both valid and invalid parameter recipes)
    selected_style_recipes = all_style_recipes
    
    # ID prefix configuration
    # - Use "Mindat_v1" for valid queries
    # - Use "Mindat_v1_irrelevance" for invalid queries
    id_prefix = "Mindat_v1_irrelevance"  # Change this to "Mindat_v1_irrelevance" for invalid queries
    
    # Output configuration
    output_dir = 'output'
    output_filename = 'BFCL_V4_Mindat_v1_irrelevance.json'  # Customize as needed
    
    # Prompt configuration
    prompt_filename = 'gemini_mindat_prompt_v1.md'
    prompt_path = Path('prompt', prompt_filename)
    
    # ========================================
    # VALIDATION & EXECUTION
    # ========================================
    
    # Check if prompt file exists
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    # Display current configuration
    recipe_type = "VALID (happy path)" if selected_param_recipes == all_param_recipes else "INVALID (RuleValidator testing)"
    print("=" * 60)
    print("CONFIGURATION")
    print("=" * 60)
    print(f"Recipe Type: {recipe_type}")
    print(f"ID Prefix: {id_prefix}")
    print(f"Parameter Recipes: {len(selected_param_recipes)} recipes")
    print(f"Style Recipes: {len(selected_style_recipes)} recipes")
    print(f"Output File: {output_dir}/{output_filename}")
    print("=" * 60)
    print()
    
    # Generate training data
    generate_diverse_training_data(
        prompt_path=str(prompt_path),
        output_dir=output_dir,
        output_filename=output_filename,
        param_recipes=selected_param_recipes,
        style_recipes=selected_style_recipes,
        id_prefix=id_prefix,
        num_queries_per_combination=5,  # Generate 5 queries per combination
        model_name=deployment_name,
        temperature=1.0,
        max_tokens=3072
    )


if __name__ == "__main__":
    main()