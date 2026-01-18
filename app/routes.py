
from flask import Flask, jsonify, render_template, request, send_file
from app.data.loader import loader
from app.data.analyzer import Analyzer
from flask_cors import CORS
import pandas as pd
from fpdf import FPDF
import io
import requests, random, time, os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from twilio.rest import Client

# ---------------------------
# Setup
# ---------------------------
load_dotenv()
app = Flask(__name__)
CORS(app)

MOCKAPI_BASE_URL = os.getenv("MOCKAPI_BASE_URL")
OTP_EXPIRY = 300

# Twilio
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")

# Email
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

otp_store = {}


# ---------------------------
# Helpers
# ---------------------------
def generate_otp():
    return str(random.randint(100000, 999999))


def send_sms(phone, otp):
    twilio_client.messages.create(
        body=f"Your OTP is {otp}. Valid for 5 minutes.",
        from_=TWILIO_PHONE,
        to=phone
    )


def send_email(email, otp):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = email
    msg["Subject"] = "Your OTP"
    msg.attach(MIMEText(f"Your OTP is {otp}", "plain"))

    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()


def save_otp(key, user):
    otp_store[key] = {
        "otp": generate_otp(),
        "expires": time.time() + OTP_EXPIRY,
        "user": user
    }
    return otp_store[key]["otp"]


app = Flask(__name__)
CORS(app)

# Initialize Data
loader.load_data()
analyzer = Analyzer(loader)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route('/dashboard')
def dashboard():
    # Sanitize states: Remove numeric-only entries and N/A
    all_states = loader.enrolment_df['state'].unique().tolist()
    states = sorted([str(s) for s in all_states if s and not str(s).isdigit() and str(s).lower() != 'nan'])
    return render_template('dashboard.html', states=states)

@app.route('/analysis/idea/<int:idea_id>')
def analysis_detail(idea_id):
    states = sorted(loader.enrolment_df['state'].unique().tolist())
    meta = analyzer.metadata.get(idea_id, {"title": "Unknown Analysis"})
    return render_template('analysis_detail.html', states=states, idea_id=idea_id, title=meta['title'])

@app.route('/analysis/category/<category_type>')
def category_analysis(category_type):
    states = sorted(loader.enrolment_df['state'].unique().tolist())
    return render_template('category_analysis.html', states=states, category=category_type.capitalize())

@app.route('/api/data/summary', methods=['GET'])
def get_summary():
    state = request.args.get('state')
    district = request.args.get('district')
    if state == "All": state = None
    if district == "All": district = None
    
    summary = analyzer.get_summary(state_filter=state, district_filter=district)
    
    # If state/district provided, also find top centers in that region
    if state or district:
        centers = analyzer.get_centers(state_filter=state, district_filter=district)
        summary['top_centers'] = centers[:10]
        
    return jsonify(summary)

@app.route('/api/centers', methods=['GET'])
def get_centers():
    state = request.args.get('state')
    district = request.args.get('district')
    pincode = request.args.get('pincode')
    query = request.args.get('q')
    
    if state == "All": state = None
    if district == "All": district = None
    
    centers = analyzer.get_centers(state_filter=state, district_filter=district, pincode_filter=pincode, query=query)
    return jsonify(centers)

@app.route('/api/geocode', methods=['GET'])
def geocode():
    q = request.args.get('q')
    # Simple mock geocoder based on known locations in our dataset or common ones
    # In a real app, use a geocoding service.
    mocks = {
        "Gujarat": [22.2587, 71.1924],
        "Ahmedabad": [23.0225, 72.5714],
        "Surat": [21.1702, 72.8311],
        "Vadodara": [22.3072, 73.1812],
        "Rajkot": [22.3039, 70.8022],
        "Karnataka": [15.3173, 75.7139],
        "Bidar": [17.9104, 77.5199],
        "Delhi": [28.6139, 77.2090],
        "Uttar Pradesh": [26.8467, 80.9462],
        "Lucknow": [26.8467, 80.9462],
        "Mumbai": [19.0760, 72.8777],
        "Maharashtra": [19.7515, 75.7139]
    }
    
    if q in mocks:
        return jsonify({"lat": mocks[q][0], "lng": mocks[q][1]})
    
    return jsonify({"error": "Location not found"}), 404

