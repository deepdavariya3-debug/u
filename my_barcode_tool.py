import streamlit as st
import pandas as pd
from barcode import Code128
from barcode.writer import ImageWriter
from fpdf import FPDF
import io
import os

# --- HELPER FUNCTION: TEXT CLEANER ---
def clean_text_for_pdf(text):
    """
    આ ફંક્શન ટેક્સ્ટમાંથી ગુજરાતી કે સ્પેશિયલ કેરેક્ટર કાઢી નાખશે
    અને ₹ ને Rs. માં ફેરવી દેશે જેથી PDF ક્રેશ ન થાય.
    """
    if not text: return ""
    text = str(text)
    # 1. રૂપિયાના સિમ્બોલને Rs. માં ફેરવો
    text = text.replace("₹", "Rs. ")
    # 2. માત્ર અંગ્રેજી અક્ષરો, નંબરો અને સામાન્ય ચિહ્નો રાખો
    # (ગુજરાતી કે ઈમોજી કાઢી નાખશે)
    text = text.encode('latin-1', 'ignore').decode('latin-1')
    return text

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Pro Barcode Maker", page_icon="🏷️", layout="wide")
st.title("🏷️ Ultimate Barcode Sticker Generator (Final Version)")
st.markdown("### હવે ડબલ ટેક્સ્ટ નહીં આવે! (અને એરર પણ નહીં)")

# --- 2. SIDEBAR SETTINGS ---
st.sidebar.header("⚙️ Page & Sticker Settings")
columns_per_page = st.sidebar.number_input("Columns (ઉભી લાઈન)", value=3, min_value=1)
rows_per_page = st.sidebar.number_input("Rows (આડી લાઈન)", value=8, min_value=1)
cell_width = st.sidebar.number_input("Sticker Width (mm)", value=64.0)
cell_height = st.sidebar.number_input("Sticker Height (mm)", value=34.0)

# --- 3. INPUT DATA ---
col1, col2 = st.columns([1, 2])

with col1:
    st.info("Step 1: દુકાનનું નામ")
    shop_name_input = st.text_input("Shop Name (Header):", value="My Best Store")
    shop_name = clean_text_for_pdf(shop_name_input) # નામ ક્લીન કરો
    currency_symbol = st.text_input("Currency (Type Rs):", value="Rs.")

with col2:
    st.info("Step 2: ફાઈલ અપલોડ કરો")
    uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

# --- 4. GENERATE PROCESS ---
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.write("Data Preview:", df.head(3))
        
        st.subheader("Step 3: કોલમ ધ્યાનથી પસંદ કરો")
        # અહીં લાલ રંગમાં સૂચના આવશે
        st.markdown("🔴 **મહત્વનું:** નીચેના ત્રણેય ખાનામાં અલગ-અલગ કોલમ સિલેક્ટ કરો. (એકનું એક નામ ત્રણ વાર સિલેક્ટ ન કરતા).")

        c1, c2, c3 = st.columns(3)
        with c1:
            # અહીં SKU કોડ હોય તે કોલમ પસંદ કરો
            sku_col = st.selectbox("Select Barcode/SKU Column:", df.columns)
        with c2:
            # અહીં પ્રોડક્ટનું નામ હોય તે કોલમ પસંદ કરો
            name_col = st.selectbox("Select Product Name Column:", df.columns)
        with c3:
            # અહીં ભાવ હોય તે કોલમ પસંદ કરો
            price_col = st.selectbox("Select Price Column:", df.columns)
        
        if st.button("Generate Professional PDF 🚀"):
            
            pdf = FPDF(unit='mm', format='A4')
            pdf.set_auto_page_break(auto=False)
            pdf.add_page()
            
            margin_x = 7
            margin_y = 10
            
            current_col = 0
            current_row = 0
            
            progress_bar = st.progress(0)
            total_rows = len(df)
            success_count = 0
            
            for index, row in df.iterrows():
                # --- STEP A: DATA CLEANING ---
                # બારકોડ માટે ડેટા લો
                raw_code = str(row[sku_col]).strip()
                
                # Product Name અને Price ને PDF માટે સાફ કરો
                prod_name = clean_text_for_pdf(str(row[name_col]))[:25]
                price_val = clean_text_for_pdf(str(row[price_col]))
                
                # જો કોડ ખાલી હોય તો આગળ વધો
                if not raw_code or raw_code.lower() == 'nan': 
                    continue

                # --- STEP B: GENERATION (SAFE MODE) ---
                try:
                    # 1. Coordinates
                    x = margin_x + (current_col * cell_width)
                    y = margin_y + (current_row * cell_height)
                    
                    # 2. Draw Box
                    pdf.set_line_width(0.1)
                    pdf.rect(x, y, cell_width, cell_height)
                    
                    # 3. Shop Name
                    pdf.set_font("Arial", 'B', 8)
                    pdf.set_xy(x, y + 2)
                    pdf.cell(cell_width, 4, txt=shop_name, align='C')
                    
                    # 4. Barcode Image (FIXED HERE)
                    rv = io.BytesIO()
                    # અહીં "text_distance": 0.0 કર્યું છે, જેથી ઈમેજમાં ટેક્સ્ટ ન આવે
                    # અને "font_size": 0 કર્યું છે.
                    Code128(raw_code, writer=ImageWriter()).write(rv, options={"module_height": 8.0, "font_size": 0, "text_distance": 0.0, "quiet_zone": 1.0})
                    
                    temp_img = f"temp_{index}.png"
                    with open(temp_img, "wb") as f:
                        f.write(rv.getvalue())
                    
                    img_w = cell_width - 10
                    img_h = 12
                    pdf.image(temp_img, x=x+5, y=y+7, w=img_w, h=img_h)
                    os.remove(temp_img)
                    
                    # 5. Code Text (Safe Text - આપણે અલગથી લખીએ છીએ)
                    safe_code_text = clean_text_for_pdf(raw_code)
                    pdf.set_font("Arial", size=6)
                    pdf.set_xy(x, y + 19)
                    pdf.cell(cell_width, 3, txt=safe_code_text, align='C')
                    
                    # 6. Name & Price
                    pdf.set_font("Arial", size=7)
                    pdf.set_xy(x, y + 23)
                    pdf.cell(cell_width, 4, txt=prod_name, align='C')
                    
                    pdf.set_font("Arial", 'B', 10)
                    pdf.set_xy(x, y + 27)
                    clean_currency = clean_text_for_pdf(currency_symbol)
                    pdf.cell(cell_width, 5, txt=f"MRP: {clean_currency} {price_val}", align='C')
                    
                    success_count += 1
                    
                    # --- GRID LOGIC ---
                    current_col += 1
                    if current_col >= columns_per_page:
                        current_col = 0
                        current_row += 1
                        if current_row >= rows_per_page:
                            pdf.add_page()
                            current_row = 0
                            
                except Exception as e:
                    st.warning(f"⚠️ Skipped Item {index+1}: Code '{raw_code}' is invalid. (Check if you selected the wrong column!)")
                    if os.path.exists(f"temp_{index}.png"):
                        os.remove(f"temp_{index}.png")
                    continue
                
                progress_bar.progress((index + 1) / total_rows)
            
            # Final PDF Download
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.success(f"✅ PDF Ready! ({success_count} Stickers Created)")
            st.download_button("📥 Download Final PDF", pdf_bytes, "Stickers.pdf", "application/pdf")

    except Exception as main_error:
        st.error(f"Something went wrong: {main_error}")
else:
    st.info("👈 Upload CSV to start!")
