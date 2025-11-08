import json
from itertools import permutations

def generate_all_combinations(elements):
    """
    Generate all possible combinations for a list of elements.
    For ["Fe", "Mg"], generates:
    - ["Fe", "Mg"] (original list)
    - ["Mg", "Fe"] (reversed list)
    - "Fe,Mg" (comma-separated)
    - "Mg,Fe" (reversed comma-separated)
    """
    if not elements or len(elements) == 0:
        return [elements]
    
    combinations = []
    
    # Generate all permutations as lists
    if len(elements) > 1:
        for perm in permutations(elements):
            # Add list format
            combinations.append(list(perm))
    else:
        # Single element case - just add as list
        combinations.append(elements)
    
    # Generate all permutations as comma-separated strings
    if len(elements) > 1:
        for perm in permutations(elements):
            # Add comma-separated format
            combinations.append(",".join(perm))
    else:
        # Single element as string
        combinations.append(elements[0])
    
    return combinations

def transform_element_field(data):
    """
    Transform el_inc and el_exc fields from [["Fe", "Mg"]] 
    to [["Fe", "Mg"], ["Mg", "Fe"], ["Fe,Mg"], ["Mg,Fe"]]
    """
    if isinstance(data, dict):
        for key, value in data.items():
            # Check if this is el_inc or el_exc field
            if key in ["el_inc", "el_exc"] and isinstance(value, list):
                transformed = []
                for item in value:
                    if isinstance(item, list):
                        # Generate all combinations for this element list
                        combinations = generate_all_combinations(item)
                        transformed.extend(combinations)
                    else:
                        # Keep non-list items as is
                        transformed.append(item)
                data[key] = transformed
            elif isinstance(value, (dict, list)):
                # Recursively process nested structures
                transform_element_field(value)
    elif isinstance(data, list):
        for item in data:
            transform_element_field(item)
    return data

def transform_crystal_system(data):
    """
    Transform crystal_system field: if it has only one string value, 
    convert it from ["value"] to ["value", ["value"]]
    Keep unchanged if:
    - It already has multiple values (e.g., ["A", "B"])
    - The first element is a list (e.g., [["A", "B"]])
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "crystal_system":
                # Check if it's a list with exactly one element AND that element is a string
                if isinstance(value, list) and len(value) == 1 and isinstance(value[0], str):
                    # Transform to ["value", ["value"]]
                    data[key] = [value[0], [value[0]]]
                # If the first element is a list or it has multiple values, keep unchanged
            else:
                # Recursively process nested structures
                if isinstance(value, (dict, list)):
                    transform_crystal_system(value)
    elif isinstance(data, list):
        for item in data:
            transform_crystal_system(item)
    return data

def process_jsonl_complete(input_file, output_file):
    """
    Complete processing pipeline:
    1. Read and sort JSONL file by ID
    2. Transform el_inc and el_exc fields
    3. Transform crystal_system field
    4. Write to output file
    """
    # Step 1: Read all lines and parse JSON
    print("Step 1: Reading and sorting data...")
    data_list = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():  # Skip empty lines
                data_list.append(json.loads(line))
    
    # Step 2: Sort by ID in ascending order
    # Extract numeric part from ID (e.g., "Mindat_v1_112" -> 112)
    data_list.sort(key=lambda x: int(x['id'].split('_')[-1]))
    print(f"Sorted {len(data_list)} records by ID")
    
    # Step 3: Transform each record and write to output
    print("Step 2: Transforming el_inc and el_exc fields...")
    print("Step 3: Transforming crystal_system fields...")
    print("Step 4: Writing to output file...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for idx, item in enumerate(data_list, 1):
            # Apply element field transformation
            item = transform_element_field(item)
            # Apply crystal system transformation
            item = transform_crystal_system(item)
            # Write to output
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
            if idx % 100 == 0:
                print(f"Processed {idx}/{len(data_list)} records...")
    
    print(f"\nProcessing complete!")
    print(f"Total records processed: {len(data_list)}")
    print(f"Output saved to: {output_file}")

# Main execution
if __name__ == "__main__":
    input_file = 'test_input.jsonl'
    output_file = 'test_output.jsonl'
    
    print("=" * 60)
    print("JSONL File Processing Pipeline")
    print("=" * 60)
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print("=" * 60)
    
    process_jsonl_complete(input_file, output_file)