@app.route('/api/data/idea/<int:idea_id>', methods=['GET', 'POST'])
def get_idea_data(idea_id):
    state = request.args.get('state') or request.form.get('state')
    district = request.args.get('district') or request.form.get('district')
    
    if state == "All": state = None
    if district == "All": district = None

    data = {}
    # Map idea IDs to analyzer methods
    methods = {
        1: analyzer.idea_1_district_activity,
        2: analyzer.idea_2_biometric_camps,
        3: analyzer.idea_3_age_verifier,
        4: analyzer.idea_4_ghost_child,
        5: analyzer.idea_5_integrity_shield,
        6: analyzer.idea_6_financial,
        7: analyzer.idea_7_language_support,
        8: analyzer.idea_8_health_monitor,
        9: analyzer.idea_9_disaster_planning,
        10: analyzer.idea_10_urban_traffic
    }
    
    if idea_id in methods:
        # Some methods accept filtering, some don't (like 5, 6, 8 which use full datasets or logic)
        # We pass filters to all; Python handles kwargs or we check logic inside function
        # For simplicity in Analyzer update, most methods accepted filters.
        # But simpler to just handle call args based on what I wrote in Analyzer.
        
        func = methods[idea_id]
        import inspect
        sig = inspect.signature(func)
        
        args = {}
        if 'state_filter' in sig.parameters: args['state_filter'] = state
        if 'district_filter' in sig.parameters: args['district_filter'] = district
        
        data = func(**args)
    else:
        return jsonify({"error": "Invalid Idea ID"}), 400
        

        
    return jsonify(data)

@app.route('/api/data/category/<category_type>', methods=['GET'])
def get_category_data(category_type):
    state = request.args.get('state')
    district = request.args.get('district')
    if state == "All": state = None
    if district == "All": district = None
    
    data = analyzer.get_category_analysis(category_type, state_filter=state, district_filter=district)
    return jsonify(data)

@app.route('/export/category/csv/<category_type>')
def export_category_csv(category_type):
    state = request.args.get('state')
    district = request.args.get('district')
    if state == "All": state = None
    if district == "All": district = None
    
    data = analyzer.get_category_analysis(category_type, state_filter=state, district_filter=district)
    
    # Create DF for chart data (Top 10) for simplicity in CSV, or full list?
    # Request implied "export data", usually means the chart data or summary. 
    # Let's export the top 10 chart data + summary rows.
    
    rows = []
    # Summary header
    rows.append({"Label": "METRIC", "Value": data['metric_label']})
    rows.append({"Label": "TOTAL VOLUME", "Value": data['total_volume']})
    rows.append({"Label": "TOP PERFORMER", "Value": f"{data['top_performer']['name']} ({data['top_performer']['value']})"})
    rows.append({"Label": "BOTTOM PERFORMER", "Value": f"{data['bottom_performer']['name']} ({data['bottom_performer']['value']})"})
    rows.append({"Label": "", "Value": ""})
    rows.append({"Label": "DATA TABLE (TOP REGIONS)", "Value": ""})
    
    for label, val in zip(data['chart_labels'], data['chart_data']):
        rows.append({"Label": label, "Value": val})
        
    df = pd.DataFrame(rows)
    
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f'{category_type}_Analysis.csv', mimetype='text/csv')

