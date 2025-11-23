import streamlit as st
import datetime
from api_client import get_daily_log, get_recipes, log_food
import requests
from api_client import API_URL

st.set_page_config(
    page_title="Nutrition Tracker", 
    page_icon="🥦", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar styling
st.markdown("""
    <style>
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.05) 100%);
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 2rem;
    }
    
    /* Sidebar navigation styling */
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
    .big-metric {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
        padding: 1.5rem;
        border-radius: 16px;
        text-align: center;
        border: 1px solid rgba(250, 250, 250, 0.1);
    }
    .big-metric h2 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    .big-metric p {
        margin: 0.5rem 0 0 0;
        opacity: 0.7;
        font-size: 0.9rem;
    }
    .meal-card {
        background: rgba(255, 255, 255, 0.03);
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid rgba(250, 250, 250, 0.1);
        margin-bottom: 0.5rem;
    }
    .meal-card:hover {
        background: rgba(255, 255, 255, 0.05);
        border-color: rgba(250, 250, 250, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

st.title("🥦 Daily Food Logger")
st.markdown("##### Track your nutrition journey, one meal at a time")

# Fetch recipes once
all_recipes = get_recipes()

# Sidebar content
with st.sidebar:
    st.markdown("### 🎯 Quick Stats")
    st.markdown("")
    
    # Get today's stats
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    today_logs = get_daily_log(today_str)
    
    if today_logs:
        recipes = all_recipes
        recipe_dict = {r['id']: r for r in recipes}
        
        total_kcal = 0
        for entry in today_logs:
            recipe = recipe_dict.get(entry['recipe_id'])
            if recipe:
                multiplier = entry['serving_multiplier']
                if recipe['type'] == 'DIRECT':
                    nut = recipe.get('nutrition_direct', {})
                    total_kcal += nut.get('energy_kcal', 0) * multiplier
                else:
                    for ing_item in recipe.get('ingredients', []):
                        ing = ing_item.get('ingredient', {})
                        qty = ing_item['quantity']
                        factor = qty / 100.0
                        total_kcal += ing.get('energy_kcal_100g', 0) * factor * multiplier
        
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 1.5rem; 
                        border-radius: 12px; 
                        text-align: center;'>
                <h2 style='margin: 0; color: white;'>{total_kcal:.0f}</h2>
                <p style='margin: 0.5rem 0 0 0; color: rgba(255,255,255,0.9); font-size: 0.9rem;'>
                    🔥 Calories Today
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("")
        st.metric("📝 Meals Logged", len(today_logs))
    else:
        st.info("No meals logged today")
    
    st.markdown("---")
    st.markdown("### 📚 Navigation")
    st.markdown("""
        - 🏠 **Home** - Daily food logger
        - 📖 **Recipe Manager** - View & edit recipes
        - ✨ **AI Import** - Import from images
    """)
    
    st.markdown("---")
    st.markdown("##### 💡 Quick Tip")
    st.caption("Use AI Import to quickly create recipes from food photos!")

# Date Selector
col_date, col_spacer = st.columns([2, 3])
with col_date:
    selected_date = st.date_input("📅 Select Date", datetime.date.today())
date_str = selected_date.strftime("%Y-%m-%d")

st.markdown("---")

# 1. View Today's Log
st.markdown("### 📊 Today's Intake")
st.markdown("")

if date_str == today_str:
    logs = today_logs
else:
    logs = get_daily_log(date_str)

if logs:
    total_kcal = 0
    total_p = 0
    total_c = 0
    total_f = 0
    
    # Fetch all recipes to map nutrition
    recipes = all_recipes
    recipe_dict = {r['id']: r for r in recipes}
    
    # Display each meal entry
    for idx, entry in enumerate(logs, 1):
        recipe = recipe_dict.get(entry['recipe_id'])
        if not recipe:
            continue
            
        multiplier = entry['serving_multiplier']
        
        # Calculate nutrition based on recipe type
        if recipe['type'] == 'DIRECT':
            nut = recipe.get('nutrition_direct', {})
            kcal = nut.get('energy_kcal', 0) * multiplier
            prot = nut.get('protein_g', 0) * multiplier
            carb = nut.get('carbs_g', 0) * multiplier
            fat = nut.get('fat_g', 0) * multiplier
        else:
            # For GRANULAR, sum up ingredients
            kcal, prot, carb, fat = 0, 0, 0, 0
            for ing_item in recipe.get('ingredients', []):
                ing = ing_item.get('ingredient', {})
                qty = ing_item['quantity']
                factor = qty / 100.0
                kcal += ing.get('energy_kcal_100g', 0) * factor
                prot += ing.get('protein_g_100g', 0) * factor
                carb += ing.get('carbs_g_100g', 0) * factor
                fat += ing.get('fat_g_100g', 0) * factor
            kcal *= multiplier
            prot *= multiplier
            carb *= multiplier
            fat *= multiplier
        
        total_kcal += kcal
        total_p += prot
        total_c += carb
        total_f += fat
        
        # Display meal card
        st.markdown(f"""
        <div class='meal-card'>
            <h4 style='margin: 0 0 0.5rem 0;'>🍽️ {recipe['name']}</h4>
            <p style='margin: 0; opacity: 0.7; font-size: 0.9rem;'>
                {multiplier:.2f}x serving • 
                {kcal:.0f} kcal • 
                P: {prot:.1f}g • 
                C: {carb:.1f}g • 
                F: {fat:.1f}g
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Display totals
    st.markdown("")
    st.markdown("#### 📈 Daily Totals")
    tc1, tc2, tc3, tc4 = st.columns(4)
    
    tc1.markdown(f"""
        <div class='big-metric'>
            <h2 style='color: #ff6b6b;'>{total_kcal:.0f}</h2>
            <p>🔥 Total Calories</p>
        </div>
    """, unsafe_allow_html=True)
    
    tc2.markdown(f"""
        <div class='big-metric'>
            <h2 style='color: #4ecdc4;'>{total_p:.1f}g</h2>
            <p>💪 Protein</p>
        </div>
    """, unsafe_allow_html=True)
    
    tc3.markdown(f"""
        <div class='big-metric'>
            <h2 style='color: #ffe66d;'>{total_c:.1f}g</h2>
            <p>🌾 Carbs</p>
        </div>
    """, unsafe_allow_html=True)
    
    tc4.markdown(f"""
        <div class='big-metric'>
            <h2 style='color: #a8e6cf;'>{total_f:.1f}g</h2>
            <p>🥑 Fat</p>
        </div>
    """, unsafe_allow_html=True)
    
else:
    st.info("🍽️ No meals logged for this date. Start by logging a meal below!")

st.markdown("---")

# 2. Log New Food
st.markdown("### ➕ Log New Meal")
st.markdown("")

recipes = all_recipes
if not recipes:
    st.warning("⚠️ No recipes found. Create your first recipe in **Recipe Manager** or use **AI Import** to get started!")
else:
    recipe_map = {r['name']: r for r in recipes}
    
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_recipe_name = st.selectbox("🍽️ Select Recipe", list(recipe_map.keys()), help="Choose which recipe you ate")
    
    if selected_recipe_name:
        recipe = recipe_map[selected_recipe_name]
        
        with col2:
            recipe_type_badge = "🧱 GRANULAR" if recipe['type'] == 'GRANULAR' else "🍱 DIRECT"
            st.markdown(f"""
                <div style='padding: 1.5rem 0 0 0;'>
                    <span style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          padding: 0.4rem 0.8rem; 
                          border-radius: 12px; 
                          font-size: 0.85rem; 
                          font-weight: 600; 
                          color: white;'>
                        {recipe_type_badge}
                    </span>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("")
        st.info(f"📏 **Standard Serving:** {recipe['standard_serving_amount']} {recipe['standard_serving_unit']}")
        
        st.markdown("")
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            portion_type = st.radio("📊 Portion Method", ["Multiplier", "Custom Amount"], help="Choose how to specify portion size")
        
        multiplier = 1.0
        with col_right:
            if portion_type == "Multiplier":
                multiplier = st.slider("🔢 Serving Multiplier", 0.1, 5.0, 1.0, 0.1, help="E.g., 0.5 for half serving, 2.0 for double")
            else:
                custom_amount = st.number_input(
                    f"📏 Amount ({recipe['standard_serving_unit']})", 
                    value=float(recipe['standard_serving_amount']),
                    min_value=0.1,
                    help="Enter the exact amount you consumed"
                )
                if recipe['standard_serving_amount'] > 0:
                    multiplier = custom_amount / recipe['standard_serving_amount']
        
        # Preview nutrition
        st.markdown("")
        st.markdown("#### 🔍 Nutrition Preview")
        
        if recipe['type'] == 'DIRECT':
            nut = recipe.get('nutrition_direct', {})
            prev_kcal = nut.get('energy_kcal', 0) * multiplier
            prev_p = nut.get('protein_g', 0) * multiplier
            prev_c = nut.get('carbs_g', 0) * multiplier
            prev_f = nut.get('fat_g', 0) * multiplier
        else:
            prev_kcal, prev_p, prev_c, prev_f = 0, 0, 0, 0
            for ing_item in recipe.get('ingredients', []):
                ing = ing_item.get('ingredient', {})
                qty = ing_item['quantity']
                factor = qty / 100.0
                prev_kcal += ing.get('energy_kcal_100g', 0) * factor
                prev_p += ing.get('protein_g_100g', 0) * factor
                prev_c += ing.get('carbs_g_100g', 0) * factor
                prev_f += ing.get('fat_g_100g', 0) * factor
            prev_kcal *= multiplier
            prev_p *= multiplier
            prev_c *= multiplier
            prev_f *= multiplier
        
        pc1, pc2, pc3, pc4 = st.columns(4)
        pc1.metric("🔥 Calories", f"{prev_kcal:.0f}")
        pc2.metric("💪 Protein", f"{prev_p:.1f}g")
        pc3.metric("🌾 Carbs", f"{prev_c:.1f}g")
        pc4.metric("🥑 Fat", f"{prev_f:.1f}g")
        
        st.markdown("")
        if st.button("✨ Log This Meal", type="primary", use_container_width=True):
            res = log_food(recipe['id'], multiplier, date_str)
            if res.status_code == 200:
                st.success("✅ Meal logged successfully!")
                st.rerun()
            else:
                st.error(f"❌ Failed to log meal: {res.text}")

