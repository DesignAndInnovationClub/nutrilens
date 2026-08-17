import streamlit as st
from barcode_reader import barcode_scanner
from openfoodfactsapi import get_product_info
from rag import analyze_product  
1

st.set_page_config(page_title="NutriLens", page_icon="🥗", layout="wide")

if "profile_confirmed" not in st.session_state:
    st.session_state["profile_confirmed"] = False
if "active_barcode" not in st.session_state:
    st.session_state["active_barcode"] = None
if "analysis_ready" not in st.session_state:
    st.session_state["analysis_ready"] = False
if "scanned_price" not in st.session_state:
    st.session_state["scanned_price"] = 0

user_profile_data = {
                "user_age": st.session_state.get("user_age", "Unknown"),
                "user_profile": st.session_state.get("user_profile", "General Wellness"),
                "dietary_preference": st.session_state.get("dietary_preference", "None")
            }


def get_nutriscore_badge(grade) -> tuple[str, str, str]:
    grade_str = str(grade).upper() if grade else "UNKNOWN"
    mapping = {
        "A": ("A - Excellent", "Highest nutritional quality", "green"),
        "B": ("B - Good", "Good nutritional profile", "green"),
        "C": ("C - Average", "Balanced profile; fine in moderation", "orange"),
        "D": ("D - Poor", "High in sugar, saturated fat, or salt", "orange"),
        "E": ("E - Very Poor", "Unhealthy profile; high calories, sugars, bad fats", "red"),
    }
    return mapping.get(grade_str, ("Not Graded", "Evaluated by AI below.", "gray"))


def get_nova_badge(group) -> tuple[str, str]:
    try:
        grp = int(group)
    except (ValueError, TypeError):
        grp = 0
    mapping = {
        1: ("Group 1: Unprocessed", "Natural foods like fresh fruits, grains, nuts."),
        2: ("Group 2: Culinary Ingredients", "Oils, butter, sugar, salt used in cooking."),
        3: ("Group 3: Processed Foods", "Canned vegetables, cheeses, breads."),
        4: ("Group 4: Ultra-Processed (UPF)", "Industrial formulations with artificial additives."),
    }
    return mapping.get(grp, ("Unclassified Group", "Evaluated by AI below."))