@app.route('/export/category/pdf/<category_type>', methods=['POST'])
def export_category_pdf(category_type):
    state = request.form.get('state')
    district = request.form.get('district')
    chart_image = request.form.get('chart_image') # Base64 string
    
    if state == "All": state = None
    if district == "All": district = None
    
    data = analyzer.get_category_analysis(category_type, state_filter=state, district_filter=district)
    
    pdf = FPDF()
    pdf.add_page()
    
    # --- Professional Header ---
    pdf.set_fill_color(0, 51, 102) # Dark Blue
    pdf.rect(0, 0, 210, 40, 'F')
    
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(0, 20, txt="Aadhaar Analytics Portal", ln=1, align='C')
    pdf.set_font("Arial", size=14)
    pdf.cell(0, 10, txt=f"{data['category']} Performance Report - 2026", ln=1, align='C')
    
    pdf.ln(15)
    pdf.set_text_color(0, 0, 0)
    
    # --- Filter Context ---
    pdf.set_font("Arial", 'I', 10)
    filter_txt = f"Scope: State: {state or 'National'}, District: {district or 'All Cities'}"
    pdf.cell(0, 10, txt=filter_txt, ln=1, align='L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)
    
    # --- Summary Dashboard ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="Executive Summary", ln=1)
    
    # Key Stats Boxes
    start_y = pdf.get_y()
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, start_y, 60, 25, 'F')
    pdf.rect(75, start_y, 60, 25, 'F')
    pdf.rect(140, start_y, 60, 25, 'F')
    
    pdf.set_font("Arial", 'B', 10)
    pdf.set_xy(10, start_y + 5)
    pdf.cell(60, 5, txt="TOTAL VOLUME", ln=0, align='C')
    pdf.set_xy(75, start_y + 5)
    pdf.cell(60, 5, txt="TOP PERFORMER", ln=0, align='C')
    pdf.set_xy(140, start_y + 5)
    pdf.cell(60, 5, txt="BOTTOM PERFORMER", ln=0, align='C')
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_xy(10, start_y + 12)
    pdf.cell(60, 8, txt=f"{data['total_volume']:,}", ln=0, align='C')
    pdf.set_xy(75, start_y + 12)
    pdf.cell(60, 8, txt=data['top_performer']['name'], ln=0, align='C')
    pdf.set_xy(140, start_y + 12)
    pdf.cell(60, 8, txt=data['bottom_performer']['name'], ln=1, align='C')
    
    pdf.set_xy(10, start_y + 25)
    pdf.ln(10)

    # --- Chart Integration ---
    if chart_image:
        temp_file = None
        try:
            import base64
            import tempfile
            import os
            
            # Decode the base64 image
            img_data = base64.b64decode(chart_image.split(',')[1])
            
            # Create a named temporary file that persists long enough for fpdf to read it
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                tmp.write(img_data)
                temp_file = tmp.name
            
            # Use the file path in fpdf
            pdf.image(temp_file, x=15, y=pdf.get_y(), w=180)
            pdf.set_y(pdf.get_y() + 100) # Space for image
            
        except Exception as e:
            pdf.set_font("Arial", 'I', 8)
            pdf.cell(0, 10, txt=f"[Chart could not be rendered: {str(e)}]", ln=1)
        finally:
            # Clean up the temp file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

    pdf.ln(5)
    
    # --- Deep Insights ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="Regional Performance Analysis", ln=1)
    
    # Performer breakdown
    def draw_performer_box(title, name, val, reason, color):
        pdf.set_fill_color(*color)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 8, txt=f" {title}: {name}", ln=1, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 6, txt=f"Volume: {val:,} units\nAnalysis: {reason}", border='LRB')
        pdf.ln(5)

    draw_performer_box("HIGH ACTIVITY ZONE", data['top_performer']['name'], data['top_performer']['value'], data['top_performer']['reason'], (40, 167, 69))
    draw_performer_box("LOW ACTIVITY ZONE", data['bottom_performer']['name'], data['bottom_performer']['value'], data['bottom_performer']['reason'], (220, 53, 69))

    # --- Recommendation ---
    pdf.set_fill_color(255, 243, 205) # Light Yellow
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Government Strategic Action Plan", ln=1, fill=True)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, txt=data['solution'], border=1)
    
    # --- Data Table Page ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt=f"Detailed Data: {data['metric_label']} Distribution", ln=1)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(140, 8, txt="Region Name", border=1, fill=True)
    pdf.cell(50, 8, txt="Volume", border=1, ln=1, fill=True)
    
    pdf.set_font("Arial", size=10)
    for label, val in zip(data['chart_labels'], data['chart_data']):
        pdf.cell(140, 8, txt=str(label), border=1)
        pdf.cell(50, 8, txt=f"{int(val):,}", border=1, ln=1)
        
    buffer = io.BytesIO()
    pdf_content = pdf.output(dest='S').encode('latin-1')
    buffer.write(pdf_content)
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f'{category_type}_Full_Report.pdf', mimetype='application/pdf')

