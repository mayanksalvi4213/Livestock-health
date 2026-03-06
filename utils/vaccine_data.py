"""
Vaccine data module containing comprehensive information about livestock vaccines
This data maps diseases to their corresponding vaccines and provides detailed information
"""

# Master dictionary mapping diseases to their associated vaccines
DISEASE_VACCINES = {
    # Cow diseases
    "Foot and Mouth Disease": {
        "name": "FMD Vaccine",
        "description": "Protects against the highly contagious Foot and Mouth Disease virus that affects cloven-hoofed animals.",
        "schedule": "Every 6 months",
        "administration": "Subcutaneous injection",
        "first_dose_age": "4 months",
        "animals": ["cow", "goat"],
        "effectiveness": "85-95%",
        "side_effects": "Mild swelling at injection site, slight fever for 1-2 days",
        "storage": "2-8°C, do not freeze",
        "notes": "Mandatory vaccination in many regions due to high economic impact"
    },
    "Brucellosis": {
        "name": "Brucella Vaccine",
        "description": "Prevents Brucellosis, a bacterial infection that causes abortion and infertility in cattle.",
        "schedule": "One-time vaccination",
        "administration": "Subcutaneous injection",
        "first_dose_age": "4-8 months (female calves only)",
        "animals": ["cow"],
        "effectiveness": "70-90%",
        "side_effects": "Local reaction at injection site",
        "storage": "2-8°C, protect from light",
        "notes": "Caution: This is a live vaccine - use protective equipment during administration"
    },
    "Lumpy Skin Disease": {
        "name": "LSD Vaccine",
        "description": "Protects against Lumpy Skin Disease, a viral disease characterized by nodules on the skin.",
        "schedule": "Annual",
        "administration": "Subcutaneous injection",
        "first_dose_age": "6 months",
        "animals": ["cow"],
        "effectiveness": "80-95%",
        "side_effects": "Mild fever, temporary reduction in milk yield",
        "storage": "2-8°C, protect from light",
        "notes": "Essential in regions where LSD is endemic"
    },
    "Lumpy Cows": {
        "name": "LSD Vaccine (Lumpy Skin Disease)",
        "description": "Live attenuated vaccine specifically developed for the prevention of Lumpy Skin Disease in cattle. Provides strong immunity against the capripoxvirus that causes nodular skin lesions.",
        "schedule": "Annual vaccination, with boosters every 6 months in high-risk areas",
        "administration": "Subcutaneous injection, 2ml dose in the neck region",
        "first_dose_age": "6 months of age, can be administered to pregnant cows",
        "effectiveness": "85-95% protection against clinical disease",
        "side_effects": "Mild transient fever, local swelling at injection site which resolves within 1-2 weeks",
        "storage": "2-8°C, protected from light and heat, maintain cold chain",
        "animals": ["cow"],
        "notes": "Critical for cattle in endemic areas. Multiple commercial formulations available (Lumpyvax, LSDV, Neethling strain vaccines). Vaccination is the most effective control measure."
    },
    "Black Quarter": {
        "name": "BQ Vaccine",
        "description": "Prevents Black Quarter, a fatal bacterial disease affecting the muscles of cattle.",
        "schedule": "Annual (before monsoon)",
        "administration": "Subcutaneous injection",
        "first_dose_age": "6 months",
        "animals": ["cow"],
        "effectiveness": "85-90%",
        "side_effects": "Mild swelling at injection site",
        "storage": "2-8°C",
        "notes": "Critical for cattle in areas with previous Black Quarter outbreaks"
    },
    "Hemorrhagic Septicemia": {
        "name": "HS Vaccine",
        "description": "Protects against Hemorrhagic Septicemia, a bacterial disease causing acute fever and respiratory distress.",
        "schedule": "Annual",
        "administration": "Subcutaneous injection",
        "first_dose_age": "6 months",
        "animals": ["cow"],
        "effectiveness": "80-95%",
        "side_effects": "Mild swelling at injection site",
        "storage": "2-8°C",
        "notes": "Particularly important during rainy season in endemic areas"
    },
    "Mastitis": {
        "name": "J-5 Bacterin",
        "description": "Vaccine against bacterial mastitis in dairy cattle, reducing severity of infections.",
        "schedule": "Pre-calving and mid-lactation",
        "administration": "Intramuscular injection",
        "first_dose_age": "Heifers before first calving",
        "animals": ["cow"],
        "effectiveness": "60-70% reduction in severity",
        "side_effects": "Mild swelling at injection site",
        "storage": "2-8°C",
        "notes": "Should be used alongside good milking hygiene practices"
    },
    "Tuberculosis": {
        "name": "BCG Vaccine",
        "description": "Limited protection against bovine tuberculosis, a chronic bacterial disease.",
        "schedule": "Varies by region",
        "administration": "Intradermal injection",
        "first_dose_age": "As directed by veterinarian",
        "animals": ["cow"],
        "effectiveness": "Variable",
        "side_effects": "Local reaction at injection site",
        "storage": "2-8°C, protect from light",
        "notes": "Not used in all countries; test-and-slaughter policies are more common"
    },
    "Infectious Bovine Rhinotracheitis": {
        "name": "IBR Vaccine",
        "description": "Prevents IBR, a viral respiratory disease that can cause reproductive problems.",
        "schedule": "Annual",
        "administration": "Intramuscular or intranasal",
        "first_dose_age": "3-4 months",
        "animals": ["cow"],
        "effectiveness": "75-90%",
        "side_effects": "Mild respiratory signs with intranasal form",
        "storage": "2-8°C",
        "notes": "Available in modified live and killed forms"
    },
    "Bovine Viral Diarrhea": {
        "name": "BVD Vaccine",
        "description": "Protects against Bovine Viral Diarrhea, a viral disease affecting reproductive and immune systems.",
        "schedule": "Annual",
        "administration": "Intramuscular injection",
        "first_dose_age": "6-8 months",
        "animals": ["cow"],
        "effectiveness": "70-90%",
        "side_effects": "Minimal",
        "storage": "2-8°C",
        "notes": "Critical for breeding herds"
    },
    "Pinkeye": {
        "name": "Moraxella Bovis Bacterin",
        "description": "Vaccine against infectious bovine keratoconjunctivitis (pinkeye), a bacterial eye infection.",
        "schedule": "Annual (before fly season)",
        "administration": "Subcutaneous injection",
        "first_dose_age": "6 months",
        "animals": ["cow"],
        "effectiveness": "60-80%",
        "side_effects": "Minimal",
        "storage": "2-8°C",
        "notes": "Most effective when administered before peak fly season"
    },
    "Ringworm": {
        "name": "Ringworm Vaccine",
        "description": "Protects against bovine dermatophytosis (ringworm), a fungal skin infection.",
        "schedule": "Two doses 10-14 days apart",
        "administration": "Intramuscular injection",
        "first_dose_age": "Any age above 1 month",
        "animals": ["cow", "goat"],
        "effectiveness": "70-80%",
        "side_effects": "Mild swelling at injection site",
        "storage": "2-8°C",
        "notes": "Both preventive and therapeutic effects"
    },
    
    # Goat diseases
    "Peste des Petits Ruminants": {
        "name": "PPR Vaccine",
        "description": "Protects against PPR, a highly contagious viral disease of goats and sheep.",
        "schedule": "Annual",
        "administration": "Subcutaneous injection",
        "first_dose_age": "3 months",
        "animals": ["goat"],
        "effectiveness": "90-95%",
        "side_effects": "Minimal",
        "storage": "2-8°C, reconstitute before use",
        "notes": "Essential in all small ruminant herds in endemic areas"
    },
    "Contagious Caprine Pleuropneumonia": {
        "name": "CCPP Vaccine",
        "description": "Protects against CCPP, a contagious bacterial disease affecting lungs of goats.",
        "schedule": "Annual",
        "administration": "Subcutaneous injection",
        "first_dose_age": "4 months",
        "animals": ["goat"],
        "effectiveness": "85-90%",
        "side_effects": "Small nodule at injection site",
        "storage": "2-8°C",
        "notes": "Critical in areas with previous CCPP outbreaks"
    },
    "Goat Pox": {
        "name": "Goat Pox Vaccine",
        "description": "Prevents goat pox, a viral disease causing skin lesions and systemic illness.",
        "schedule": "Annual",
        "administration": "Subcutaneous injection",
        "first_dose_age": "3 months",
        "animals": ["goat"],
        "effectiveness": "85-90%",
        "side_effects": "Mild fever, small nodule at injection site",
        "storage": "2-8°C, protect from light",
        "notes": "Live attenuated vaccine"
    },
    "Enterotoxemia": {
        "name": "Clostridial Vaccine",
        "description": "Protects against enterotoxemia (pulpy kidney disease) caused by Clostridium perfringens.",
        "schedule": "Annual, with booster during pregnancy",
        "administration": "Subcutaneous injection",
        "first_dose_age": "2-3 months",
        "animals": ["goat", "cow"],
        "effectiveness": "85-95%",
        "side_effects": "Minimal",
        "storage": "2-8°C",
        "notes": "Often combined with tetanus toxoid as multivalent clostridial vaccine"
    },
    
    # Chicken diseases
    "Newcastle Disease": {
        "name": "ND Vaccine",
        "description": "Protects against Newcastle Disease, a highly contagious viral disease affecting birds.",
        "schedule": "Multiple times during first few months, then every 3-6 months",
        "administration": "Eye drop, drinking water, or spray",
        "first_dose_age": "1-7 days",
        "animals": ["chicken"],
        "effectiveness": "90-95% with proper administration",
        "side_effects": "Mild respiratory signs with some strains",
        "storage": "2-8°C, or room temperature for thermostable variants",
        "notes": "Several types available (B1, La Sota, thermostable)"
    },
    "Infectious Bursal Disease": {
        "name": "Gumboro Vaccine",
        "description": "Prevents IBD (Gumboro), a viral disease affecting the immune system of young chickens.",
        "schedule": "2-3 times in first 6 weeks",
        "administration": "Drinking water or eye drop",
        "first_dose_age": "10-14 days",
        "animals": ["chicken"],
        "effectiveness": "85-95%",
        "side_effects": "Immunosuppression with some vaccine strains",
        "storage": "2-8°C",
        "notes": "Timing depends on maternal antibody levels"
    },
    "Avian Influenza": {
        "name": "AI Vaccine",
        "description": "Protects against specific strains of avian influenza virus.",
        "schedule": "As directed by authorities",
        "administration": "Subcutaneous or intramuscular injection",
        "first_dose_age": "1-10 days (depending on product)",
        "animals": ["chicken"],
        "effectiveness": "70-90% strain-specific",
        "side_effects": "Minimal",
        "storage": "2-8°C",
        "notes": "Use regulated in many countries; specific to circulating strains"
    },
    "Infectious Bronchitis": {
        "name": "IB Vaccine",
        "description": "Protects against infectious bronchitis, a highly contagious viral respiratory disease.",
        "schedule": "Multiple vaccinations starting at 1 day old",
        "administration": "Spray, eye drop, or drinking water",
        "first_dose_age": "1 day",
        "animals": ["chicken"],
        "effectiveness": "70-85%",
        "side_effects": "Mild respiratory reaction",
        "storage": "2-8°C",
        "notes": "Multiple serotypes available; match to local variants"
    },
    "Fowl Pox": {
        "name": "Fowl Pox Vaccine",
        "description": "Prevents fowl pox, a slow-spreading viral disease causing skin lesions.",
        "schedule": "Once at 6-10 weeks (layer/breeder)",
        "administration": "Wing-web stab",
        "first_dose_age": "6-10 weeks",
        "animals": ["chicken"],
        "effectiveness": "85-95%",
        "side_effects": "Small scab at vaccination site",
        "storage": "2-8°C, freeze-dried product",
        "notes": "Check for 'take' (reaction) 7 days post-vaccination"
    },
    "Coccidiosis": {
        "name": "Coccidiosis Vaccine",
        "description": "Protects against coccidiosis, a parasitic disease affecting intestines.",
        "schedule": "Single dose",
        "administration": "Spray on feed or drinking water",
        "first_dose_age": "1-5 days",
        "animals": ["chicken"],
        "effectiveness": "80-90%",
        "side_effects": "Mild intestinal reaction",
        "storage": "2-8°C",
        "notes": "Alternative to anticoccidial drugs in feed"
    },
    
    # Generic/default entry for diseases without specific vaccine data
    "default": {
        "name": "Consult veterinarian",
        "description": "A specific vaccine may be available for this condition. Please consult your veterinarian for appropriate vaccination advice.",
        "schedule": "As prescribed",
        "administration": "As directed by veterinarian",
        "first_dose_age": "As directed by veterinarian",
        "animals": ["cow", "goat", "chicken"],
        "effectiveness": "Varies",
        "side_effects": "Varies by product",
        "storage": "As per manufacturer's instructions",
        "notes": "Always follow your veterinarian's recommendations for vaccination"
    }
}

