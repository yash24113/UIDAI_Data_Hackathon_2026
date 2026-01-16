
from flask import Flask, jsonify, render_template, request, send_file
from app.data.loader import loader
from app.data.analyzer import Analyzer
from flask_cors import CORS
import pandas as pd
from fpdf import FPDF
import io

app = Flask(__name__)
CORS(app)

# Initialize Data
loader.load_data()
analyzer = Analyzer(loader)

@app.route('/')
def dashboard():
    states = sorted(loader.enrolment_df['state'].unique().tolist())
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
    return jsonify(analyzer.get_summary(state_filter=state, district_filter=district))

@app.route('/api/data/idea/<int:idea_id>', methods=['GET'])
def get_idea_data(idea_id):
    state = request.args.get('state')
    district = request.args.get('district')
    
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

@app.route('/export/category/pdf/<category_type>')
def export_category_pdf(category_type):
    state = request.args.get('state')
    district = request.args.get('district')
    if state == "All": state = None
    if district == "All": district = None
    
    data = analyzer.get_category_analysis(category_type, state_filter=state, district_filter=district)
    
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt=f"{data['category']} Analysis Report", ln=1, align='C')
    pdf.ln(5)
    
    # Filter Info
    pdf.set_font("Arial", size=10)
    filter_txt = f"Filter: State={state or 'All'}, District={district or 'All'}"
    pdf.cell(0, 10, txt=filter_txt, ln=1, align='C')
    pdf.ln(10)
    
    # Stats Grid
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, txt=f"Total Volume: {data['total_volume']:,}", ln=1)
    pdf.cell(100, 10, txt=f"Active Regions: {data['active_regions']}", ln=1)
    pdf.ln(5)
    
    # Insights Section
    pdf.set_fill_color(240, 248, 255) # Light Blue
    pdf.rect(10, pdf.get_y(), 190, 60, 'F')
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Key Insights", ln=1)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 10, txt="Top Performer:", ln=0)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, txt=f"{data['top_performer']['name']} ({data['top_performer']['value']:,})", ln=1)
    pdf.multi_cell(0, 6, txt=f"Reason: {data['top_performer']['reason']}")
    pdf.ln(2)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(45, 10, txt="Bottom Performer:", ln=0)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, txt=f"{data['bottom_performer']['name']} ({data['bottom_performer']['value']:,})", ln=1)
    pdf.multi_cell(0, 6, txt=f"Reason: {data['bottom_performer']['reason']}")
    pdf.ln(5)
    
    # Government Solution
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(40, 167, 69) # Green
    pdf.cell(0, 10, txt="  GOVERNMENT ACTION PLAN", ln=1, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, txt=data['solution'], border=1)
    pdf.ln(10)
    
    # Data Table
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt=f"Top {data['entity_label']}s by {data['metric_label']}", ln=1)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(140, 8, txt="Region Name", border=1)
    pdf.cell(50, 8, txt="Volume", border=1, ln=1)
    
    pdf.set_font("Arial", size=10)
    for label, val in zip(data['chart_labels'], data['chart_data']):
        pdf.cell(140, 8, txt=str(label), border=1)
        pdf.cell(50, 8, txt=f"{int(val):,}", border=1, ln=1)
        
    buffer = io.BytesIO()
    pdf_content = pdf.output(dest='S').encode('latin-1')
    buffer.write(pdf_content)
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f'{category_type}_Report.pdf', mimetype='application/pdf')
@app.route('/api/districts/<state_name>')
def get_districts(state_name):
    districts = sorted(loader.enrolment_df[loader.enrolment_df['state'] == state_name]['district'].unique().tolist())
    return jsonify(districts)

@app.route('/export/report')
def export_report():
    # Full PDF Report
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.cell(200, 10, txt="UIDAI Hackathon 2026 - Comprehensive Report", ln=1, align='C')
    
    summary = analyzer.get_summary()
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Total Enrolment: {summary['total_enrolment']}", ln=1)
    pdf.cell(200, 10, txt=f"Total Demographic Updates: {summary['total_demographic_updates']}", ln=1)
    pdf.cell(200, 10, txt=f"Total Biometric Updates: {summary['total_biometric_updates']}", ln=1)
    
    pdf.ln(10)
    pdf.cell(200, 10, txt="Key Insights (Top 5 Ideas):", ln=1)
    
    for i in [1, 2, 3, 4, 9]: # Selected key ideas
        data = analyzer._format_response(i, [], [], "", "") # Just to get meta
        res = get_idea_data(i).json
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, txt=f"{i}. {data['title']}", ln=1)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 8, txt=f"Problem: {data['problem']}")
        pdf.multi_cell(0, 8, txt=f"Insight: {res.get('insight', 'N/A')}")
        pdf.multi_cell(0, 8, txt=f"Solution: {data['solution']}")
        pdf.ln(5)

    buffer = io.BytesIO()
    pdf_content = pdf.output(dest='S').encode('latin-1')
    buffer.write(pdf_content)
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name='UIDAI_Full_Report.pdf', mimetype='application/pdf')

@app.route('/export/idea/<int:idea_id>')
def export_idea_report(idea_id):
    # Single Idea PDF Report
    state = request.args.get('state')
    district = request.args.get('district')
    
    res = get_idea_data(idea_id).json
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.cell(200, 10, txt=f"Analysis Report: Idea {idea_id}", ln=1, align='C')
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt=res['title'], ln=1, align='C')
    
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    if state: pdf.cell(0, 10, txt=f"Filter State: {state}", ln=1)
    if district: pdf.cell(0, 10, txt=f"Filter District: {district}", ln=1)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Problem Statement:", ln=1)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, txt=res['problem'])
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Key Insight:", ln=1)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, txt=res['insight'])
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Recommended Solution:", ln=1)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, txt=res['solution'])
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Data Summary (Top Records):", ln=1)
    pdf.set_font("Arial", size=10)
    
    # Table logic
    pdf.cell(100, 10, txt="Label (District/Pincode)", border=1)
    pdf.cell(50, 10, txt="Value", border=1, ln=1)
    
    for label, val in zip(res['labels'][:15], res['data'][:15]):
        pdf.cell(100, 10, txt=str(label), border=1)
        pdf.cell(50, 10, txt=str(val), border=1, ln=1)

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