@app.route('/api/analysis/regional', methods=['POST'])
def regional_analysis():
    category = request.form.get('category')
    region_name = request.form.get('region')
    state = request.form.get('state')
    district = request.form.get('district')
    
    if not category or not region_name:
        return jsonify({"error": "Missing parameters"}), 400
        
    context_data = analyzer.get_regional_context(category, region_name, state, district)
    if not context_data:
        return jsonify({"error": "Failed to get context"}), 404

    # Prepare detailed context for Gemini
    prompt = f"""
    Analyze the {category} data for {region_name} ({context_data['level']}).
    Data:
    - Total Volume: {context_data['total']:,}
    - 0-5 Years: {context_data['metrics']['age_0_5']:,}
    - 5-17 Years: {context_data['metrics']['age_5_17']:,}
    - 18+ Years: {context_data['metrics']['age_18_above']:,}
    
    Provide:
    1. **Why this value?**: Explain based on the metrics (e.g., if 0-5 is low, mention saturation or child enrollment gaps).
    2. **Government Solution**: Actionable steps for this specific region.
    3. **Extra Details**: Mention estimated Aadhaar center health or infrastructure needs (infer from data).
    4. **Fun Fact**: A small positive or interesting data point.
    """
    
    response = gemini.chat_response(prompt, context=str(context_data))
    return jsonify({"analysis": response, "data": context_data})

@app.route('/api/districts/<state_name>')
def get_districts(state_name):
    districts = sorted(loader.enrolment_df[loader.enrolment_df['state'] == state_name]['district'].unique().tolist())
    return jsonify(districts)

@app.route('/export/report', methods=['GET', 'POST'])
def export_report():
    if request.method == 'POST':
        charts = []
        for i in range(1, 11):
            chart_img = request.form.get(f'chart{i}')
            charts.append(chart_img)
        
        pdf = FPDF()
        pdf.add_page()
        
        # --- Cover Page ---
        pdf.set_fill_color(0, 51, 102)
        pdf.rect(0, 0, 210, 297, 'F')
        
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 32)
        pdf.ln(80)
        pdf.cell(0, 20, txt="UIDAI HACKATHON 2026", ln=1, align='C')
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 10, txt="Comprehensive Data Analytics Report", ln=1, align='C')
        
        pdf.set_font("Arial", size=12)
        pdf.ln(100)
        pdf.cell(0, 10, txt="Generated on: January 2026", ln=1, align='C')
        pdf.cell(0, 10, txt="Version 2.0 - Interactive Edition", ln=1, align='C')
        
        # --- Summary Page ---
        pdf.add_page()
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", 'B', 20)
        pdf.cell(0, 15, txt="Executive Overview", ln=1)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)
        
        summary = analyzer.get_summary()
        def draw_stat(label, val, y_off):
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(100, 10, txt=label, ln=0)
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, txt=str(val), ln=1)

        draw_stat("Total National Enrolment:", f"{summary['total_enrolment']:,}", 0)
        draw_stat("Demographic Updates:", f"{summary['total_demographic_updates']:,}", 0)
        draw_stat("Biometric Updates:", f"{summary['total_biometric_updates']:,}", 0)
        draw_stat("States Covered:", summary['states_count'], 0)
        draw_stat("Districts Analyzed:", summary['districts_count'], 0)
        
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, txt="Top 10 Actionable Insights", ln=1)
        
        # --- 10 Ideas Pages ---
        import base64
        import tempfile
        import os
        
        for i in range(1, 11):
            pdf.add_page()
            meta = analyzer.metadata.get(i, {})
            # res = get_idea_data(i).json # This might depend on state filters if we want to be precise, but here we assume general
            # For simplicity, we use a basic call to idea data to get insight
            res = analyzer.idea_1_district_activity() if i==1 else \
                  analyzer.idea_2_biometric_camps() if i==2 else \
                  analyzer.idea_3_age_verifier() if i==3 else \
                  analyzer.idea_4_ghost_child() if i==4 else \
                  analyzer.idea_5_integrity_shield() if i==5 else \
                  analyzer.idea_6_financial() if i==6 else \
                  analyzer.idea_7_language_support() if i==7 else \
                  analyzer.idea_8_health_monitor() if i==8 else \
                  analyzer.idea_9_disaster_planning() if i==9 else \
                  analyzer.idea_10_urban_traffic()
            
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 12, txt=f"Insight {i}: {meta.get('title', 'Analysis')}", ln=1, fill=True)
            pdf.ln(5)
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 8, txt="Problem Statement:", ln=1)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 6, txt=meta.get('problem', 'N/A'))
            pdf.ln(5)
            
            # Insert Chart
            chart_b64 = charts[i-1]
            if chart_b64:
                temp_file = None
                try:
                    img_data = base64.b64decode(chart_b64.split(',')[1])
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                        tmp.write(img_data)
                        temp_file = tmp.name
                    pdf.image(temp_file, x=20, y=pdf.get_y(), w=170)
                    pdf.set_y(pdf.get_y() + 85)
                except:
                    pdf.cell(0, 10, txt="[Chart analysis available in portal]", ln=1)
                finally:
                    if temp_file and os.path.exists(temp_file):
                        try: os.remove(temp_file)
                        except: pass
            
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 8, txt="Data Insight:", ln=1)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 6, txt=res.get('insight', 'N/A'))
            
            pdf.ln(5)
            pdf.set_fill_color(220, 240, 220)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 8, txt="Recommendation:", ln=1, fill=True)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 6, txt=meta.get('solution', 'N/A'), border='T')

        buffer = io.BytesIO()
        pdf_content = pdf.output(dest='S').encode('latin-1')
        buffer.write(pdf_content)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name='UIDAI_Full_Analytical_Report.pdf', mimetype='application/pdf')

    # GET request fallback or simpler report
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.cell(200, 10, txt="UIDAI Hackathon 2026 - Comprehensive Report", ln=1, align='C')
    # ... (existing GET logic remains as backup)
    buffer = io.BytesIO()
    pdf_content = pdf.output(dest='S').encode('latin-1')
    buffer.write(pdf_content)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='UIDAI_Report_Summary.pdf', mimetype='application/pdf')

