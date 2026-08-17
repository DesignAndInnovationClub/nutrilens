from dotenv import load_dotenv
import json
import os
import google.generativeai as genai
from analyser import build_rag_context

load_dotenv() 


genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-3.6-flash")


def analyze_product(
    product_data: dict, price: float = None, user_profile: dict = None
) -> dict:  
    """Analyzes a food product using Gemini API + RAG.

    Args:
        product_data: dict containing product details from Open Food Facts.
        price: Actual cost of the scanned product in INR (e.g., 180).
        user_profile: Dict with keys user_age, user_profile, and dietary_preference.

    Returns:
        Complete analysis dict from Gemini with attached product_meta.
    """


    product_name = product_data.get("product_name", "Unknown Product")
    brand = product_data.get("brand", "Unknown Brand")
    barcode = product_data.get("barcode", "")
    image_url = product_data.get("image_url", "")
    ingredients_list = product_data.get("ingredients", [])
    ingredients_text = product_data.get("ingredients_text", "")
    nutriscore = product_data.get("nutriscore_grade", "unknown")
    nova_group = product_data.get("nova_group", "unknown")
    nutriments = product_data.get("nutriments", {})
    additives = product_data.get("additives", [])

    price_str = f"₹{price}" if price else "Unknown / Not specified"


    has_ingredients = bool(ingredients_list or ingredients_text or additives)


    if has_ingredients:
        all_ingredients = ingredients_list + additives
        all_ingredients = [
            i for i in all_ingredients if str(i).strip()
        ]  
        rag = build_rag_context(all_ingredients)
        rag_context = rag.get("full_context", "")
    else:
        rag_context = ""

    if user_profile:
   
        user_age = user_profile.get("user_age", "Unknown")
        user_goal = user_profile.get("user_profile", "General Wellness")
     
        dietary_pref = user_profile.get("dietary_preference", user_profile.get("dietary_pref", "None"))
        
        profile_text = (
            f"Age: {user_age} years old\n"
            f"Health Profile: {user_goal}\n"
            f"Dietary Restrictions: {dietary_pref}"
        )
    else:
        profile_text = "Standard Adult Profile (No specific restrictions)"


    nutrition_block = (
        f"""
Energy:        {nutriments.get('energy_kcal', 'N/A')} kcal per 100g
Sugar:         {nutriments.get('sugars', 'N/A')}g per 100g
Fat:           {nutriments.get('fat', 'N/A')}g per 100g
Saturated fat: {nutriments.get('saturated_fat', 'N/A')}g per 100g
Protein:       {nutriments.get('protein', 'N/A')}g per 100g
Salt:          {nutriments.get('salt', 'N/A')}g per 100g
Fibre:         {nutriments.get('fiber', 'N/A')}g per 100g
""".strip()
        if nutriments
        else "Nutrition data not available"
    )

  
    prompt = f"""
You are the intelligence behind NutriScan — a personalized clinical nutritionist AI.

═══════════════════════════════════════════════════
PRODUCT
═══════════════════════════════════════════════════
Name:          {product_name}
Brand:         {brand}
Barcode:       {barcode}
Scanned Price: {price_str}

NUTRISCORE:    {str(nutriscore).upper()}
NOVA GROUP:    {nova_group}

NUTRITION (per 100g):
{nutrition_block}

INGREDIENTS TEXT:
{ingredients_text if ingredients_text else "Not available"}

ADDITIVES DETECTED:
{', '.join(additives) if additives else "None detected"}

═══════════════════════════════════════════════════
USER PROFILE
═══════════════════════════════════════════════════
{profile_text}

═══════════════════════════════════════════════════
REFERENCE DATABASE
═══════════════════════════════════════════════════
{rag_context if rag_context else "No database matches found — rely on standard food science."}

═══════════════════════════════════════════════════
YOUR TASK & RULES
═══════════════════════════════════════════════════
1. PERSONA ALIGNMENT (CRITICAL): You must evaluate the PRODUCT strictly through the lens of the USER PROFILE. What is considered "SAFE" for a young athlete might be "AVOID" for a senior diabetic. Tailor the one-liner, emotional_message, and verdicts directly to this user's age, restrictions, and health goals.
2. OVERALL VERDICT: Evaluate if this product is SAFE, CAUTION, or AVOID based on the user's profile and the ingredients.
3. CRITICAL RULE FOR ALTERNATIVES:
   - IF product verdict is "SAFE" (healthy / well to consume for THIS user): Set "budget_alternatives" to an empty list []. Do not suggest alternatives when the product is already a good match.
   - IF product verdict is "CAUTION" or "AVOID": Provide 2-3 healthier, cleaner alternatives priced around or below the product's scanned price ({price_str}).
4. ESTIMATED SCORES: If the provided Nutri-Score or NOVA group is missing or "UNKNOWN", calculate an estimated Nutri-Score (A-E) and NOVA group (1-4) based on the ingredients and nutrition data provided.
5. JSON FORMATTING (STRICT): Return ONLY valid, raw JSON. Do NOT wrap the JSON in Markdown formatting (do not use ```json). Do not leave trailing commas at the end of lists or dictionaries.

{{
  "score": <1.0 to 10.0 based on user profile compatibility>,
  "one_liner": "<one punchy honest sentence about this product tailored to the user profile>",
  "verdict": "<SAFE, AVOID CAUTION, or>",
  "ingredients_available": {str(has_ingredients).lower()},
  "emotional_message": "<2-3 realistic sentences on how this product specifically impacts the user's health goals>",
  "fun_fact": "<Generate 'Did a fact fascinating ingredients its know?' nutrition or product related short, specifically this to you>",
  "estimated_scores": {{
    "nutriscore": "<A, B, C, D, E or>",
    "nova_group": <1, 2, 3, or 4>
  }},
  "harmful_ingredients": [
    {{
      "name": "<ingredient name>",
      "plain_english": "<what it is>",
      "impact_on_you": "<how it affects THIS specific user profile>",
      "severity": "<HIGH, LOW MEDIUM, or>"
    }}
  ],
  "hidden_sugars": [],
  "nutrition_reality": {{
    "sugar_verdict": "<plain English on sugar content and its impact on the user>",
    "protein_verdict": "<plain English on protein content and its impact on the user>",
    "salt_verdict": "<plain English on salt content and its impact on the user>"
  }},
  "budget_alternatives": [
    {{
      "name": "<alternative item name>",
      "approx_cost": "<₹XX (close to or less than scanned price)>",
      "where_to_find": "<general store / supermarket / local shop>",
      "why_better": "<why it is a cleaner choice for this user>"
    }}
  ]
}}
"""

    generation_config = genai.types.GenerationConfig(
        temperature=0.3, max_output_tokens=2500, response_mime_type="application/json"
    )

   
    response = model.generate_content(
        prompt, generation_config=generation_config
    )
    raw = response.text.strip()

  
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        print("🚨 AI JSON FORMATTING ERROR 🚨")
        print(f"Error: {e}")
        print("Raw text from AI:")
        print(raw)
        
        
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end != 0:
            try:
                result = json.loads(raw[start:end])
            except Exception:
                result = {"verdict": "CAUTION", "one_liner": "AI parsing error occurred.", "budget_alternatives": []}
        else:
            result = {"verdict": "CAUTION", "one_liner": "AI parsing error occurred.", "budget_alternatives": []}


    result["product_meta"] = {
        "name": product_name,
        "brand": brand,
        "barcode": barcode,
        "price": price,
        "image_url": image_url,
        "nutriscore": str(nutriscore).upper(),
        "nova_group": nova_group,
        "nutriments": nutriments,
    }

    return result
