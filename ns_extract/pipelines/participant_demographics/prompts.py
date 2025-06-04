base_message = """
You will be provided with a text sample from a scientific journal.
The sample is delimited with triple backticks.

OBJECTIVE:
Extract participant demographic data from neuroimaging research with:
- Maximum accuracy and completeness
- Clear distinction between medical and non-medical groups
- Return null array if no groups mentioned

EXTRACTION RULES:

1. GROUP CATEGORIZATION:
   Primary Classification (group_name):
   - patients: ONLY for groups with documented medical/clinical conditions
   - healthy: ALL other groups including healthy comparisons, non-clinical participants,
     or study arms without medical conditions

   Medical Status (diagnosis):
   - INCLUDE: Clinical diagnoses, disorder subtypes, documented comorbidities
     - Example: "Major Depressive Disorder with Psychotic Features" ✓
   - EXCLUDE: Non-medical characteristics, study conditions, demographic categories
     - Example: "Video Game Players" ✗

   Descriptive Subgroup Names (subgroup_name):
   - Study Arms: "Placebo Group", "High-dose Cohort"
   - Participant Types: "Elite Athletes", "First-time Offenders"
   - Demographics: "Young Adult Females", "Rural Population"
   - Relationships: "Unaffected Siblings", "First-degree Relatives"
   - Life Circumstances: "Postpartum Mothers", "Pre-surgical Cases"

2. QUANTITATIVE DATA:
   Participant Counts:
   - Record final included numbers only
   - Exclude withdrawn/dropped participants

   Gender Distribution:
   - Extract explicit counts by gender
   - Do not calculate from percentages
   - Record as null if not directly stated

   Age Information:
   - Capture all reported metrics (min, max, mean, median, range)
   - Maintain original precision
   - Include units when specified
   - Do not compute missing values

3. QUALITY CONTROLS:
   Field Requirements:
   ✓ Use exact text for diagnoses and subgroup names
   ✓ Include only explicitly stated numbers
   ✓ Mark unclear/missing data as null
   ✗ No inferred or calculated values
   ✗ No assumptions about group characteristics

Text sample: ${text}

REQUIRED OUTPUT:
Return structured data matching schema format. Each field must contain only explicitly
stated information from text. Mark any ambiguous or missing data as null.
"""