@app.route('/export/idea/<int:idea_id>', methods=['GET', 'POST'])
def export_idea_report(idea_id):
    # Single Idea PDF Report
    state = request.form.get('state') if request.method == 'POST' else request.args.get('state')
    district = request.form.get('district') if request.method == 'POST' else request.args.get('district')
    chart_image = request.form.get('chart_image') if request.method == 'POST' else None
    
    if state == "All": state = None
    if district == "All": district = None

    # Get Data
    data = get_idea_data(idea_id)
    if hasattr(data, 'json'):
        res = data.json
    else:
        # Fallback if called internally (though we use routes)
        res = analyzer.metadata.get(idea_id, {})

    pdf = FPDF()
    pdf.add_page()
    
    # --- Professional Header ---
    pdf.set_fill_color(13, 110, 253) # Bootstrap Primary
    pdf.rect(0, 0, 210, 40, 'F')
    
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 22)
    pdf.cell(0, 20, txt="Aadhaar Insight Dossier", ln=1, align='C')
    pdf.set_font("Arial", size=14)
    pdf.cell(0, 10, txt=f"Idea Analysis Report: {res['title']}", ln=1, align='C')
    
    pdf.ln(15)
    pdf.set_text_color(0, 0, 0)
    
    # --- Meta Info ---
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, txt=f"Scope: {state or 'National'} | {district or 'All Districts'} | Date: January 2026", ln=1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    # --- Problem & Solution Section ---
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(220, 53, 69) # Red
    pdf.cell(0, 10, txt="THE PROBLEM", ln=1)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 6, txt=res['problem'])
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(25, 135, 84) # Green
    pdf.cell(0, 10, txt="GOVERNMENT SOLUTION", ln=1)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 6, txt=res['solution'])
    pdf.ln(10)

    # --- Chart Integration ---
    if chart_image:
        temp_file = None
        try:
            import base64
            import tempfile
            import os
            
            img_data = base64.b64decode(chart_image.split(',')[1])
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                tmp.write(img_data)
                temp_file = tmp.name
            
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, txt="Statistical Visualization", ln=1)
            pdf.image(temp_file, x=15, y=pdf.get_y(), w=180)
            pdf.set_y(pdf.get_y() + 90)
        except Exception as e:
            pdf.cell(0, 10, txt="[Visual data included in digital version]", ln=1)
        finally:
            if temp_file and os.path.exists(temp_file):
                try: os.remove(temp_file)
                except: pass

    # --- Key Insight ---
    pdf.ln(10)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 12, txt="CORE ANALYTICAL INSIGHT", ln=1, fill=True)
    pdf.set_font("Arial", size=11)
    pdf.ln(2)
    pdf.multi_cell(0, 7, txt=res['insight'])

    # --- Data Table ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="Top Regional Performers", ln=1)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(140, 10, txt="Region / Category", border=1, fill=True)
    pdf.cell(50, 10, txt="Metric Value", border=1, ln=1, fill=True, align='R')
    
    pdf.set_font("Arial", size=10)
    for label, val in zip(res['labels'][:20], res['data'][:20]):
        pdf.cell(140, 10, txt=str(label), border=1)
        pdf.cell(50, 10, txt=f"{val:,}" if isinstance(val, (int, float)) else str(val), border=1, ln=1, align='R')

    buffer = io.BytesIO()
    pdf_content = pdf.output(dest='S').encode('latin-1')
    buffer.write(pdf_content)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f'Idea_{idea_id}_Analysis.pdf', mimetype='application/pdf')

