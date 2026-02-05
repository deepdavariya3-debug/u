import streamlit as st
import pandas as pd
from barcode import Code128
from barcode.writer import ImageWriter
from fpdf import FPDF
import io
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Pro Barcode Maker", page_icon="🏷️", layout="wide")
st.title("🏷️ Ultimate Barcode Sticker Generator")
st.markdown("### દુકાનનું નામ, વસ્તુનું નામ અને ભાવ સાથે સ્ટીકર બનાવો!")

# --- 1. SIDEBAR: STICKER SETTINGS ---
st.sidebar.header("⚙️ Page & Sticker Settings")
# A4 Size Default (24 Labels: 3x8)
columns_per_page = st.sidebar.number_input("Columns (ઉભી લાઈન)", value=3, min_value=1)
rows_per_page = st.sidebar.number_input("Rows (આડી લાઈન)", value=8, min_value=1)
cell_width = st.sidebar.number_input("Sticker Width (mm)", value=64.0)
cell_height = st.sidebar.number_input("Sticker Height (mm)", value=34.0)

# --- 2. INPUT DATA ---
col1, col2 = st.columns([1, 2])

with col1:
    st.info("Step 1: દુકાનનું નામ લખો")
    shop_name = st.text_input("Shop Name (Header):", value="My Store")
    currency_symbol = st.text_input("Currency:", value="₹")

with col2:
    st.info("Step 2: ફાઈલ અપલોડ કરો")
    uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

# --- 3. GENERATE PROCESS ---
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Data Preview:", df.head(3))
    
    # કોલમ સિલેક્શન (બહુ મહત્વનું)
    c1, c2, c3 = st.columns(3)
    with c1:
        sku_col = st.selectbox("Select Barcode/SKU Column:", df.columns)
    with c2:
        name_col = st.selectbox("Select Product Name Column:", df.columns)
    with c3:
        price_col = st.selectbox("Select Price Column:", df.columns)
    
    if st.button("Generate Professional PDF 🚀"):
        
        # PDF Setup
        pdf = FPDF(unit='mm', format='A4')
        pdf.set_auto_page_break(auto=False)
        pdf.add_page()
        
        # Fonts (Arial is built-in)
        margin_x = 7
        margin_y = 10
        
        current_col = 0
        current_row = 0
        
        progress_bar = st.progress(0)
        total_rows = len(df)
        
        for index, row in df.iterrows():
            # ડેટા લો
            code_text = str(row[sku_col])
            prod_name = str(row[name_col])[:25] # લાંબુ નામ હોય તો કાપી નાખે
            price_text = str(row[price_col])
            
            if code_text == 'nan' or not code_text: continue

            # --- 1. COORDINATES ---
            x = margin_x + (current_col * cell_width)
            y = margin_y + (current_row * cell_height)
            
            # --- 2. DRAW BOX (BORDER) ---
            pdf.set_line_width(0.1)
            pdf.rect(x, y, cell_width, cell_height)
            
            # --- 3. SHOP NAME (TOP) ---
            pdf.set_font("Arial", 'B', 8)
            pdf.set_xy(x, y + 2)
            pdf.cell(cell_width, 4, txt=shop_name, align='C')
            
            # --- 4. BARCODE IMAGE ---
            # ઈમેજ બનાવો
            rv = io.BytesIO()
            Code128(code_text, writer=ImageWriter()).write(rv, options={"module_height": 8.0, "font_size": 0, "text_distance": 1.0, "quiet_zone": 1.0})
            
            temp_img = f"temp_{index}.png"
            with open(temp_img, "wb") as f:
                f.write(rv.getvalue())
            
            # ઈમેજ મૂકો (વચ્ચે)
            img_w = cell_width - 10
            img_h = 12
            pdf.image(temp_img, x=x+5, y=y+7, w=img_w, h=img_h)
            os.remove(temp_img) # ક્લીન અપ
            
            # --- 5. CODE TEXT (નીચે નાનો) ---
            pdf.set_font("Arial", size=6)
            pdf.set_xy(x, y + 19)
            pdf.cell(cell_width, 3, txt=code_text, align='C')
            
            # --- 6. PRODUCT NAME & PRICE (BOTTOM) ---
            pdf.set_font("Arial", size=7)
            pdf.set_xy(x, y + 23)
            # Product Name
            pdf.cell(cell_width, 4, txt=prod_name, align='C')
            
            # Price (Bold)
            pdf.set_font("Arial", 'B', 10)
            pdf.set_xy(x, y + 27)
            pdf.cell(cell_width, 5, txt=f"MRP: {currency_symbol}{price_text}", align='C')
            
            # --- LOOP LOGIC ---
            current_col += 1
            if current_col >= columns_per_page:
                current_col = 0
                current_row += 1
                if current_row >= rows_per_page:
                    pdf.add_page()
                    current_row = 0
            
            progress_bar.progress((index + 1) / total_rows)
            
        # Download
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.success("✅ Professional Stickers Ready!")
        st.download_button("📥 Download PDF", pdf_bytes, "Professional_Labels.pdf", "application/pdf")