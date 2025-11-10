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
    "Invalid crystal system names (e.g., 'find Cubic minerals', 'Rectangular or Pentagonal systems', 'Hexgonal system' [typo], 'Square crystal structure')",
    
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