@app.route('/export/idea/csv/<int:idea_id>')
def export_idea_csv(idea_id):
    # Single Idea CSV Export
    state = request.args.get('state')
    district = request.args.get('district')
    
    res = get_idea_data(idea_id).json
    
    # Create DataFrame from labels and data
    df = pd.DataFrame({
        'Category': res['labels'],
        'Value': res['data']
    })
    
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f'Idea_{idea_id}_Data.csv', mimetype='text/csv')

# Chatbot Route
from app.gemini_analysis import GeminiAnalyzer
gemini = GeminiAnalyzer()

@app.route('/api/chat', methods=['POST'])
def chat():
    message = request.form.get('message')
    image = request.files.get('image')
    
    if not message and not image:
        return jsonify({"error": "No message or image provided"}), 400
    
    image_data = None
    if image:
        image_data = image.read()
    
    # Prepare Data Context with Real Statistics
    
    # 1. State-wise Enrolment Summary
    # Calculate total enrolment per state (sum of all age groups)
    state_df = loader.enrolment_df.copy()
    state_df['total_enrolment'] = state_df['age_0_5'] + state_df['age_5_17'] + state_df['age_18_above']
    state_summary = state_df.groupby('state')['total_enrolment'].sum().sort_values(ascending=False).head(10).reset_index()
    
    state_context = "\nTop 10 States by Enrolment:\n| State | Total Enrolment |\n|---|---|\n"
    for _, row in state_summary.iterrows():
        state_context += f"| {row['state']} | {int(row['total_enrolment']):,} |\n"
        
    # 2. District-wise Insights (Top 5 Overall)
    district_summary = state_df.groupby(['state', 'district'])['total_enrolment'].sum().sort_values(ascending=False).head(5).reset_index()
    district_context = "\nTop 5 Districts by Enrolment:\n| District | State | Total Enrolment |\n|---|---|---|\n"
    for _, row in district_summary.iterrows():
        district_context += f"| {row['district']} | {row['state']} | {int(row['total_enrolment']):,} |\n"

    
    # 3. Overall Totals
    total_enrolment = state_df['total_enrolment'].sum()
    
    # --- Dynamic Context Injection ---
    specific_context = ""
    msg_lower = message.lower() if message else ""
    
    # Detect States
    unique_states = loader.enrolment_df['state'].unique()
    found_states = [s for s in unique_states if s.lower() in msg_lower]
    
    # Detect Districts
    unique_districts = loader.enrolment_df['district'].unique()
    found_districts = [d for d in unique_districts if d.lower() in msg_lower]
    
    for state in found_states:
        specific_context += f"\n--- SPECIFIC DATA FOR STATE: {state} ---\n"
        
        # Enrolment
        e_data = loader.enrolment_df[loader.enrolment_df['state'] == state]
        total = e_data['age_0_5'].sum() + e_data['age_5_17'].sum() + e_data['age_18_above'].sum()
        specific_context += f"Enrolment: Total={int(total):,}, 0-5={int(e_data['age_0_5'].sum()):,}, 5-17={int(e_data['age_5_17'].sum()):,}, 18+={int(e_data['age_18_above'].sum()):,}\n"
        
        # Demographic
        d_data = loader.demographic_df[loader.demographic_df['state'] == state]
        d_total = d_data['age_5_17'].sum() + d_data['age_18_above'].sum()
        specific_context += f"Demographic Updates: Total={int(d_total):,}\n"
        
        # Biometric
        b_data = loader.biometric_df[loader.biometric_df['state'] == state]
        b_total = b_data['age_5_17'].sum() + b_data['age_18_above'].sum()
        specific_context += f"Biometric Updates: Total={int(b_total):,}\n"

    for dist in found_districts:
        specific_context += f"\n--- SPECIFIC DATA FOR DISTRICT: {dist} ---\n"
        
        # Enrolment
        e_data = loader.enrolment_df[loader.enrolment_df['district'] == dist]
        total = e_data['age_0_5'].sum() + e_data['age_5_17'].sum() + e_data['age_18_above'].sum()
        state_name = e_data['state'].iloc[0] if not e_data.empty else "Unknown"
        specific_context += f"State: {state_name}\n"
        specific_context += f"Enrolment: Total={int(total):,}, 0-5={int(e_data['age_0_5'].sum()):,}, 5-17={int(e_data['age_5_17'].sum()):,}, 18+={int(e_data['age_18_above'].sum()):,}\n"
        
        # Demographic
        d_data = loader.demographic_df[loader.demographic_df['district'] == dist]
        d_total = d_data['age_5_17'].sum() + d_data['age_18_above'].sum()
        specific_context += f"Demographic Updates: Total={int(d_total):,}\n"
        
         # Biometric
        b_data = loader.biometric_df[loader.biometric_df['district'] == dist]
        b_total = b_data['age_5_17'].sum() + b_data['age_18_above'].sum()
        specific_context += f"Biometric Updates: Total={int(b_total):,}\n"
    
    context = f"""
    *** REAL DATA FROM DATABASE ***
    
    Total National Enrolment: {int(total_enrolment):,}
    Total States: {loader.enrolment_df['state'].nunique()}
    
    {state_context}
    {district_context}
    
    {specific_context}
    """
    
    language = request.form.get('language', 'en')
    
    response = gemini.chat_response(message, context=context, image_data=image_data, language=language)
    return jsonify({"response": response})

