import streamlit as st
import pandas as pd
from barcode import Code128
from barcode.writer import ImageWriter
from fpdf import FPDF
import io
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Pro Barcode Maker", page_icon="🏷️", layout="wide")
st.title("🏷️ Ultimate Barcode Sticker Generator (Final Version)")
st.markdown("### દુકાનનું નામ, પ્રોડક્ટ અને ભાવ સાથે સ્ટીકર બનાવો (Error Free!)")

# --- 2. SIDEBAR SETTINGS ---
st.sidebar.header("⚙️ Page & Sticker Settings")
# A4 Size Default (24 Labels: 3x8)
columns_per_page = st.sidebar.number_input("Columns (ઉભી લાઈન)", value=3, min_value=1)
rows_per_page = st.sidebar.number_input("Rows (આડી લાઈન)", value=8, min_value=1)
cell_width = st.sidebar.number_input("Sticker Width (mm)", value=64.0)
cell_height = st.sidebar.number_input("Sticker Height (mm)", value=34.0)

# --- 3. INPUT DATA ---
col1, col2 = st.columns([1, 2])

with col1:
    st.info("Step 1: દુકાનનું નામ લખો")
    shop_name = st.text_input("Shop Name (Header):", value="My Best Store")
    currency_symbol = st.text_input("Currency:", value="₹")

with col2:
    st.info("Step 2: ફાઈલ અપલોડ કરો")
    uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

# --- 4. GENERATE PROCESS ---
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.write("Data Preview:", df.head(3))
        
        # કોલમ સિલેક્શન
        st.subheader("Step 3: કોલમ પસંદ કરો")
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
            
            # Margins
            margin_x = 7
            margin_y = 10
            
            current_col = 0
            current_row = 0
            
            progress_bar = st.progress(0)
            total_rows = len(df)
            success_count = 0
            
            for index, row in df.iterrows():
                # ડેટા સફાઈ (Cleaning)
                code_text = str(row[sku_col]).strip()
                prod_name = str(row[name_col]).strip()[:25] # લાંબુ નામ હોય તો 25 અક્ષર સુધી કાપો
                price_text = str(row[price_col]).strip()
                
                # ખાલી હોય તો છોડી દો
                if not code_text or code_text.lower() == 'nan': 
                    continue

                # --- SAFETY BLOCK (TRY-EXCEPT) ---
                try:
                    # 1. ગણતરી (Coordinates)
                    x = margin_x + (current_col * cell_width)
                    y = margin_y + (current_row * cell_height)
                    
                    # 2. બોક્સ દોરો (Border)
                    pdf.set_line_width(0.1)
                    pdf.rect(x, y, cell_width, cell_height)
                    
                    # 3. દુકાનનું નામ (Shop Name)
                    pdf.set_font("Arial", 'B', 8)
                    pdf.set_xy(x, y + 2)
                    pdf.cell(cell_width, 4, txt=shop_name, align='C')
                    
                    # 4. બારકોડ ઈમેજ (Barcode Image)
                    rv = io.BytesIO()
                    # અહીં એરર આવી શકે એટલે ધ્યાન રાખવું
                    Code128(code_text, writer=ImageWriter()).write(rv, options={"module_height": 8.0, "font_size": 0, "text_distance": 1.0, "quiet_zone": 1.0})
                    
                    temp_img = f"temp_{index}.png"
                    with open(temp_img, "wb") as f:
                        f.write(rv.getvalue())
                    
                    # ઈમેજ PDF માં મૂકો
                    img_w = cell_width - 10
                    img_h = 12
                    pdf.image(temp_img, x=x+5, y=y+7, w=img_w, h=img_h)
                    os.remove(temp_img) # ક્લીન અપ
                    
                    # 5. કોડ લખો (Text Code)
                    pdf.set_font("Arial", size=6)
                    pdf.set_xy(x, y + 19)
                    pdf.cell(cell_width, 3, txt=code_text, align='C')
                    
                    # 6. પ્રોડક્ટ અને ભાવ (Details)
                    pdf.set_font("Arial", size=7)
                    pdf.set_xy(x, y + 23)
                    pdf.cell(cell_width, 4, txt=prod_name, align='C')
                    
                    pdf.set_font("Arial", 'B', 10)
                    pdf.set_xy(x, y + 27)
                    pdf.cell(cell_width, 5, txt=f"MRP: {currency_symbol}{price_text}", align='C')
                    
                    # Success Count વધારો
                    success_count += 1
                    
                    # --- GRID LOGIC (Next Sticker) ---
                    current_col += 1
                    if current_col >= columns_per_page:
                        current_col = 0
                        current_row += 1
                        if current_row >= rows_per_page:
                            pdf.add_page()
                            current_row = 0
                            
                except Exception as e:
                    # જો કોઈ કોડ ખરાબ હોય તો અહીં પકડાશે
                    st.warning(f"⚠️ Row {index+1} Skipped (Invalid Code: '{code_text}'). Error: {e}")
                    # ટેમ્પ ફાઈલ રહી ગઈ હોય તો કાઢી નાખો
                    if os.path.exists(f"temp_{index}.png"):
                        os.remove(f"temp_{index}.png")
                    continue
                
                # Progress Bar Update
                progress_bar.progress((index + 1) / total_rows)
            
            # Final PDF Download
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.success(f"✅ PDF Created Successfully! ({success_count} Stickers Generated)")
            st.download_button("📥 Download Final PDF", pdf_bytes, "Stickers.pdf", "application/pdf")

    except Exception as main_error:
        st.error(f"File Error: {main_error}")
else:
    st.info("👈 ડાબી બાજુ સેટિંગ્સ છે. ફાઈલ અપલોડ કરો એટલે મેજિક શરૂ!")