def render_nutriscan_dashboard(data: dict):
    meta = data.get("product_meta", {})

    col_img, col_title = st.columns([1, 4])
    with col_img:
        if meta.get("image_url"):
            st.image(meta.get("image_url"), width=130)
        else:
            st.markdown("📷 *No image available*")

    with col_title:
        st.title(meta.get("name", "Product Analysis"))
        st.caption(f"**Brand:** {meta.get('brand')} | **Barcode:** `{meta.get('barcode')}` | **Price Entered:** ₹{st.session_state['scanned_price']}")

        off_nutri = meta.get("nutriscore")
        off_nova = meta.get("nova_group")

        valid_nutri = off_nutri and str(off_nutri).upper() in ["A", "B", "C", "D", "E"]
        valid_nova = off_nova and str(off_nova) in ["1", "2", "3", "4"]

        estimates = data.get("estimated_scores", {})
        

        final_nutri = off_nutri if valid_nutri else estimates.get("nutriscore", "UNKNOWN")
        final_nova = off_nova if valid_nova else estimates.get("nova_group", 0)

        score_label, score_desc, score_color = get_nutriscore_badge(final_nutri)
        nova_title, nova_desc = get_nova_badge(final_nova)

        col_badge1, col_badge2 = st.columns(2)
        with col_badge1:
            prefix = "🟢 **Nutri-Score:**" if valid_nutri else "🤖 **Nutri-Score:**"
            with st.popover(f"{prefix} :{score_color}[{score_label}]"):
                if not valid_nutri: st.warning("⚠️ *Nutriscore is evaluated using our own database and AI*")
                st.info(f"**Status:** {score_desc}")
                # --- ADD THIS LINE FOR NUTRI-SCORE RANGE ---
                st.caption("ℹ️ **Range Guide:** Grades from **A** (Highest quality) to **E** (Lowest quality).")

        with col_badge2:
            prefix2 = "⚙️ **NOVA Group:**" if valid_nova else "🤖 **NOVA Group:**"
            with st.popover(f"{prefix2} **{nova_title}**"):
                if not valid_nova: st.warning("⚠️ *Nova group is calculated using our own database and AI*")
                st.warning(f"**Status:** {nova_desc}")
                # --- ADD THIS LINE FOR NOVA RANGE ---
                st.caption("ℹ️ **Range Guide:** Levels from **Group 1** (Unprocessed) to **Group 4** (Ultra-Processed).")


    st.markdown("---")

    verdict = data.get("verdict", "UNKNOWN")
    score = data.get("score", 0.0)

    if verdict == "SAFE": st.success(f"### Verdict: {verdict} (Health Score: {score}/10)")
    elif verdict == "CAUTION": st.warning(f"### Verdict: {verdict} (Health Score: {score}/10)")
    else: st.error(f"### Verdict: {verdict} (Health Score: {score}/10)")

    st.markdown(f"👉 **Key Insight:** {data.get('one_liner')}")
    st.info(f"💡 **Summary:** {data.get('emotional_message')}")
    st.markdown("---")


    
    ai_fact = data.get("fun_fact", "Staying hydrated helps your body process nutrients more efficiently!")
    st.info(f"💡 **Did you know?** {ai_fact}")
    st.markdown("---")



    col_harm, col_nutr = st.columns([1, 1])
    with col_harm:
        st.subheader("⚠️ High Risk Additives & Ingredients")
        harmful = data.get("harmful_ingredients", [])
        if harmful:
            for item in harmful:
                severity = item.get("severity", "LOW")
                color = "red" if severity == "HIGH" else "orange"
                with st.container(border=True):
                    st.markdown(f"**:{color}[{item.get('name')}]** `[{severity}]`")
                    st.write(f"• **What it is:** {item.get('plain_english')}")
                    st.write(f"• **Impact:** {item.get('impact_on_you')}")
        else:
            st.success("✅ No high-risk chemical additives detected.")

    with col_nutr:
        st.subheader("📊 Nutrition Reality")
        nutr_reality = data.get("nutrition_reality", {})
        st.write(f"• **Sugar:** {nutr_reality.get('sugar_verdict')}")
        st.write(f"• **Protein:** {nutr_reality.get('protein_verdict')}")
        st.write(f"• **Salt:** {nutr_reality.get('salt_verdict')}")
        
    alternatives = data.get("budget_alternatives", [])
    if alternatives:
        st.markdown("---")
        st.subheader("💡 Healthier Budget Alternatives")
        alt_cols = st.columns(len(alternatives))
        for col, alt in zip(alt_cols, alternatives):
            with col:
                with st.container(border=True):
                    st.subheader(f"✨ {alt.get('name')}")
                    st.markdown(f"💰 **Estimated Cost:** `{alt.get('approx_cost')}`")
                    st.write(f"📍 **Availability:** {alt.get('where_to_find')}")
                    st.info(f"Why it's better: {alt.get('why_better')}")



st.sidebar.title("👤 1. Your Health Profile")

input_disabled = st.session_state["profile_confirmed"]

user_age = st.sidebar.number_input(
    "Age", min_value=5, max_value=100, value=25, step=1, disabled=input_disabled
)

profile_preset = st.sidebar.selectbox(
    "Primary Dietary Focus",
    [
        "Balanced Everyday Diet",
        "High Protein / Muscle Build",
        "Weight Management",
        "Low Sugar / Diabetic Care",
        "Clean Label / Minimally Processed",
        "Child Safe (Low Additives)",
        "Budget Friendly",
    ],
    disabled=input_disabled
)

st.sidebar.markdown("---")
st.sidebar.subheader("Dietary Restrictions & Allergies")
is_vegetarian = st.sidebar.checkbox("🌱 Vegetarian / Vegan", disabled=input_disabled)
is_diabetic = st.sidebar.checkbox("🩸 Diabetic / Insulin Sensitive", disabled=input_disabled)
is_asthmatic = st.sidebar.checkbox("🫁 Sulphite Sensitive (Asthma)", disabled=input_disabled)
is_lactose = st.sidebar.checkbox("🥛 Lactose Sensitive", disabled=input_disabled)