@app.route('/export/global/dataset')
def export_global_dataset():
    # Export full filtered data as CSV
    state = request.args.get('state')
    district = request.args.get('district')
    
    if state == "All": state = None
    if district == "All": district = None

    # We concatenate all dataframes but filtered
    df_enrol = analyzer.filter_data(loader.enrolment_df, state, district).copy()
    df_enrol['Dataset_Type'] = 'Enrolment'
    
    df_demo = analyzer.filter_data(loader.demographic_df, state, district).copy()
    df_demo['Dataset_Type'] = 'Demographic'
    
    df_bio = analyzer.filter_data(loader.biometric_df, state, district).copy()
    df_bio['Dataset_Type'] = 'Biometric'
    
    full_df = pd.concat([df_enrol, df_demo, df_bio], ignore_index=True)
    
    buffer = io.BytesIO()
    full_df.to_csv(buffer, index=False)
    buffer.seek(0)
    
    fname = f"UIDAI_Filtered_Dataset_{state or 'All'}_{district or 'All'}.csv"
    return send_file(buffer, as_attachment=True, download_name=fname, mimetype='text/csv')

# ---------------------------
# Login Routes
# ---------------------------
@app.route("/auth/login/aadhaar", methods=["POST"])
def login_aadhaar():
    aadhaar = request.json.get("aadhaar")

    users = requests.get(f"{MOCKAPI_BASE_URL}/login").json()
    user = next((u for u in users if u.get("aadhaar") == aadhaar), None)

    if not user:
        return jsonify({"success": False, "message": "Aadhaar not registered"})

    otp = save_otp(user["phone"], user)
    send_sms(user["phone"], otp)

    return jsonify({"success": True, "message": "OTP sent to registered mobile"})

#login send mobile otp
@app.route("/auth/login/mobile", methods=["POST"])
def login_mobile():
    phone = request.json.get("phone")

    users = requests.get(f"{MOCKAPI_BASE_URL}/login").json()
    user = next((u for u in users if u.get("phone") == phone), None)

    if not user:
        return jsonify({"success": False, "message": "Mobile not registered"})

    otp = save_otp(phone, user)
    send_sms(phone, otp)

    return jsonify({"success": True, "message": "OTP sent to mobile"})


#login email sendOtp

@app.route("/auth/login/email", methods=["POST"])
def login_email():
    try:
        email = request.json.get("email")
        
        if not email:
            return jsonify({"success": False, "message": "Email required"}), 400

        # Fetch users from MockAPI with error handling
        response = requests.get(f"{MOCKAPI_BASE_URL}/login", timeout=5)
        response.raise_for_status()
        users = response.json()

        # Case-insensitive email matching
        user = next((u for u in users if u.get("email", "").lower() == email.lower()), None)

        if not user:
            return jsonify({"success": False, "message": "Email not registered"}), 404

        # Generate and save OTP
        otp = save_otp(email, user)
        
        # Send email
        send_email(email, otp)

        return jsonify({"success": True, "message": "OTP sent to email"}), 200
        
    except requests.RequestException as e:
        print(f"MockAPI Error: {str(e)}")
        return jsonify({"success": False, "message": "Service unavailable"}), 503
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"success": False, "message": "Internal server error"}), 500
    