# Special case mappings for disease names that don't match exactly
disease_mappings = {
    "lumpy_cows": "Lumpy Skin Disease",
    "lumpy cows": "Lumpy Skin Disease",
    "lumpy skin": "Lumpy Skin Disease",
    "ringworm": "Ringworm",
    "blackquarter": "Black Quarter",
    "mastitis": "Mastitis",
    "pinkeye": "Pinkeye",
    "foot_and_mouth": "Foot and Mouth Disease",
    "foot and mouth": "Foot and Mouth Disease",
    "fmd": "Foot and Mouth Disease"
}

# Mapping of diseases to their vaccines
disease_vaccine_mapping = {
    "foot and mouth disease": "foot_and_mouth",
    "lumpy skin disease": "lumpy_skin_disease",
    "mastitis": "mastitis",
    "brucellosis": "brucellosis",
    "ringworm": "ringworm",
    "blackleg": "blackleg",
    "lumpy cows": "lumpy_skin_disease"  # Map "lumpy cows" to the same vaccine as "lumpy skin disease"
}

def get_vaccines_for_disease(disease_name):
    """
    Get vaccine information for a specific disease
    
    Args:
        disease_name (str): Name of the disease
        
    Returns:
        dict: Vaccine information or default entry if not found
    """
    print(f"Fetching vaccine info for disease: '{disease_name}'")
    # Special case mappings for disease names that don't match exactly
    disease_mappings = {
        "lumpy_cows": "Lumpy Skin Disease",
        "lumpy cows": "Lumpy Skin Disease",
        "lumpy skin": "Lumpy Skin Disease",
        "ringworm": "Ringworm",
        "blackquarter": "Black Quarter",
        "mastitis": "Mastitis",
        "pinkeye": "Pinkeye",
        "foot_and_mouth": "Foot and Mouth Disease",
        "foot and mouth": "Foot and Mouth Disease",
        "fmd": "Foot and Mouth Disease"
    }
    
    # Check if we have a mapping for this disease name
    if disease_name in disease_mappings:
        mapped_name = disease_mappings[disease_name]
        print(f"Mapped disease '{disease_name}' to '{mapped_name}'")
        disease_name = mapped_name
        
    # Case insensitive matching - try exact match first
    if disease_name in DISEASE_VACCINES:
        return DISEASE_VACCINES[disease_name]
        
    # Try case insensitive match
    for disease, vaccine in DISEASE_VACCINES.items():
        if disease.lower() == disease_name.lower():
            return vaccine
            
    # If no match found, return default
    print(f"No vaccine found for '{disease_name}', returning default vaccine")
    return DISEASE_VACCINES["default"]

def get_vaccines_for_animal(animal_type):
    """
    Get all vaccines applicable for a specific animal type
    
    Args:
        animal_type (str): Type of animal ('cow', 'goat', or 'chicken')
        
    Returns:
        list: List of vaccine dictionaries for the specified animal
    """
    vaccines = []
    
    for disease, vaccine in DISEASE_VACCINES.items():
        if disease != "default" and animal_type in vaccine.get("animals", []):
            # Add disease name to vaccine info
            vaccine_info = vaccine.copy()
            vaccine_info["disease"] = disease
            vaccines.append(vaccine_info)
            
    return vaccines 