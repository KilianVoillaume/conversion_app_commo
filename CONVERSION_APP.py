import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import math

st.set_page_config(
    page_title="Commodities Trading Converter",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .conversion-result {
        background-color: #e8f5e8;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

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

UNIT_CONVERSIONS = {
    "barrels": 0.158987, # cubic meters per barrel
    "gallons": 0.00378541, # cubic meters per gallon
    "liters": 0.001, # cubic meters per liter
    "metric tons": 1.0,
    "short tons": 0.907185,
    "pounds": 0.000453592,
    "kilograms": 0.001,
    "bushels": {"wheat": 27.2155, "corn": 25.4012, "soybeans": 27.2155, "rice": 20.4124}, # kg per bushel
    "mcf": 28.3168, # cubic meters per thousand cubic feet
    "bcf": 28316846.6, # cubic meters per billion cubic feet
    "mmbtu": 1.05506, # GJ per MMBtu
    "therms": 0.105506, # GJ per therm
    "cubic_meters": 1.0,
    "mwh": 3.6, # GJ per MWh
    "kwh": 0.0036, # GJ per kWh
    "gwh": 3600, # GJ per GWh
    "kcal": 4.184e-6 # GJ per kcal
}

CURRENCY_DATA = {
    "USD": {"region": "USA"},
    "EUR": {"region": "Europe"},
    "GBP": {"region": "United Kingdom"},
    "JPY": {"region": "Japan"},
    "CAD": {"region": "Canada"},
    "AUD": {"region": "Australia"},
    "CHF": {"region": "Switzerland"},
    "CNY": {"region": "China"},
    "INR": {"region": "Indian Rupee"},
    "BRL": {"region": "Brazil"},
    "RUB": {"region": "Russia"},
    "MXN": {"region": "Mexico"}
}

def calculate_density_from_api(api_gravity):
    return 141.5 / (131.5 + api_gravity)

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

def get_currency_display(currency_code):
    region = CURRENCY_DATA.get(currency_code, {}).get("region", "")
    return f"{currency_code} – {region}"

st.markdown('<h1 class="main-header">🏭 Commodities Trading Converter</h1>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🔄 Unit & Volume Conversion", "💱 Currency Conversion", "📖 Glossary"])

# Unit & Volume Conversion
with tab1:
    st.header("Unit & Volume Conversion")
    
    col1, col2 = st.columns(2)
    
    with col1:
        category = st.selectbox("Select Commodity Category", list(COMMODITY_DATA.keys()))
    
    with col2:
        commodity = st.selectbox("Select Specific Commodity", list(COMMODITY_DATA[category].keys()))
    
    available_units = COMMODITY_DATA[category][commodity]["units"]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        input_value = st.number_input("Enter Value", value=1.0, min_value=0.0, step=0.1)
    
    with col2:
        from_unit = st.selectbox("From Unit", available_units)
    
    with col3:
        to_unit = st.selectbox("To Unit", available_units)
    
    additional_params = {}
    
    if category == "Oil & Liquids":
        col1, col2 = st.columns(2)
        with col1:
            use_default_density = st.checkbox("Use default density", value=True)
        with col2:
            if not use_default_density:
                custom_density = st.number_input("Custom Density (g/cm³)", 
                                               value=COMMODITY_DATA[category][commodity]["density"], 
                                               min_value=0.1, max_value=2.0, step=0.001)
                additional_params["density"] = custom_density
            else:
                additional_params["density"] = COMMODITY_DATA[category][commodity]["density"]
                
        st.info(f"Default density for {commodity}: {COMMODITY_DATA[category][commodity]['density']} g/cm³")
    
    elif category == "Natural Gas":
        col1, col2 = st.columns(2)
        with col1:
            use_default_cv = st.checkbox("Use default calorific value", value=True)
        with col2:
            if not use_default_cv:
                custom_cv = st.number_input("Custom Calorific Value (MMBtu/thousand m³)", 
                                          value=COMMODITY_DATA[category][commodity]["calorific_value"], 
                                          min_value=10.0, max_value=100.0, step=0.1)
                additional_params["calorific_value"] = custom_cv
            else:
                additional_params["calorific_value"] = COMMODITY_DATA[category][commodity]["calorific_value"]
                
        st.info(f"Default calorific value for {commodity}: {COMMODITY_DATA[category][commodity]['calorific_value']} MMBtu/thousand m³")
    
    elif category == "Agricultural":
        col1, col2 = st.columns(2)
        with col1:
            use_default_moisture = st.checkbox("Use default moisture content", value=True)
        with col2:
            if not use_default_moisture:
                custom_moisture = st.number_input("Custom Moisture Content (%)", 
                                                value=COMMODITY_DATA[category][commodity]["moisture_content"], 
                                                min_value=0.0, max_value=30.0, step=0.1)
                additional_params["moisture_content"] = custom_moisture
            else:
                additional_params["moisture_content"] = COMMODITY_DATA[category][commodity]["moisture_content"]
                
        st.info(f"Default moisture content for {commodity}: {COMMODITY_DATA[category][commodity]['moisture_content']}%")
    
    if st.button("Convert", type="primary"):
        try:
            if from_unit == to_unit:
                result = input_value
            else:
                if category == "Oil & Liquids":
                    result = convert_oil_units(input_value, from_unit, to_unit, 
                                             density=additional_params.get("density"))
                elif category == "Natural Gas":
                    result = convert_gas_units(input_value, from_unit, to_unit, 
                                             calorific_value=additional_params.get("calorific_value"))
                elif category == "Agricultural":
                    result = convert_agricultural_units(input_value, from_unit, to_unit, commodity,
                                                      moisture_content=additional_params.get("moisture_content"))
                elif category == "Power/Electricity":
                    result = convert_power_units(input_value, from_unit, to_unit)
                elif category == "Coal":
                    if from_unit == "metric tons" and to_unit == "short tons":
                        result = input_value / 0.907185
                    elif from_unit == "short tons" and to_unit == "metric tons":
                        result = input_value * 0.907185
                    else:
                        result = input_value
                else:
                    result = input_value
            
            st.markdown(f"""
            <div class="conversion-result">
                <h3>Conversion Result</h3>
                <p><strong>{format_number(input_value)} {from_unit}</strong> of <strong>{commodity}</strong> equals:</p>
                <h2 style="color: #28a745;">{format_number(result)} {to_unit}</h2>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.markdown(f"""
            <div class="error-message">
                <strong>Error:</strong> {str(e)}
            </div>
            """, unsafe_allow_html=True)

# Currency Conversion
with tab2:
    st.header("Currency Conversion")
    
    # Create currency options with flags
    currency_options = [get_currency_display(code) for code in CURRENCY_DATA.keys()]
    currency_codes = list(CURRENCY_DATA.keys())
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        amount = st.number_input("Amount", value=1.0, min_value=0.0, step=0.01)
    
    with col2:
        from_currency_display = st.selectbox("From Currency", currency_options, index=0)
        from_currency = currency_codes[currency_options.index(from_currency_display)]
    
    with col3:
        to_currency_display = st.selectbox("To Currency", currency_options, index=1)
        to_currency = currency_codes[currency_options.index(to_currency_display)]
    
    rate_option = st.radio("Exchange Rate Option", ["Fetch Live Rate", "Enter Custom Rate"])
    
    if rate_option == "Enter Custom Rate":
        custom_rate = st.number_input(f"Exchange Rate ({from_currency} to {to_currency})", 
                                    value=1.0, min_value=0.0001, step=0.0001, format="%.4f")
    
    if st.button("Convert Currency", type="primary"):
        try:
            if rate_option == "Fetch Live Rate":
                exchange_rate = get_exchange_rate(from_currency, to_currency)
                if exchange_rate is None:
                    st.error("Unable to fetch live exchange rate. Please try again or use custom rate.")
                else:
                    converted_amount = amount * exchange_rate
                    st.markdown(f"""
                    <div class="conversion-result">
                        <h3>Currency Conversion Result</h3>
                        <p><strong>{amount:,.2f} {get_currency_display(from_currency)}</strong> equals:</p>
                        <h2 style="color: #28a745;">{converted_amount:,.2f} {get_currency_display(to_currency)}</h2>
                        <p><small>Exchange rate: 1 {from_currency} = {exchange_rate:.4f} {to_currency}</small></p>
                        <p><small>Rates updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                converted_amount = amount * custom_rate
                st.markdown(f"""
                <div class="conversion-result">
                    <h3>Currency Conversion Result</h3>
                    <p><strong>{amount:,.2f} {get_currency_display(from_currency)}</strong> equals:</p>
                    <h2 style="color: #28a745;">{converted_amount:,.2f} {get_currency_display(to_currency)}</h2>
                    <p><small>Custom exchange rate: 1 {from_currency} = {custom_rate:.4f} {to_currency}</small></p>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.markdown(f"""
            <div class="error-message">
                <strong>Error:</strong> {str(e)}
            </div>
            """, unsafe_allow_html=True)

# Glossary
with tab3:
    st.header("Glossary")
    
    glossary_data = {
        "Units & Measurements": {
            "Barrel (bbl)": "Standard unit for crude oil = 42 US gallons = 158.987 liters",
            "MMBtu": "Million British Thermal Units - energy content measurement",
            "Mcf": "Thousand cubic feet - natural gas volume measurement",
            "Bushel": "Agricultural volume unit varying by commodity (wheat: 60 lbs, corn: 56 lbs)",
            "API Gravity": "Measure of oil density relative to water (higher = lighter oil)",
            "Calorific Value": "Energy content per unit mass or volume"
        },
        "Commodities": {
            "Brent Crude": "North Sea crude oil benchmark, typically 38-39° API gravity",
            "WTI": "West Texas Intermediate crude oil, US benchmark",
            "LNG": "Liquefied Natural Gas - natural gas cooled to liquid state",
            "Thermal Coal": "Coal used for electricity generation",
            "Coking Coal": "Coal used in steel production"
        },
        "Trading Terms": {
            "Density": "Mass per unit volume, crucial for oil conversions",
            "Moisture Content": "Water percentage in agricultural commodities",
            "Basis": "Price difference between local and benchmark prices",
            "Contango": "Futures price higher than spot price",
            "Backwardation": "Futures price lower than spot price"
        }
    }
    
    for category, terms in glossary_data.items():
        st.subheader(category)
        for term, definition in terms.items():
            st.write(f"**{term}**: {definition}")
        st.write("")

st.sidebar.header("📊 App Information")
st.sidebar.info("""
This application provides accurate conversions for:
- Oil & liquid products
- Natural gas & LNG
- Agricultural commodities
- Coal & power
- Currency exchange

Built for commodities trading professionals.
""")

st.sidebar.header("📝 Notes")
st.sidebar.warning("Always verify critical conversions with official sources. Default values are industry standards but may vary.")

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="text-align: center; padding: 1rem;">
    <p style="margin-bottom: 0.5rem;"><strong>Created by</strong></p>
    <a href="https://fr.linkedin.com/in/kilian-voillaume" target="_blank" style="text-decoration: none; color: #0077B5;">
        <div style="display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="#0077B5">
                <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
            </svg>
            <span><strong>Kilian Voillaume</strong></span>
        </div>
    </a>
</div>
""", unsafe_allow_html=True)
