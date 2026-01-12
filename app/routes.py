
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
