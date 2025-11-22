import streamlit as st
from api_client import get_recipes, create_recipe, update_recipe, delete_recipe
import requests
import pandas as pd
from api_client import API_URL

st.set_page_config(page_title="Recipe Manager", page_icon="📖", layout="wide", initial_sidebar_state="expanded")

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
    
    /* Main content styling */
    .main > div {
        padding-top: 2rem;
    }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    div[data-testid="stExpander"] {
        border: 1px solid rgba(250, 250, 250, 0.1);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.02);
        margin-bottom: 1rem;
    }
    div[data-testid="stExpander"]:hover {
        border-color: rgba(250, 250, 250, 0.2);
        background: rgba(255, 255, 255, 0.04);
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📖 Recipe Manager")
st.markdown("##### Manage your recipes with ease")

tab1, tab2 = st.tabs(["View & Edit", "Create New"])

with tab1:
    recipes = get_recipes()
    if not recipes:
        st.info("🔍 No recipes found. Create your first recipe in the **Create New** tab or use **AI Import**!")
    
    for r in recipes:
        icon = "🧱" if r['type'] == 'GRANULAR' else "🍱"
        label = f"{icon} {r['name']} • {r['type']}"
        
        with st.expander(label, expanded=False):
            st.markdown("---")
            # Header Edits
            st.markdown("##### 📝 Recipe Details")
            c1, c2, c3 = st.columns([2, 1, 1])
            new_name = c1.text_input("📌 Name", r['name'], key=f"name_{r['id']}")
            new_amt = c2.number_input("📊 Serving Amount", value=float(r['standard_serving_amount']), key=f"amt_{r['id']}", min_value=0.1)
            new_unit = c3.text_input("📏 Serving Unit", value=r['standard_serving_unit'], key=f"unit_{r['id']}")
            
            new_ingredients = []
            new_kcal, new_prot, new_carb, new_fat = 0, 0, 0, 0

            st.markdown("")
            
            if r['type'] == 'DIRECT':
                st.markdown("##### 🍽️ Nutrition (Per Standard Serving)")
                n = r.get('nutrition_direct') or {}
                ec1, ec2, ec3, ec4 = st.columns(4)
                new_kcal = ec1.number_input("🔥 Kcal", value=float(n.get('energy_kcal', 0)), key=f"dk_{r['id']}", min_value=0.0)
                new_prot = ec2.number_input("💪 Protein (g)", value=float(n.get('protein_g', 0)), key=f"dp_{r['id']}", min_value=0.0)
                new_carb = ec3.number_input("🌾 Carbs (g)", value=float(n.get('carbs_g', 0)), key=f"dc_{r['id']}", min_value=0.0)
                new_fat = ec4.number_input("🥑 Fat (g)", value=float(n.get('fat_g', 0)), key=f"df_{r['id']}", min_value=0.0)
            else:
                st.markdown("##### 🥗 Ingredients & Nutrition")
                st.caption("Edit quantities and units directly in the table below")
                
                current_ingredients = r.get('ingredients', [])
                
                # Create a lookup map for nutrition to avoid passing objects through data_editor (which can stringify them)
                # Key: Ingredient Name -> Value: Nutrition Dict
                nut_lookup = {}
                
                df_data = []
                for item in current_ingredients:
                    ing = item.get('ingredient', {})
                    name = ing.get('name', '')
                    
                    # Store 100g nutrition in map
                    nut_lookup[name] = {
                        "energy_kcal": ing.get('energy_kcal_100g', 0),
                        "protein_g": ing.get('protein_g_100g', 0),
                        "carbs_g": ing.get('carbs_g_100g', 0),
                        "fat_g": ing.get('fat_g_100g', 0)
                    }
                    
                    # Calculate per-row nutrition for initial display
                    factor = float(item['quantity']) / 100.0
                    nut_100g = nut_lookup[name]

                    df_data.append({
                        "Ingredient": name,
                        "Qty": float(item['quantity']),
                        "Unit": item['unit'],
                        "Kcal": round(nut_100g['energy_kcal'] * factor), 
                        "Protein (g)": round(nut_100g['protein_g'] * factor, 1),
                        "Carbs (g)": round(nut_100g['carbs_g'] * factor, 1),
                        "Fat (g)": round(nut_100g['fat_g'] * factor, 1)
                    })
                
                df = pd.DataFrame(df_data)
                
                edited_df = st.data_editor(
                    df,
                    column_config={
                        "Ingredient": st.column_config.TextColumn("Ingredient", disabled=True),
                        "Qty": st.column_config.NumberColumn("Qty", min_value=0.0, format="%.2f"),
                        "Unit": st.column_config.TextColumn("Unit"),
                        "Kcal": st.column_config.NumberColumn("Kcal", disabled=True),
                        "Protein (g)": st.column_config.NumberColumn("Protein (g)", disabled=True),
                        "Carbs (g)": st.column_config.NumberColumn("Carbs (g)", disabled=True),
                        "Fat (g)": st.column_config.NumberColumn("Fat (g)", disabled=True)
                    },
                    hide_index=True,
                    key=f"editor_{r['id']}",
                    num_rows="dynamic"
                )

                # Calculate Live Totals using the LOOKUP map, not hidden columns
                t_kcal, t_p, t_c, t_f = 0, 0, 0, 0
                
                for _, row in edited_df.iterrows():
                    name = row['Ingredient']
                    qty = row['Qty']
                    unit = row['Unit']
                    
                    # Fallback if something weird happens and name is missing (shouldn't since disabled)
                    nut = nut_lookup.get(name, {"energy_kcal": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0})
                    
                    f = qty / 100.0
                    
                    t_kcal += float(nut.get('energy_kcal', 0) or 0) * f
                    t_p += float(nut.get('protein_g', 0) or 0) * f
                    t_c += float(nut.get('carbs_g', 0) or 0) * f
                    t_f += float(nut.get('fat_g', 0) or 0) * f
                    
                    new_ingredients.append({
                        "ingredient_name": name,
                        "quantity": qty,
                        "unit": unit,
                        "nutrition_per_100g": nut
                    })
                
                st.markdown("")
                st.markdown("##### 📊 Live Nutrition Totals")
                tc1, tc2, tc3, tc4 = st.columns(4)
                tc1.markdown(f"<div class='metric-card'><h4 style='color: #ff6b6b; margin: 0;'>{t_kcal:.0f}</h4><p style='margin: 0; font-size: 0.85rem; opacity: 0.7;'>🔥 Calories</p></div>", unsafe_allow_html=True)
                tc2.markdown(f"<div class='metric-card'><h4 style='color: #4ecdc4; margin: 0;'>{t_p:.1f}g</h4><p style='margin: 0; font-size: 0.85rem; opacity: 0.7;'>💪 Protein</p></div>", unsafe_allow_html=True)
                tc3.markdown(f"<div class='metric-card'><h4 style='color: #ffe66d; margin: 0;'>{t_c:.1f}g</h4><p style='margin: 0; font-size: 0.85rem; opacity: 0.7;'>🌾 Carbs</p></div>", unsafe_allow_html=True)
                tc4.markdown(f"<div class='metric-card'><h4 style='color: #a8e6cf; margin: 0;'>{t_f:.1f}g</h4><p style='margin: 0; font-size: 0.85rem; opacity: 0.7;'>🥑 Fat</p></div>", unsafe_allow_html=True)

            # Footer Actions
            st.markdown("---")
            ac1, ac2, ac3 = st.columns([1.2, 1.2, 2])
            
            if ac1.button("💾 Save Changes", key=f"save_{r['id']}", type="primary"):
                payload = {
                    "name": new_name,
                    "type": r['type'],
                    "standard_serving_amount": new_amt,
                    "standard_serving_unit": new_unit,
                    "nutrition_direct": {
                        "energy_kcal": new_kcal, "protein_g": new_prot, "carbs_g": new_carb, "fat_g": new_fat
                    } if r['type'] == 'DIRECT' else None,
                    "ingredients": new_ingredients
                }
                res = update_recipe(r['id'], payload)
                if res.status_code == 200:
                    st.success("✅ Recipe updated successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Update failed: {res.text}")

            if r['type'] == 'GRANULAR':
                if ac2.button("🔄 Flatten to Direct", key=f"flat_{r['id']}"):
                    requests.post(f"{API_URL}/recipes/{r['id']}/flatten")
                    st.success("✅ Converted to Direct recipe!")
                    st.rerun()
            else:
                ac2.markdown("")
            
            if ac3.button("🗑️ Delete Recipe", key=f"del_{r['id']}", help="Permanently delete this recipe"):
                res = delete_recipe(r['id'])
                if res.status_code == 200:
                    st.success("✅ Recipe deleted!")
                    st.rerun()
                else:
                    st.error("❌ Failed to delete recipe.")

with tab2:
    st.markdown("##### ➕ Create New Recipe")
    st.markdown("")
    
    r_type = st.selectbox("📋 Recipe Type", ["DIRECT", "GRANULAR"], help="Direct: Enter total nutrition. Granular: Build from ingredients.")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    name = col1.text_input("🍽️ Recipe Name", placeholder="e.g., Chicken Salad")
    srv_amt = col2.number_input("📊 Serving Amount", value=1.0, min_value=0.1)
    srv_unit = col3.text_input("📏 Unit", value="serving", placeholder="e.g., bowl, cup")
    
    if r_type == "DIRECT":
        st.markdown("")
        st.markdown("##### 🍽️ Nutrition per Standard Serving")
        c1, c2, c3, c4 = st.columns(4)
        kcal = c1.number_input("🔥 Kcal", value=0, min_value=0)
        prot = c2.number_input("💪 Protein (g)", value=0.0, min_value=0.0)
        carbs = c3.number_input("🌾 Carbs (g)", value=0.0, min_value=0.0)
        fat = c4.number_input("🥑 Fat (g)", value=0.0, min_value=0.0)
        
        st.markdown("")
        if st.button("✨ Create Direct Recipe", type="primary", use_container_width=True):
            if not name:
                st.error("❌ Please enter a recipe name")
            else:
                payload = {
                    "name": name,
                    "type": "DIRECT",
                    "standard_serving_amount": srv_amt,
                    "standard_serving_unit": srv_unit,
                    "nutrition_direct": {
                        "energy_kcal": kcal, "protein_g": prot, "carbs_g": carbs, "fat_g": fat
                    },
                    "ingredients": []
                }
                res = create_recipe(payload)
                if res.status_code == 200:
                    st.success("✅ Recipe created successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Error: {res.text}")
                
    else:
        st.markdown("")
        st.info("💡 **Tip:** For Granular recipes, use the **AI Import** page for the best experience! Simply upload a photo and let AI identify ingredients and nutrition.")
        st.markdown("Manual granular creation requires selecting ingredients one by one, which is not yet fully implemented in this interface.")
