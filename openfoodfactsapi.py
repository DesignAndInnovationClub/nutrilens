import re
import requests




def parse_additives(additives_tags: list) -> list:
    """Converts OFF additive tags like 'en:e322' to 'INS 322' format."""
    parsed = []
    for tag in additives_tags:

        match = re.search(r"e(\d+[a-z]?)", tag.lower())
        if match:
            parsed.append(f"INS {match.group(1).upper()}")
    return parsed


def get_product_info(barcode: str) -> dict:
    url = f"https://world.openfoodfacts.net/api/v2/product/{barcode}"


    params = {
        "fields": (
            "product_name,brands,image_url,ingredients_text,ingredients,"
            "nutrition_grades,nova_group,nutriments,additives_tags"
        ),
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data.get("status") == 1:
            product = data.get("product", {})

            raw_ingredients_list = product.get("ingredients", [])
            ingredients_list = [
                ing.get("text")
                for ing in raw_ingredients_list
                if isinstance(ing, dict) and ing.get("text")
            ]

            raw_nutriments = product.get("nutriments", {})
            nutriments = {
                "energy_kcal": raw_nutriments.get(
                    "energy-kcal_100g", raw_nutriments.get("energy-kcal")
                ),
                "sugars": raw_nutriments.get("sugars_100g"),
                "fat": raw_nutriments.get("fat_100g"),
                "saturated_fat": raw_nutriments.get("saturated-fat_100g"),
                "protein": raw_nutriments.get("proteins_100g"),
                "salt": raw_nutriments.get("salt_100g"),
                "fiber": raw_nutriments.get("fiber_100g"),
            }

            
            product_data = {
                "product_name": product.get("product_name", "Unknown Product"),
                "brand": product.get("brands", "Unknown Brand"),
                "barcode": barcode,
                "image_url": product.get("image_url", ""),
                "ingredients": ingredients_list,
                "ingredients_text": product.get("ingredients_text", ""),
                "nutriscore_grade": product.get(
                    "nutrition_grades", "unknown"
                ).upper(),
                "nova_group": product.get("nova_group", "unknown"),
                "nutriments": nutriments,
                "additives": parse_additives(product.get("additives_tags", [])),
            }

            return product_data

    print(f"Product not found or error fetching data: {response.status_code}")
    return {}