if not st.session_state["profile_confirmed"]:
    if st.sidebar.button("✅ Confirm Profile & Continue", type="primary", use_container_width=True):

        st.session_state["user_profile"] = {
            "age": user_age,
            "preset": profile_preset,
            "gym_going": profile_preset == "High Protein / Muscle Build",
            "weight_loss": profile_preset == "Weight Management",
            "student_budget": profile_preset == "Budget Friendly",
            "clean_eater": profile_preset == "Clean Label / Minimally Processed",
            "for_children": profile_preset == "Child Safe (Low Additives)" or user_age < 16,
            "diabetic": is_diabetic or profile_preset == "Low Sugar / Diabetic Care",
            "vegetarian": is_vegetarian,
            "asthmatic": is_asthmatic,
            "lactose_intolerant": is_lactose,
        }
        st.session_state["profile_confirmed"] = True
        st.rerun()
else:
    if st.sidebar.button("✏️ Edit Profile", use_container_width=True):
        st.session_state["profile_confirmed"] = False
        st.session_state["active_barcode"] = None
        st.session_state["analysis_ready"] = False
        st.rerun()


st.title("🥗 NutriLens-Scan. Know. Eat")

if not st.session_state["profile_confirmed"]:
    st.info("👈 **Welcome to NutriLens !** \n\nPlease configure your health goals and dietary restrictions in the sidebar, then click **Confirm Profile & Continue** to activate the scanner.")

elif not st.session_state["active_barcode"]:
    st.markdown("### Step 2: Product Identification")
    
    input_method = st.radio(
        "Select Input Method:",
        ["📷 Camera Scanner", "⌨️ Manual Barcode Input"],
        horizontal=True
    )
    
    if input_method == "📷 Camera Scanner":
        st.info("Point your camera at the product's barcode.")
        scanned_val = barcode_scanner()
        if scanned_val:
            st.session_state["active_barcode"] = str(scanned_val).strip()
            st.rerun()
            
    elif input_method == "⌨️ Manual Barcode Input":
    
        manual_input = st.text_input("Enter Barcode Number", placeholder="e.g. 8901764012914")
        if st.button("Proceed with Manual Barcode"):
            if manual_input.strip():
                st.session_state["active_barcode"] = manual_input.strip()
                st.rerun()


elif st.session_state["active_barcode"] and not st.session_state["analysis_ready"]:
    st.success(f"✅ Product Identified: **{st.session_state['active_barcode']}**")
    st.markdown("### Step 3: Enter Price")
    
    with st.container(border=True):
        st.write("To provide accurate, budget-friendly alternatives, please enter the retail price.")
        entered_price = st.number_input("Retail Price (₹)", min_value=1, max_value=5000, value=50, step=10)
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🚀 Initiate Analysis", type="primary"):
                st.session_state["scanned_price"] = entered_price
                st.session_state["analysis_ready"] = True
                st.rerun()
        with col2:
            if st.button("Cancel & Scan Another"):
                st.session_state["active_barcode"] = None
                st.rerun()


elif st.session_state["active_barcode"] and st.session_state["analysis_ready"]:
    
    if st.button("🔄 Scan a New Product"):
        st.session_state["active_barcode"] = None
        st.session_state["analysis_ready"] = False
        st.rerun()

    st.markdown("---")
    active = st.session_state["active_barcode"]

    with st.spinner("Retrieving product data from the global database..."):
        product_data = get_product_info(active)

    if not product_data:
        st.error("⚠️ Product not found in database. Please verify the barcode and try again.")
    else:
        with st.spinner("Analyzing ingredients with AI..."):
            analysis_result = analyze_product(
                product_data=product_data,
                price=st.session_state["scanned_price"],
                user_profile=user_profile_data,
            )

        render_nutriscan_dashboard(analysis_result)

st.markdown("---")
st.caption(
    "**⚖️ Disclaimer:** NutriLens is designed for educational and informational "
    "purposes only and does not constitute professional medical advice, diagnosis, "
    "or treatment. Nutritional data is retrieved from Open Food Facts, a crowdsourced "
    "database, and may contain inaccuracies or outdated recipe information. AI-generated "
    "evaluations are estimations based on provided ingredients and should not be used as a "
    "definitive scientific or medical assessment. Always verify information on the physical "
    "product packaging and consult a qualified healthcare provider before making significant "
    "changes to your diet."
)