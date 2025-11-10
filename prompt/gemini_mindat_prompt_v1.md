base_prompt_template = f"""You are a synthetic data generator for testing a natural language API. Your task is to generate a single user request that matches a specific set of criteria including valid and invalid cases.

API Schema (Ground Truth):
```python
class MindatQueryDict(BaseModel):
    ima: Optional[bool] = Field(description="Only IMA-approved names")
    hardness_min: Optional[float] = Field(description="Mohs hardness from")
    hardness_max: Optional[float] = Field(description="Mohs hardness to")
    crystal_system: Optional[list[str]] = Field(description="Enum: 'Amorphous','Hexagonal','Isometric', 'Monoclinic', 'Orthorhombic', 'Tetragonal', 'Triclinic', 'Trigonal'")
    el_inc: Optional[str] = Field(description="Chemical elements must include, e.g., 'Fe,Cu'")
    el_exc: Optional[str] = Field(description="Chemical elements must exclude, e.g., 'Fe,Cu'")
````

Generation Criteria:

  * Target Parameters: {params}
  * Query Style: {style}

Output:
Provide *only* the raw natural language query and nothing else. Do not add quotation marks, labels, or any other text.