import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import json
import plotly.graph_objects as go
import plotly.express as px
import math

# Page Configuration
st.set_page_config(
    page_title="Commodities Trading Converter",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'conversion_history' not in st.session_state:
    st.session_state.conversion_history = []
if 'bookmarks' not in st.session_state:
    st.session_state.bookmarks = []
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'auto_calculate' not in st.session_state:
    st.session_state.auto_calculate = True
if 'wizard_mode' not in st.session_state:
    st.session_state.wizard_mode = False

# Dark/Light Mode Styling
def get_theme_styles():
    if st.session_state.dark_mode:
        return """
        <style>
            .stApp {
                background-color: #0e1117;
                color: #fafafa;
            }
            .main-header {
                font-size: 3rem;
                font-weight: bold;
                color: #64b5f6;
                text-align: center;
                margin-bottom: 2rem;
            }
            .metric-card {
                background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 100%);
                padding: 1.5rem;
                border-radius: 1rem;
                margin: 0.5rem 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }
            .conversion-result {
                background: linear-gradient(135deg, #065f46 0%, #059669 100%);
                padding: 2rem;
                border-radius: 1rem;
                border-left: 4px solid #10b981;
                margin: 1rem 0;
                box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            }
            .sticky-result {
                position: fixed;
                top: 10px;
                right: 10px;
                z-index: 1000;
                background: linear-gradient(135deg, #065f46 0%, #059669 100%);
                padding: 1rem;
                border-radius: 0.5rem;
                box-shadow: 0 4px 15px rgba(0,0,0,0.4);
                max-width: 300px;
            }
            .bookmark-card {
                background: linear-gradient(135deg, #7c2d12 0%, #dc2626 100%);
                padding: 1rem;
                border-radius: 0.5rem;
                margin: 0.5rem 0;
                cursor: pointer;
            }
            .history-item {
                background: linear-gradient(135deg, #374151 0%, #4b5563 100%);
                padding: 1rem;
                border-radius: 0.5rem;
                margin: 0.5rem 0;
                border-left: 3px solid #6366f1;
            }
        </style>
        """
    else:
        return """
        <style>
            .main-header {
                font-size: 3rem;
                font-weight: bold;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-align: center;
                margin-bottom: 2rem;
            }
            .metric-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1.5rem;
                border-radius: 1rem;
                margin: 0.5rem 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                color: white;
            }
            .conversion-result {
                background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
                padding: 2rem;
                border-radius: 1rem;
                border-left: 4px solid #10b981;
                margin: 1rem 0;
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                animation: fadeIn 0.5s ease-in;
            }
            .sticky-result {
                position: fixed;
                top: 10px;
                right: 10px;
                z-index: 1000;
                background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
                padding: 1rem;
                border-radius: 0.5rem;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                max-width: 300px;
            }
            .bookmark-card {
                background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
                padding: 1rem;
                border-radius: 0.5rem;
                margin: 0.5rem 0;
                cursor: pointer;
                transition: transform 0.2s;
            }
            .bookmark-card:hover {
                transform: translateY(-2px);
            }
            .history-item {
                background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
                padding: 1rem;
                border-radius: 0.5rem;
                margin: 0.5rem 0;
                border-left: 3px solid #6366f1;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
        </style>
        """

st.markdown(get_theme_styles(), unsafe_allow_html=True)

# Commodity Data
COMMODITY_DATA = {
    "Oil & Liquids": {
        "Brent Crude": {"density": 0.825, "api_gravity": 38.3, "units": ["barrels", "metric tons", "gallons", "liters"]},
        "WTI Crude": {"density": 0.827, "api_gravity": 37.9, "units": ["barrels", "metric tons", "gallons", "liters"]},
        "Gasoline": {"density": 0.74, "api_gravity": 60, "units": ["barrels", "metric tons", "gallons", "liters"]},
        "Diesel": {"density": 0.85, "api_gravity": 35, "units": ["barrels", "metric tons", "gallons", "liters"]},
        "Jet Fuel": {"density": 0.8, "api_gravity": 45, "units": ["barrels", "metric tons", "gallons", "liters"]},
        "Heating Oil": {"density": 0.87, "api_gravity": 31, "units": ["barrels", "metric tons", "gallons", "liters"]}
    },
    "Natural Gas": {
        "Natural Gas": {"density": 0.717, "calorific_value": 38.7, "units": ["mcf", "bcf", "mmbtu", "therms", "cubic_meters"]},
        "LNG": {"density": 0.45, "calorific_value": 55, "units": ["metric tons", "cubic_meters", "mmbtu", "gallons"]}
    },
    "Coal": {
        "Thermal Coal": {"density": 1.3, "calorific_value": 6000, "units": ["metric tons", "short tons", "mmbtu", "kcal"]},
        "Coking Coal": {"density": 1.35, "calorific_value": 7000, "units": ["metric tons", "short tons", "mmbtu", "kcal"]},
        "Anthracite": {"density": 1.4, "calorific_value": 8000, "units": ["metric tons", "short tons", "mmbtu", "kcal"]}
    },
    "Agricultural": {
        "Wheat": {"density": 0.78, "moisture_content": 13.5, "units": ["bushels", "metric tons", "pounds", "kilograms"]},
        "Corn": {"density": 0.72, "moisture_content": 15.5, "units": ["bushels", "metric tons", "pounds", "kilograms"]},
        "Soybeans": {"density": 0.77, "moisture_content": 13.0, "units": ["bushels", "metric tons", "pounds", "kilograms"]},
        "Rice": {"density": 0.75, "moisture_content": 14.0, "units": ["bushels", "metric tons", "pounds", "kilograms"]},
        "Sugar": {"density": 0.8, "moisture_content": 0.1, "units": ["metric tons", "pounds", "kilograms"]}
    },
    "Power/Electricity": {
        "Electricity": {"units": ["mwh", "kwh", "gwh", "mmbtu", "therms"]}
    }
}

# Predefined Scenarios
SCENARIOS = {
    "Typical Jet Fuel Trade": {
        "category": "Oil & Liquids",
        "commodity": "Jet Fuel",
        "from_unit": "barrels",
        "to_unit": "metric tons",
        "value": 1000
    },
    "Natural Gas Pipeline Delivery": {
        "category": "Natural Gas",
        "commodity": "Natural Gas",
        "from_unit": "mcf",
        "to_unit": "mmbtu",
        "value": 10000
    },
    "Wheat Export Deal": {
        "category": "Agricultural",
        "commodity": "Wheat",
        "from_unit": "bushels",
        "to_unit": "metric tons",
        "value": 5000
    },
    "Coal Power Plant": {
        "category": "Coal",
        "commodity": "Thermal Coal",
        "from_unit": "metric tons",
        "to_unit": "mmbtu",
        "value": 1000
    }
}

# Unit Conversions
UNIT_CONVERSIONS = {
    "barrels": 0.158987,
    "gallons": 0.00378541,
    "liters": 0.001,
    "metric tons": 1.0,
    "short tons": 0.907185,
    "pounds": 0.000453592,
    "kilograms": 0.001,
    "bushels": {"wheat": 27.2155, "corn": 25.4012, "soybeans": 27.2155, "rice": 20.4124},
    "mcf": 28.3168,
    "bcf": 28316846.6,
    "mmbtu": 1.05506,
    "therms": 0.105506,
    "cubic_meters": 1.0,
    "mwh": 3.6,
    "kwh": 0.0036,
    "gwh": 3600,
    "kcal": 4.184e-6
}

# Currency Data
CURRENCY_DATA = {
    "USD": {"region": "USA", "symbol": "$"},
    "EUR": {"region": "Europe", "symbol": "€"},
    "GBP": {"region": "United Kingdom", "symbol": "£"},
    "JPY": {"region": "Japan", "symbol": "¥"},
    "CAD": {"region": "Canada", "symbol": "C$"},
    "AUD": {"region": "Australia", "symbol": "A$"},
    "CHF": {"region": "Switzerland", "symbol": "CHF"},
    "CNY": {"region": "China", "symbol": "¥"},
    "INR": {"region": "India", "symbol": "₹"},
    "BRL": {"region": "Brazil", "symbol": "R$"},
    "RUB": {"region": "Russia", "symbol": "₽"},
    "MXN": {"region": "Mexico", "symbol": "$"}
}

# Utility Functions
def calculate_density_from_api(api_gravity):
    """Calculate density from API gravity"""
    return 141.5 / (131.5 + api_gravity)

def calculate_api_from_density(density):
    """Calculate API gravity from density"""
    return 141.5 / density - 131.5

def convert_oil_units(value, from_unit, to_unit, density=None, api_gravity=None):
    if density is None and api_gravity is not None:
        density = calculate_density_from_api(api_gravity)
    elif density is None:
        density = 0.85
    
    if from_unit == "barrels":
        cubic_meters = value * UNIT_CONVERSIONS["barrels"]
    elif from_unit == "gallons":
        cubic_meters = value * UNIT_CONVERSIONS["gallons"]
    elif from_unit == "liters":
        cubic_meters = value * UNIT_CONVERSIONS["liters"]
    elif from_unit == "metric tons":
        cubic_meters = value / density
    else:
        cubic_meters = value
    
    if to_unit == "barrels":
        return cubic_meters / UNIT_CONVERSIONS["barrels"]
    elif to_unit == "gallons":
        return cubic_meters / UNIT_CONVERSIONS["gallons"]
    elif to_unit == "liters":
        return cubic_meters / UNIT_CONVERSIONS["liters"]
    elif to_unit == "metric tons":
        return cubic_meters * density
    else:
        return cubic_meters

def convert_gas_units(value, from_unit, to_unit, calorific_value=None):
    if calorific_value is None:
        calorific_value = 38.7
    
    if from_unit == "mcf":
        cubic_meters = value * UNIT_CONVERSIONS["mcf"]
    elif from_unit == "bcf":
        cubic_meters = value * UNIT_CONVERSIONS["bcf"]
    elif from_unit == "mmbtu":
        cubic_meters = value * 1000 / calorific_value
    elif from_unit == "therms":
        cubic_meters = value * 100 / calorific_value
    else:
        cubic_meters = value
    
    if to_unit == "mcf":
        return cubic_meters / UNIT_CONVERSIONS["mcf"]
    elif to_unit == "bcf":
        return cubic_meters / UNIT_CONVERSIONS["bcf"]
    elif to_unit == "mmbtu":
        return cubic_meters * calorific_value / 1000
    elif to_unit == "therms":
        return cubic_meters * calorific_value / 100
    else:
        return cubic_meters

def convert_agricultural_units(value, from_unit, to_unit, commodity, moisture_content=None):
    commodity_lower = commodity.lower()
    
    moisture_factor = 1.0
    if moisture_content is not None:
        standard_moisture = COMMODITY_DATA["Agricultural"][commodity]["moisture_content"]
        moisture_factor = (100 - standard_moisture) / (100 - moisture_content)
    
    if from_unit == "bushels":
        if commodity_lower in UNIT_CONVERSIONS["bushels"]:
            kg = value * UNIT_CONVERSIONS["bushels"][commodity_lower] * moisture_factor
        else:
            kg = value * 25.4
    elif from_unit == "metric tons":
        kg = value * 1000
    elif from_unit == "pounds":
        kg = value * 0.453592
    else:
        kg = value
    
    if to_unit == "bushels":
        if commodity_lower in UNIT_CONVERSIONS["bushels"]:
            return kg / (UNIT_CONVERSIONS["bushels"][commodity_lower] * moisture_factor)
        else:
            return kg / 25.4
    elif to_unit == "metric tons":
        return kg / 1000
    elif to_unit == "pounds":
        return kg / 0.453592
    else:
        return kg

def convert_power_units(value, from_unit, to_unit):
    if from_unit in ["mwh", "kwh", "gwh"]:
        gj = value * UNIT_CONVERSIONS[from_unit]
    elif from_unit == "mmbtu":
        gj = value * UNIT_CONVERSIONS["mmbtu"]
    elif from_unit == "therms":
        gj = value * UNIT_CONVERSIONS["therms"]
    else:
        gj = value
    
    if to_unit in ["mwh", "kwh", "gwh"]:
        return gj / UNIT_CONVERSIONS[to_unit]
    elif to_unit == "mmbtu":
        return gj / UNIT_CONVERSIONS["mmbtu"]
    elif to_unit == "therms":
        return gj / UNIT_CONVERSIONS["therms"]
    else:
        return gj

def get_exchange_rate(from_currency, to_currency):
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data['rates'].get(to_currency, None)
    except:
        return None

def format_number(value, decimals=2):
    if value >= 1000000:
        return f"{value:,.{decimals}f}"
    elif value >= 1000:
        return f"{value:,.{decimals}f}"
    elif value >= 1:
        return f"{value:.{decimals}f}"
    else:
        return f"{value:.{decimals+2}f}"

def add_to_history(conversion_data):
    """Add conversion to history"""
    if len(st.session_state.conversion_history) >= 10:
        st.session_state.conversion_history.pop(0)
    st.session_state.conversion_history.append({
        **conversion_data,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

def create_comparison_chart(conversions):
    """Create a comparison chart for multiple conversions"""
    if not conversions:
        return None
    
    fig = go.Figure()
    
    for i, conv in enumerate(conversions):
        fig.add_trace(go.Bar(
            x=[conv["commodity"]],
            y=[conv["result"]],
            name=f"{conv['input_value']} {conv['from_unit']} → {conv['to_unit']}",
            text=f"{format_number(conv['result'])} {conv['to_unit']}",
            textposition='auto',
        ))
    
    fig.update_layout(
        title="Conversion Comparison",
        xaxis_title="Commodity",
        yaxis_title="Converted Value",
        height=400,
        showlegend=True
    )
    
    return fig

def create_gauge_chart(original_value, converted_value, from_unit, to_unit):
    """Create a gauge chart showing conversion ratio"""
    ratio = converted_value / original_value if original_value != 0 else 0
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = ratio,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Conversion Ratio<br>{from_unit} → {to_unit}"},
        delta = {'reference': 1},
        gauge = {
            'axis': {'range': [None, max(ratio * 1.5, 2)]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, ratio * 0.5], 'color': "lightgray"},
                {'range': [ratio * 0.5, ratio], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': ratio
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig

# Header with theme toggle
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown('<h1 class="main-header">🏭 Commodities Trading Converter</h1>', unsafe_allow_html=True)
with col2:
    if st.button("🌙" if not st.session_state.dark_mode else "☀️", help="Toggle Dark/Light Mode"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

# Settings Panel
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Auto-calculation toggle
    st.session_state.auto_calculate = st.checkbox("Auto-calculate on input change", value=st.session_state.auto_calculate)
    
    # Wizard mode toggle
    st.session_state.wizard_mode = st.checkbox("Enable guided wizard", value=st.session_state.wizard_mode)
    
    st.markdown("---")
    
    # Density/API Calculator
    st.subheader("🧮 Density/API Calculator")
    calc_type = st.selectbox("Calculate:", ["Density from API", "API from Density"])
    
    if calc_type == "Density from API":
        api_input = st.number_input("API Gravity (°)", value=35.0, min_value=0.0, max_value=100.0)
        density_result = calculate_density_from_api(api_input)
        st.success(f"Density: {density_result:.3f} g/cm³")
    else:
        density_input = st.number_input("Density (g/cm³)", value=0.85, min_value=0.1, max_value=2.0, step=0.001)
        api_result = calculate_api_from_density(density_input)
        st.success(f"API Gravity: {api_result:.1f}°")
    
    st.markdown("---")
    
    # Bookmarks
    st.subheader("📚 Bookmarks")
    if st.session_state.bookmarks:
        for i, bookmark in enumerate(st.session_state.bookmarks):
            if st.button(f"📌 {bookmark['name']}", key=f"bookmark_{i}"):
                st.session_state.selected_bookmark = bookmark
                st.rerun()
    else:
        st.info("No bookmarks saved yet")
    
    if st.button("🗑️ Clear Bookmarks") and st.session_state.bookmarks:
        st.session_state.bookmarks = []
        st.rerun()
    
    st.markdown("---")
    
    # Conversion History
    st.subheader("📜 Recent Conversions")
    if st.session_state.conversion_history:
        for i, conv in enumerate(reversed(st.session_state.conversion_history[-5:])):
            st.markdown(f"""
            <div class="history-item">
                <small>{conv['timestamp']}</small><br>
                <strong>{conv['commodity']}</strong><br>
                {format_number(conv['input_value'])} {conv['from_unit']} → {format_number(conv['result'])} {conv['to_unit']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No conversions yet")
    
    if st.button("🗑️ Clear History") and st.session_state.conversion_history:
        st.session_state.conversion_history = []
        st.rerun()

# Main Application Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔄 Unit Converter", 
    "💱 Currency", 
    "📊 Comparison", 
    "📋 Batch Convert",
    "📖 Glossary"
])

# Tab 1: Unit Converter
with tab1:
    if st.session_state.wizard_mode:
        st.info("🧙‍♂️ **Wizard Mode**: Follow the steps below for guided conversion")
        
        # Step 1: Select Scenario or Custom
        st.subheader("Step 1: Choose Your Conversion Type")
        conversion_type = st.radio("", ["Use Predefined Scenario", "Custom Conversion"])
        
        if conversion_type == "Use Predefined Scenario":
            scenario_name = st.selectbox("Select Scenario:", list(SCENARIOS.keys()))
            scenario = SCENARIOS[scenario_name]
            
            category = scenario["category"]
            commodity = scenario["commodity"]
            from_unit = scenario["from_unit"]
            to_unit = scenario["to_unit"]
            input_value = st.number_input("Enter Value:", value=float(scenario["value"]))
        else:
            # Step 2: Select Commodity
            st.subheader("Step 2: Select Commodity")
            category = st.selectbox("Category:", list(COMMODITY_DATA.keys()))
            commodity = st.selectbox("Commodity:", list(COMMODITY_DATA[category].keys()))
            
            # Step 3: Set Units and Value
            st.subheader("Step 3: Set Conversion Parameters")
            available_units = COMMODITY_DATA[category][commodity]["units"]
            
            col1, col2 = st.columns(2)
            with col1:
                from_unit = st.selectbox("From Unit:", available_units)
            with col2:
                to_unit = st.selectbox("To Unit:", available_units)
            
            input_value = st.number_input("Enter Value:", value=1.0, min_value=0.0)
    else:
        # Regular Mode
        st.subheader("Quick Conversion")
        
        # Predefined Scenarios
        st.markdown("**Quick Scenarios:**")
        scenario_cols = st.columns(len(SCENARIOS))
        for i, (name, scenario) in enumerate(SCENARIOS.items()):
            with scenario_cols[i]:
                if st.button(f"⚡ {name}", key=f"scenario_{i}"):
                    st.session_state.selected_scenario = scenario
                    st.rerun()
        
        st.markdown("---")
        
        # Check if scenario was selected
        if 'selected_scenario' in st.session_state:
            scenario = st.session_state.selected_scenario
            category = scenario["category"]
            commodity = scenario["commodity"]
            from_unit = scenario["from_unit"]
            to_unit = scenario["to_unit"]
            input_value = st.number_input("Enter Value:", value=float(scenario["value"]))
            del st.session_state.selected_scenario
        elif 'selected_bookmark' in st.session_state:
            bookmark = st.session_state.selected_bookmark
            category = bookmark["category"]
            commodity = bookmark["commodity"]
            from_unit = bookmark["from_unit"]
            to_unit = bookmark["to_unit"]
            input_value = st.number_input("Enter Value:", value=float(bookmark.get("value", 1.0)))
            del st.session_state.selected_bookmark
        else:
            col1, col2 = st.columns(2)
            with col1:
                category = st.selectbox("Category:", list(COMMODITY_DATA.keys()))
            with col2:
                commodity = st.selectbox("Commodity:", list(COMMODITY_DATA[category].keys()))
            
            available_units = COMMODITY_DATA[category][commodity]["units"]
            
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                input_value = st.number_input("Value:", value=1.0, min_value=0.0)
            with col2:
                from_unit = st.selectbox("From:", available_units)
            with col3:
                to_unit = st.selectbox("To:", available_units)
            with col4:
                if st.button("🔄", help="Swap units"):
                    from_unit, to_unit = to_unit, from_unit
                    st.rerun()
    
    # Additional Parameters
    additional_params = {}
    
    if category == "Oil & Liquids":
        with st.expander("🛢️ Oil Properties"):
            use_default = st.checkbox("Use default properties", value=True)
            if not use_default:
                custom_density = st.number_input("Density (g/cm³):", 
                                               value=COMMODITY_DATA[category][commodity]["density"],
                                               min_value=0.1, max_value=2.0, step=0.001)
                additional_params["density"] = custom_density
            else:
                additional_params["density"] = COMMODITY_DATA[category][commodity]["density"]
            
            st.info(f"Default: {COMMODITY_DATA[category][commodity]['density']} g/cm³, "
                   f"API: {COMMODITY_DATA[category][commodity]['api_gravity']}°")
    
    elif category == "Natural Gas":
        with st.expander("🔥 Gas Properties"):
            use_default = st.checkbox("Use default calorific value", value=True)
            if not use_default:
                custom_cv = st.number_input("Calorific Value (MMBtu/thousand m³):",
                                          value=COMMODITY_DATA[category][commodity]["calorific_value"],
                                          min_value=10.0, max_value=100.0, step=0.1)
                additional_params["calorific_value"] = custom_cv
            else:
                additional_params["calorific_value"] = COMMODITY_DATA[category][commodity]["calorific_value"]
    
    elif category == "Agricultural":
        with st.expander("🌾 Agricultural Properties"):
            use_default = st.checkbox("Use default moisture content", value=True)
            if not use_default:
                custom_moisture = st.number_input("Moisture Content (%):",
                                                value=COMMODITY_DATA[category][commodity]["moisture_content"],
                                                min_value=0.0, max_value=30.0, step=0.1)
                additional_params["moisture_content"] = custom_moisture
            else:
                additional_params["moisture_content"] = COMMODITY_DATA[category][commodity]["moisture_content"]
    
    # Conversion Logic
    def perform_conversion():
        if from_unit == to_unit:
            return input_value
        
        try:
            if category == "Oil & Liquids":
                return convert_oil_units(input_value, from_unit, to_unit, 
                                       density=additional_params.get("density"))
            elif category == "Natural Gas":
                return convert_gas_units(input_value, from_unit, to_unit, 
                                       calorific_value=additional_params.get("calorific_value"))
            elif category == "Agricultural":
                return convert_agricultural_units(input_value, from_unit, to_unit, commodity,
                                                moisture_content=additional_params.get("moisture_content"))
            elif category == "Power/Electricity":
                return convert_power_units(input_value, from_unit, to_unit)
            elif category == "Coal":
                if from_unit == "metric tons" and to_unit == "short tons":
                    return input_value / 0.907185
                elif from_unit == "short tons" and to_unit == "metric tons":
                    return input_value * 0.907185
                else:
                    return input_value
            else:
                return input_value
        except Exception as e:
            st.error(f"Conversion error: {str(e)}")
            return None
    
    # Auto-calculation or manual conversion
    if st.session_state.auto_calculate and input_value > 0:
        result = perform_conversion()
        show_result = True
    else:
        show_result = False
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("🔄 Convert", type="primary"):
                result = perform_conversion()
                show_result = True
        with col2:
            if st.button("💾 Save as Bookmark"):
                bookmark_name = st.text_input("Bookmark name:", value=f"{commodity} {from_unit}→{to_unit}")
                if bookmark_name:
                    st.session_state.bookmarks.append({
                        "name": bookmark_name,
                        "category": category,
                        "commodity": commodity,
                        "from_unit": from_unit,
                        "to_unit": to_unit,
                        "value": input_value,
                        **additional_params
                    })
                    st.success("Bookmark saved!")
    
    # Display Results
    if show_result and result is not None:
        # Add to history
        conversion_data = {
            "category": category,
            "commodity": commodity,
            "input_value": input_value,
            "from_unit": from_unit,
            "to_unit": to_unit,
            "result": result,
            **additional_params
        }
        add_to_history(conversion_data)
        
        # Main result display
        st.markdown(f"""
        <div class="conversion-result">
            <h3>✅ Conversion Result</h3>
            <p><strong>{format_number(input_value)} {from_unit}</strong> of <strong>{commodity}</strong> equals:</p>
            <h2 style="color: #059669;">{format_number(result)} {to_unit}</h2>
            <p><small>Converted at {datetime.now().strftime('%H:%M:%S')}</small></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Visualization
        col1, col2 = st.columns(2)
        with col1:
            # Gauge chart
            gauge_fig = create_gauge_chart(input_value, result, from_unit, to_unit)
            st.plotly_chart(gauge_fig, use_container_width=True)
        
        with col2:
            # Conversion factor display
            conversion_factor = result / input_value if input_value != 0 else 0
            st.metric(
                label="Conversion Factor",
                value=f"{conversion_factor:.6f}",
                delta=f"1 {from_unit} = {conversion_factor:.6f} {to_unit}"
            )
            
            # Unit reference
            st.markdown("**Quick Reference:**")
            st.markdown(f"- 1 {from_unit} = {conversion_factor:.4f} {to_unit}")
            st.markdown(f"- 1 {to_unit} = {1/conversion_factor:.4f} {from_unit}")
    
    # Cheat Sheet
    with st.expander("📋 Unit Conversion Cheat Sheet"):
        if category == "Oil & Liquids":
            st.markdown("""
            **Oil & Liquids Standard Conversions:**
            - 1 barrel = 42 US gallons = 158.987 liters
            - 1 metric ton crude oil ≈ 7.33 barrels (varies by density)
            - API Gravity: Higher number = lighter oil
            - Density = 141.5 / (131.5 + API Gravity)
            """)
        elif category == "Natural Gas":
            st.markdown("""
            **Natural Gas Standard Conversions:**
            - 1 MCF = 1,000 cubic feet
            - 1 BCF = 1,000,000,000 cubic feet
            - 1 MMBtu ≈ 1,000 cubic feet (varies by calorific value)
            - LNG: 1 metric ton ≈ 48.7 MMBtu
            """)
        elif category == "Agricultural":
            st.markdown("""
            **Agricultural Standard Conversions:**
            - Wheat: 1 bushel = 60 lbs = 27.2 kg
            - Corn: 1 bushel = 56 lbs = 25.4 kg
            - Soybeans: 1 bushel = 60 lbs = 27.2 kg
            - Moisture content affects weight conversions
            """)

# Tab 2: Currency Conversion
with tab2:
    st.subheader("💱 Currency Conversion")
    
    currency_options = [f"{code} - {data['region']}" for code, data in CURRENCY_DATA.items()]
    currency_codes = list(CURRENCY_DATA.keys())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        amount = st.number_input("Amount:", value=1.0, min_value=0.0)
    with col2:
        from_currency_display = st.selectbox("From:", currency_options, index=0)
        from_currency = currency_codes[currency_options.index(from_currency_display)]
    with col3:
        to_currency_display = st.selectbox("To:", currency_options, index=1)
        to_currency = currency_codes[currency_options.index(to_currency_display)]
    
    rate_option = st.radio("Exchange Rate:", ["Live Rate", "Custom Rate"])
    
    if rate_option == "Custom Rate":
        custom_rate = st.number_input(f"Rate ({from_currency}/{to_currency}):", 
                                    value=1.0, min_value=0.0001, step=0.0001, format="%.4f")
    
    if st.button("💱 Convert Currency", type="primary"):
        if rate_option == "Live Rate":
            with st.spinner("Fetching live rates..."):
                exchange_rate = get_exchange_rate(from_currency, to_currency)
            if exchange_rate:
                converted_amount = amount * exchange_rate
                st.success(f"**{amount:,.2f} {from_currency}** = **{converted_amount:,.2f} {to_currency}**")
                st.info(f"Rate: 1 {from_currency} = {exchange_rate:.4f} {to_currency}")
            else:
                st.error("Could not fetch live rates. Please use custom rate.")
        else:
            converted_amount = amount * custom_rate
            st.success(f"**{amount:,.2f} {from_currency}** = **{converted_amount:,.2f} {to_currency}**")
            st.info(f"Custom Rate: 1 {from_currency} = {custom_rate:.4f} {to_currency}")

# Tab 3: Comparison Mode
with tab3:
    st.subheader("📊 Commodity Comparison")
    
    st.markdown("Compare multiple commodities side by side:")
    
    # Comparison Setup
    num_commodities = st.selectbox("Number of commodities to compare:", [2, 3, 4, 5])
    
    comparisons = []
    
    for i in range(num_commodities):
        with st.expander(f"Commodity {i+1}"):
            col1, col2 = st.columns(2)
            with col1:
                cat = st.selectbox(f"Category {i+1}:", list(COMMODITY_DATA.keys()), key=f"cat_{i}")
            with col2:
                comm = st.selectbox(f"Commodity {i+1}:", list(COMMODITY_DATA[cat].keys()), key=f"comm_{i}")
            
            units = COMMODITY_DATA[cat][comm]["units"]
            col1, col2, col3 = st.columns(3)
            with col1:
                val = st.number_input(f"Value {i+1}:", value=1000.0, key=f"val_{i}")
            with col2:
                from_u = st.selectbox(f"From Unit {i+1}:", units, key=f"from_{i}")
            with col3:
                to_u = st.selectbox(f"To Unit {i+1}:", units, key=f"to_{i}")
            
            comparisons.append({
                "category": cat,
                "commodity": comm,
                "input_value": val,
                "from_unit": from_u,
                "to_unit": to_u
            })
    
    if st.button("📊 Compare All", type="primary"):
        results = []
        for comp in comparisons:
            # Perform conversion based on category
            if comp["category"] == "Oil & Liquids":
                result = convert_oil_units(comp["input_value"], comp["from_unit"], comp["to_unit"],
                                         density=COMMODITY_DATA[comp["category"]][comp["commodity"]]["density"])
            elif comp["category"] == "Natural Gas":
                result = convert_gas_units(comp["input_value"], comp["from_unit"], comp["to_unit"],
                                         calorific_value=COMMODITY_DATA[comp["category"]][comp["commodity"]]["calorific_value"])
            elif comp["category"] == "Agricultural":
                result = convert_agricultural_units(comp["input_value"], comp["from_unit"], comp["to_unit"], comp["commodity"],
                                                  moisture_content=COMMODITY_DATA[comp["category"]][comp["commodity"]]["moisture_content"])
            else:
                result = comp["input_value"]  # Simplified for other categories
            
            results.append({**comp, "result": result})
        
        # Display comparison table
        df = pd.DataFrame(results)
        st.dataframe(df[["commodity", "input_value", "from_unit", "result", "to_unit"]], use_container_width=True)
        
        # Comparison chart
        fig = create_comparison_chart(results)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

# Tab 4: Batch Conversion
with tab4:
    st.subheader("📋 Batch Conversion")
    
    st.markdown("Convert multiple values at once:")
    
    # Batch setup
    col1, col2 = st.columns(2)
    with col1:
        batch_category = st.selectbox("Category:", list(COMMODITY_DATA.keys()), key="batch_cat")
    with col2:
        batch_commodity = st.selectbox("Commodity:", list(COMMODITY_DATA[batch_category].keys()), key="batch_comm")
    
    batch_units = COMMODITY_DATA[batch_category][batch_commodity]["units"]
    col1, col2 = st.columns(2)
    with col1:
        batch_from = st.selectbox("From Unit:", batch_units, key="batch_from")
    with col2:
        batch_to = st.selectbox("To Unit:", batch_units, key="batch_to")
    
    # Input methods
    input_method = st.radio("Input Method:", ["Manual Entry", "Upload CSV"])
    
    if input_method == "Manual Entry":
        values_input = st.text_area("Enter values (one per line):", 
                                   value="1000\n2000\n3000\n4000\n5000",
                                   height=100)
        values = [float(v.strip()) for v in values_input.split('\n') if v.strip()]
    else:
        uploaded_file = st.file_uploader("Upload CSV file", type="csv")
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            values_column = st.selectbox("Select values column:", df.columns)
            values = df[values_column].tolist()
        else:
            values = []
    
    if st.button("🔄 Convert Batch", type="primary") and values:
        batch_results = []
        for value in values:
            try:
                if batch_category == "Oil & Liquids":
                    result = convert_oil_units(value, batch_from, batch_to,
                                             density=COMMODITY_DATA[batch_category][batch_commodity]["density"])
                elif batch_category == "Natural Gas":
                    result = convert_gas_units(value, batch_from, batch_to,
                                             calorific_value=COMMODITY_DATA[batch_category][batch_commodity]["calorific_value"])
                elif batch_category == "Agricultural":
                    result = convert_agricultural_units(value, batch_from, batch_to, batch_commodity,
                                                      moisture_content=COMMODITY_DATA[batch_category][batch_commodity]["moisture_content"])
                else:
                    result = value
                
                batch_results.append({
                    "Input": value,
                    "From Unit": batch_from,
                    "Result": result,
                    "To Unit": batch_to
                })
            except Exception as e:
                st.error(f"Error converting {value}: {str(e)}")
        
        # Display results
        if batch_results:
            results_df = pd.DataFrame(batch_results)
            st.dataframe(results_df, use_container_width=True)
            
            # Summary statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Input", f"{sum(r['Input'] for r in batch_results):,.2f}")
            with col2:
                st.metric("Total Output", f"{sum(r['Result'] for r in batch_results):,.2f}")
            with col3:
                st.metric("Average Ratio", f"{(sum(r['Result'] for r in batch_results) / sum(r['Input'] for r in batch_results)):.4f}")
            
            # Download results
            csv = results_df.to_csv(index=False)
            st.download_button("📥 Download Results", csv, "batch_conversion_results.csv", "text/csv")

# Tab 5: Glossary
with tab5:
    st.subheader("📖 Glossary & Reference")
    
    glossary_categories = {
        "🛢️ Oil & Liquids": {
            "Barrel (bbl)": "Standard oil unit = 42 US gallons = 158.987 liters",
            "API Gravity": "Measure of oil density (°API = 141.5/density - 131.5)",
            "Density": "Mass per unit volume, typically 0.7-0.95 g/cm³ for crude oil",
            "Brent Crude": "North Sea benchmark, ~38°API, light sweet crude",
            "WTI": "West Texas Intermediate, US benchmark, ~38°API",
            "Gasoline": "Refined petroleum product, ~60°API, density ~0.74 g/cm³",
            "Diesel": "Middle distillate, ~35°API, density ~0.85 g/cm³"
        },
        "🔥 Natural Gas": {
            "MCF": "Thousand cubic feet of natural gas",
            "BCF": "Billion cubic feet of natural gas",
            "MMBtu": "Million British Thermal Units, energy content measure",
            "Therm": "100,000 BTU, residential gas billing unit",
            "Calorific Value": "Energy content per unit volume, typically 35-40 MMBtu/MCF",
            "LNG": "Liquefied Natural Gas, cooled to -162°C for transport",
            "Henry Hub": "US natural gas pricing benchmark point"
        },
        "🌾 Agricultural": {
            "Bushel": "Volume measure varying by crop (wheat: 60 lbs, corn: 56 lbs)",
            "Moisture Content": "Water percentage affecting weight and storage",
            "Test Weight": "Weight per unit volume, quality indicator",
            "Protein Content": "Nutritional value measure, affects pricing",
            "CBOT": "Chicago Board of Trade, major agricultural exchange",
            "Basis": "Local price vs. futures price difference"
        },
        "⚡ Power & Coal": {
            "MWh": "Megawatt-hour, 1000 kWh of electricity",
            "Thermal Coal": "Steam coal for power generation, 5500-6500 kcal/kg",
            "Coking Coal": "Metallurgical coal for steel production",
            "Heat Rate": "Efficiency of power plant (BTU/kWh)",
            "Load Factor": "Average power output vs. maximum capacity",
            "Calorific Value": "Energy content, measured in kcal/kg or BTU/lb"
        },
        "💱 Trading Terms": {
            "Spot Price": "Current market price for immediate delivery",
            "Forward Contract": "Agreement for future delivery at set price",
            "Basis Risk": "Risk from price difference between spot and futures",
            "Contango": "Futures price higher than spot price",
            "Backwardation": "Futures price lower than spot price",
            "Hedge": "Risk management strategy using derivatives",
            "Arbitrage": "Profit from price differences between markets"
        }
    }
    
    # Search functionality
    search_term = st.text_input("🔍 Search glossary:", placeholder="Enter term to search...")
    
    for category, terms in glossary_categories.items():
        # Filter terms based on search
        if search_term:
            filtered_terms = {k: v for k, v in terms.items() 
                            if search_term.lower() in k.lower() or search_term.lower() in v.lower()}
        else:
            filtered_terms = terms
        
        if filtered_terms:
            with st.expander(category):
                for term, definition in filtered_terms.items():
                    st.markdown(f"**{term}**: {definition}")
    
    # Conversion factors reference
    st.markdown("---")
    st.subheader("🔢 Quick Reference Factors")
    
    ref_col1, ref_col2 = st.columns(2)
    
    with ref_col1:
        st.markdown("""
        **Energy Equivalents:**
        - 1 MMBtu = 1.055 GJ
        - 1 therm = 0.1 MMBtu
        - 1 kWh = 3.412 kBtu
        - 1 barrel oil ≈ 5.8 MMBtu
        """)
    
    with ref_col2:
        st.markdown("""
        **Volume Conversions:**
        - 1 barrel = 42 US gallons
        - 1 m³ = 6.29 barrels
        - 1 gallon = 3.785 liters
        - 1 cubic foot = 28.32 liters
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 1rem; margin-top: 2rem;">
    <h3 style="color: white; margin-bottom: 1rem;">🏭 Enhanced Commodities Trading Converter</h3>
    <p style="color: white; margin-bottom: 1rem;">Professional-grade conversion tool with advanced features</p>
    <div style="display: flex; justify-content: center; gap: 1rem; align-items: center; color: white;">
        <span>Created by</span>
        <a href="https://fr.linkedin.com/in/kilian-voillaume" target="_blank" style="color: white; text-decoration: none;">
            <strong>Kilian Voillaume</strong>
        </a>
    </div>
</div>
""", unsafe_allow_html=True)

# App Info Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 App Features")
st.sidebar.markdown("""
✅ **Enhanced Features:**
- 🔄 Auto-calculation mode
- 📚 Bookmark system
- 📜 Conversion history
- 🧙‍♂️ Guided wizard mode
- 📊 Visual comparisons
- 📋 Batch processing
- 🌙 Dark/Light themes
- 📱 Mobile-responsive
- 🧮 Built-in calculators
- 📈 Interactive charts
""")

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip**: Enable auto-calculation for real-time conversions as you type!")

# Floating result (when applicable)
if 'result' in locals() and result is not None:
    st.markdown(f"""
    <div class="sticky-result">
        <strong>Quick Result:</strong><br>
        {format_number(input_value)} {from_unit} = {format_number(result)} {to_unit}
    </div>
    """, unsafe_allow_html=True)