# ---------------------------
# Verify OTP (ONLY ONE)
# ---------------------------
@app.route("/auth/verify-otp", methods=["POST"])
def verify_otp():
    try:
        otp = request.json.get("otp")

        if not otp:
            return jsonify({
                "success": False,
                "message": "OTP is required"
            }), 400

        for key, record in list(otp_store.items()):
            if record["otp"] == otp:

                # ❌ Expired
                if time.time() > record["expires"]:
                    otp_store.pop(key)
                    return jsonify({
                        "success": False,
                        "message": "OTP expired"
                    }), 400

                user = record["user"]

                # ✅ Save to MockAPI AFTER verification
                url = f"{MOCKAPI_BASE_URL}/login"
                
                try:
                    response = requests.get(url, timeout=5)
                    response.raise_for_status()
                    users = response.json()
                except requests.RequestException:
                    return jsonify({
                        "success": False,
                        "message": "Service unavailable"
                    }), 503

                # Check if user already exists (case-insensitive)
                phone = user.get("phone", "")
                email = user.get("email", "")
                
                existing = any(
                    u.get("phone", "").lower() == phone.lower() or 
                    u.get("email", "").lower() == email.lower() 
                    for u in users
                )
                
                if not existing:
                    try:
                        user_response = requests.post(url, json=user, timeout=5)
                        user_response.raise_for_status()
                        user = user_response.json()
                    except requests.RequestException:
                        return jsonify({
                            "success": False,
                            "message": "Failed to create user"
                        }), 500

                otp_store.pop(key)

                return jsonify({
                    "success": True,
                    "message": "Registration successful",
                    "user": user
                }), 200

        return jsonify({
            "success": False,
            "message": "Invalid OTP"
        }), 400
        
    except Exception as e:
        print(f"Error in verify_otp: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500


@app.route("/auth/send-mobile-otp", methods=["POST"])
def send_mobile_otp():
    try:
        data = request.json
        phone = data.get("phone", "").strip()

        if not phone:
            return jsonify({
                "success": False,
                "message": "Mobile number is required"
            }), 400

        url = f"{MOCKAPI_BASE_URL}/login"
        
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            users = response.json()
        except requests.RequestException:
            return jsonify({
                "success": False,
                "message": "Service unavailable"
            }), 503

        # ❌ If already registered → error (case-insensitive)
        if any(u.get("phone", "").lower() == phone.lower() for u in users):
            return jsonify({
                "success": False,
                "message": "Mobile number already registered"
            }), 409

        # ✅ Create TEMP user (NOT saved)
        temp_user = {
            "name": data.get("name", "").strip(),
            "email": data.get("email", "").strip(),
            "phone": phone,
            "aadhaar": data.get("aadhaar", "").strip()
        }

        # Generate & store OTP with temp user
        otp = save_otp(phone, temp_user)
        send_sms(phone, otp)

        return jsonify({
            "success": True,
            "message": "OTP sent to mobile"
        }), 200
        
    except Exception as e:
        print(f"Error in send_mobile_otp: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500


@app.route("/auth/send-email-otp", methods=["POST"])
def send_email_otp():
    try:
        data = request.json
        email = data.get("email", "").strip()

        if not email:
            return jsonify({
                "success": False,
                "message": "Email is required"
            }), 400

        url = f"{MOCKAPI_BASE_URL}/login"
        
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            users = response.json()
        except requests.RequestException:
            return jsonify({
                "success": False,
                "message": "Service unavailable"
            }), 503

        # ❌ If already registered → error (case-insensitive)
        if any(u.get("email", "").lower() == email.lower() for u in users):
            return jsonify({
                "success": False,
                "message": "Email already registered"
            }), 409

        # ✅ TEMP user (NOT saved yet)
        temp_user = {
            "name": data.get("name", "").strip(),
            "email": email,
            "phone": data.get("phone", "").strip(),
            "aadhaar": data.get("aadhaar", "").strip()
        }

        # Generate & store OTP with temp user
        otp = save_otp(email, temp_user)
        send_email(email, otp)

        return jsonify({
            "success": True,
            "message": "OTP sent to email"
        }), 200
        
    except Exception as e:
        print(f"Error in send_email_otp: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500