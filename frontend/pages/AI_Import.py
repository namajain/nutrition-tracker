import streamlit as st
from api_client import analyze_image, create_recipe

st.set_page_config(page_title="AI Import", page_icon="✨", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.05) 100%);
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 2rem;
    }
    
    [data-testid="stSidebarNav"] {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        padding: 1rem 0.5rem;
        margin: 0 0.5rem;
    }
    
    [data-testid="stSidebarNav"] a {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        border: 1px solid rgba(250, 250, 250, 0.05);
        transition: all 0.3s;
    }
    
    [data-testid="stSidebarNav"] a:hover {
        background: rgba(102, 126, 234, 0.2);
        border-color: rgba(102, 126, 234, 0.4);
        transform: translateX(5px);
    }
    
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%);
        border-color: rgba(102, 126, 234, 0.5);
        font-weight: 600;
    }
    
    .upload-section {
        background: rgba(102, 126, 234, 0.05);
        border: 2px dashed rgba(102, 126, 234, 0.3);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

st.title("✨ AI Recipe Import")
st.markdown("##### Upload a food photo and let AI create your recipe")

st.markdown("")
st.markdown("### 📸 Upload Image")
uploaded_file = st.file_uploader("Choose a meal photo", type=["jpg", "jpeg", "png"], help="Upload a clear photo of your meal")

if "ai_draft" not in st.session_state:
    st.session_state.ai_draft = None

if uploaded_file:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
    with col2:
        st.markdown("### 🔍 Analysis")
        if st.button("🚀 Analyze with AI", type="primary", use_container_width=True):
            with st.spinner("✨ Analyzing your meal..."):
                res = analyze_image(uploaded_file, uploaded_file.type)
                if res.status_code == 200:
                    st.session_state.ai_draft = res.json()
                    st.success("✅ Analysis complete!")
                else:
                    st.error(f"❌ Analysis failed: {res.text}")

if st.session_state.ai_draft:
    st.markdown("---")
    st.markdown("### ✏️ Review & Edit Draft")
    st.markdown("")
    
    draft = st.session_state.ai_draft
    
    with st.form("confirm_recipe"):
        name = st.text_input("📝 Recipe Name", value=draft.get("name", "New Recipe"), placeholder="Give your recipe a name")
        
        # Edit ingredients
        ingredients = draft.get("ingredients", [])
        updated_ingredients = []
        
        st.markdown("#### 🥗 Ingredients")
        st.caption("Review and adjust AI-detected ingredients")
        for i, ing in enumerate(ingredients):
            st.markdown(f"**Ingredient {i+1}**")
            c1, c2, c3 = st.columns([3, 1, 1])
            i_name = c1.text_input(f"Name", value=ing['name'], key=f"name_{i}")
            i_qty = c2.number_input(f"Qty ({ing['unit']})", value=float(ing['quantity']), key=f"qty_{i}")
            i_unit = c3.text_input(f"Unit", value=ing['unit'], key=f"unit_{i}")
            
            # Expose nutrition per 100g
            with st.expander(f"📊 Nutrition per 100g for {i_name}"):
                nut = ing.get("nutrition_per_100g", {})
                n1, n2, n3, n4 = st.columns(4)
                i_kcal = n1.number_input(f"🔥 Kcal", value=float(nut.get("energy_kcal", 0.0)), key=f"kcal_{i}")
                i_prot = n2.number_input(f"💪 Protein (g)", value=float(nut.get("protein_g", 0.0)), key=f"prot_{i}")
                i_carb = n3.number_input(f"🌾 Carbs (g)", value=float(nut.get("carbs_g", 0.0)), key=f"carb_{i}")
                i_fat = n4.number_input(f"🥑 Fat (g)", value=float(nut.get("fat_g", 0.0)), key=f"fat_{i}")
            
            updated_ingredients.append({
                "ingredient_name": i_name,
                "quantity": i_qty,
                "unit": i_unit,
                "nutrition_per_100g": {
                    "energy_kcal": i_kcal,
                    "protein_g": i_prot,
                    "carbs_g": i_carb,
                    "fat_g": i_fat
                }
            })
        
        st.markdown("---")
        st.markdown("#### 💾 Save Options")
        save_type = st.radio("📂 Save Mode", ["Granular (Editable Ingredients)", "Direct (Final Nutrition Only)"], help="Granular keeps ingredients separate, Direct saves only total nutrition")
        
        if st.form_submit_button("✨ Save Recipe", type="primary", use_container_width=True):
            payload = {
                "name": name,
                "type": "GRANULAR",
                "standard_serving_amount": 1.0,
                "standard_serving_unit": "meal",
                "ingredients": updated_ingredients
            }
            
            res = create_recipe(payload)
            if res.status_code == 200:
                recipe_id = res.json()['id']
                if save_type.startswith("Direct"):
                    # Trigger flatten
                    import requests
                    from api_client import API_URL
                    requests.post(f"{API_URL}/recipes/{recipe_id}/flatten")
                
                st.success("✅ Recipe saved successfully!")
                st.session_state.ai_draft = None
                st.rerun()
            else:
                st.error(f"❌ Failed to save: {res.text}")
