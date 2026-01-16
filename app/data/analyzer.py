
import pandas as pd

class Analyzer:
    def __init__(self, loader):
        self.loader = loader
        self.metadata = {
            1: {"title": "District-Level Activity Insights", "problem": "Uneven distribution of Aadhaar services leads to resource mismanagement and long wait times for citizens.", "solution": "GOVERNMENT SOLUTION: Strategically deploy mobile Aadhaar vans and increase operator strength in identified high-activity districts to ensure 100% service coverage."},
            2: {"title": "Biometric Update Camps", "problem": "Citizens in specific areas are failing to update biometrics, leading to authentication failures in welfare schemes.", "solution": "GOVERNMENT SOLUTION: Mandatory Biometric Update Camps to be organized in the identified districts, synchronized with local fair-price shops and schools."},
            3: {"title": "Zero-Knowledge Age Verifier", "problem": "Requirement for secure, privacy-preserving age verification for first-time voters without exposing full Aadhaar details.", "solution": "GOVERNMENT SOLUTION: Implementation of ZKP-based age verification APIs for the Election Commission, focusing on districts with high 18+ enrollment growth."},
            4: {"title": "The Ghost Child Indicator", "problem": "Low child enrollment (0-5 years) indicates potential gaps in birth-registration-linked Aadhaar saturation.", "solution": "GOVERNMENT SOLUTION: Integration of Aadhaar enrollment with the 'Mother and Child Tracking System' (MCTS) in identified low-performance districts."},
            5: {"title": "System Integrity Shield", "problem": "Unusual spikes in demographic updates might signal systematic data manipulation or internal process breaches.", "solution": "GOVERNMENT SOLUTION: Immediate automated audit of service centers in high-spike pincodes and enforcement of dual-factor authentication for operators."},
            6: {"title": "Financial Inclusion Score", "problem": "Gaps in digital facility updates hinder the transition to a direct benefit transfer (DBT) enabled economy.", "solution": "GOVERNMENT SOLUTION: Link Aadhaar update frequency with Jan Dhan account activity to identify and bridge financial inclusion gaps in rural clusters."},
            7: {"title": "Demographic & Enrollment Activity", "problem": "High enrollment states often face language barriers, leading to data entry errors by non-native operators.", "solution": "GOVERNMENT SOLUTION: Mandatory deployment of multi-lingual support interfaces and local language translators at regional hubs in top-performing states."},
            8: {"title": "Service Center Health Monitor", "problem": "Persistent demographic updates with zero biometric updates indicate faulty fingerprint/iris scanners at centers.", "solution": "GOVERNMENT SOLUTION: Real-time hardware health monitoring dashboard and automatic ticket generation for device replacement in identified pincodes."},
            9: {"title": "Disaster Relief Planning", "problem": "Lack of real-time data on population displacement during natural disasters like floods or cyclones.", "solution": "GOVERNMENT SOLUTION: Utilize demographic update spikes (address changes) as a proxy for migration tracking to optimize relief supply logistics."},
            10: {"title": "Easy Life in Cities", "problem": "Extreme overcrowding at urban Aadhaar Seva Kendras (ASKs) leads to citizen dissatisfaction and administrative strain.", "solution": "GOVERNMENT SOLUTION: Smart Appointment Scheduling and extended shift timings for centers in high-traffic urban pincodes to reduce footfall congestion."}
        }
        self.pincode_map = {
            "380001": "Lal Darwaja", "380002": "Kalupur", "380003": "Maju", "380004": "Shahibaug",
            "380005": "Sabarmati", "380006": "Ellisbridge", "380007": "Paldi", "380008": "Maninagar",
            "380009": "Navrangpura", "380013": "Naranpura", "380015": "Ambawadi", "380019": "Ghatlodia",
            "380021": "Bapunagar", "380022": "Naroda", "380024": "Bapunagar Ind.", "380026": "Amraiwadi",
            "380028": "Vejalpur", "380050": "Ghodasar", "380051": "Jivraj Park", "380052": "Thaltej",
            "380054": "Bodakdev", "380055": "Jodhpur", "380058": "Sarkhej", "380059": "Gota",
            "380060": "Science City", "380061": "Ghatlodia",
            # Add some sample UP codes for testing if needed, or other Gujarat
            "382010": "Gandhinagar", "382330": "Naroda", "382340": "Naroda Road", "382345": "India Colony"
        }

    def _get_area_name(self, pincode):
        pincode = str(pincode).strip()
        if pincode in self.pincode_map:
            return f"{self.pincode_map[pincode]} ({pincode})"
        return pincode

    def get_summary(self, state_filter=None, district_filter=None):
        enrol = self.filter_data(self.loader.enrolment_df, state_filter, district_filter)
        demo = self.filter_data(self.loader.demographic_df, state_filter, district_filter)
        bio = self.filter_data(self.loader.biometric_df, state_filter, district_filter)
        
        summary = {
            "total_enrolment": int(enrol['age_0_5'].sum() + enrol['age_5_17'].sum() + enrol.get('age_18_above', 0).sum()),
            "total_demographic_updates": int(demo['age_5_17'].sum() + demo['age_18_above'].sum()),
            "total_biometric_updates": int(bio['age_5_17'].sum() + bio['age_18_above'].sum()),
            "states_count":  enrol['state'].nunique(),
            "districts_count": enrol['district'].nunique()
        }
        return summary

    def filter_data(self, df, state_filter=None, district_filter=None):
        if state_filter and state_filter != "All":
            df = df[df['state'] == state_filter]
        if district_filter and district_filter != "All":
            df = df[df['district'] == district_filter]
        return df

    def _format_response(self, idea_id, labels, data, insight, extra_info=None):
        meta = self.metadata.get(idea_id, {})
        return {
            "idea_id": idea_id,
            "title": meta.get("title", ""),
            "problem": meta.get("problem", ""),
            "solution": meta.get("solution", ""),
            "labels": labels,
            "data": data,
            "insight": insight,
            "extra_info": extra_info
        }

    def _generate_narrative(self, df, metric_col, entity_col, context="activity"):
        if df.empty: return "No data available for analysis."
        
        # Find High/Low
        high_row = df.loc[df[metric_col].idxmax()]
        low_row = df.loc[df[metric_col].idxmin()]
        
        avg = df[metric_col].mean()
        high_val = high_row[metric_col]
        
        # Basic Variation explanation
        variation = "significant" if high_val > 2 * avg else "moderate"
        
        # Helper to format entity for narrative if it's a pincode
        def format_ent(val):
            return self._get_area_name(val) if entity_col == 'pincode' else val
            
        narrative = (f"{format_ent(high_row[entity_col])} reports the highest {context} ({int(high_val):,}), showing {variation} deviation from the average ({int(avg):,}). "
                     f"In contrast, {format_ent(low_row[entity_col])} reports the lowest ({int(low_row[metric_col]):,}). "
                     f"This disparity suggests uneven resource allocation or demand patterns in the {variation} range.")
        return narrative

    # Idea 1: District/Pincode-Level Activity Insights
    def idea_1_district_activity(self, state_filter=None, district_filter=None):
        e_df = self.loader.enrolment_df
        d_df = self.loader.demographic_df
        b_df = self.loader.biometric_df

        # Filter
        e_df = self.filter_data(e_df, state_filter, district_filter)
        d_df = self.filter_data(d_df, state_filter, district_filter)
        b_df = self.filter_data(b_df, state_filter, district_filter)

        # Drill-down Logic
        if district_filter and district_filter != "All":
            group_col = 'pincode'
            entity_name = 'Pincode'
        elif state_filter and state_filter != "All":
            group_col = 'district'
            entity_name = 'District'
        else:
            group_col = 'state'
            entity_name = 'State'
        
        e_grp = e_df.groupby(group_col)[['age_0_5', 'age_5_17', 'age_18_above']].sum().sum(axis=1)
        d_grp = d_df.groupby(group_col)[['age_5_17', 'age_18_above']].sum().sum(axis=1)
        b_grp = b_df.groupby(group_col)[['age_5_17', 'age_18_above']].sum().sum(axis=1)

        total_activity = (e_grp.add(d_grp, fill_value=0).add(b_grp, fill_value=0)).reset_index(name='value')
        total_activity = total_activity.sort_values('value', ascending=False)
        
        # Convert Pincode to string for labels if needed
        if group_col == 'pincode': 
            total_activity[group_col] = total_activity[group_col].apply(lambda x: self._get_area_name(x))
        
        top_data = total_activity.head(15)
        
        # Generate Narrative
        insight = self._generate_narrative(total_activity, 'value', group_col, "overall service volume")
        
        return self._format_response(1, top_data[group_col].tolist(), top_data['value'].tolist(), insight)

    # Idea 2: Biometric Update Camps
    def idea_2_biometric_camps(self, state_filter=None, district_filter=None):
        d_df = self.filter_data(self.loader.demographic_df, state_filter, district_filter)
        b_df = self.filter_data(self.loader.biometric_df, state_filter, district_filter)

        # Drill-down
        group_col = 'pincode' if district_filter and district_filter != "All" else 'district'
        
        d_grp = d_df.groupby(group_col)[['age_5_17', 'age_18_above']].sum().sum(axis=1)
        b_grp = b_df.groupby(group_col)[['age_5_17', 'age_18_above']].sum().sum(axis=1)

        merged = pd.concat([d_grp, b_grp], axis=1, keys=['demo', 'bio']).fillna(0)
        # Filter for meaningful activity
        merged = merged[merged['demo'] > (50 if group_col == 'district' else 10)] 
        
        merged['bio_ratio'] = merged['bio'] / merged['demo']
        
        target = merged.sort_values('bio_ratio').head(15).reset_index()
        if group_col == 'pincode': 
             target[group_col] = target[group_col].apply(lambda x: self._get_area_name(x))

        narrative = self._generate_narrative(target, 'bio_ratio', group_col, "biometric update efficiency")
        narrative = f"Bottom performing {group_col}s identified. " + narrative

        return self._format_response(2, target[group_col].tolist(), target['bio_ratio'].round(2).tolist(), narrative)

    # Idea 3: Zero-Knowledge Age Verifier
    def idea_3_age_verifier(self, state_filter=None, district_filter=None):
        e_df = self.loader.enrolment_df
        e_df = self.filter_data(e_df, state_filter, district_filter)
        
        group_col = 'pincode' if district_filter and district_filter != "All" else ('district' if state_filter and state_filter != "All" else 'state')
        
        if 'age_18_above' not in e_df.columns: return self._format_response(3, [], [], "No 18+ data.")
        
        voter_potential = e_df.groupby(group_col)['age_18_above'].sum().reset_index(name='value')
        voter_potential = voter_potential.sort_values('value', ascending=False).head(15)
        
        if group_col == 'pincode': 
            voter_potential[group_col] = voter_potential[group_col].apply(lambda x: self._get_area_name(x))
        
        insight = self._generate_narrative(voter_potential, 'value', group_col, "new 18+ enrolment")
        
        return self._format_response(3, voter_potential[group_col].tolist(), voter_potential['value'].tolist(), insight)

    # Idea 4: Ghost Child Indicator
    def idea_4_ghost_child(self, state_filter=None, district_filter=None):
        e_df = self.loader.enrolment_df
        e_df = self.filter_data(e_df, state_filter, district_filter)
        
        group_col = 'pincode' if district_filter and district_filter != "All" else 'district'
        
        grp = e_df.groupby(group_col)['age_0_5'].sum()
        mean_enrolment = grp.mean()
        
        low_enrolment = grp[grp < (0.5 * mean_enrolment)].sort_values().head(15).reset_index(name='value')
        if group_col == 'pincode': 
            low_enrolment[group_col] = low_enrolment[group_col].apply(lambda x: self._get_area_name(x))

        insight = f"Critical Gap: {len(low_enrolment)} {group_col}s have less than 50% of the average child enrolment ({int(mean_enrolment)}). Lowest being {low_enrolment.iloc[0][group_col]} ({low_enrolment.iloc[0]['value']})."
        
        return self._format_response(4, low_enrolment[group_col].tolist(), low_enrolment['value'].tolist(), insight)

    # Idea 5: Integrity Shield
    def idea_5_integrity_shield(self, state_filter=None, district_filter=None):
        d_df = self.loader.demographic_df
        d_df = self.filter_data(d_df, state_filter, district_filter)
        
        group_col = 'pincode' 
        
        daily_pincode_activity = d_df.groupby(['date', group_col]).size().reset_index(name='count')
        mean_val = daily_pincode_activity['count'].mean()
        threshold = max(50, mean_val * 3)
        
        anomalies = daily_pincode_activity[daily_pincode_activity['count'] > threshold].sort_values('count', ascending=False).head(15)
        
        labels = [f"{self._get_area_name(row[group_col])} ({row['date']})" for _, row in anomalies.iterrows()]
        
        return self._format_response(5, labels, anomalies['count'].tolist(), 
                                     f"Detected {len(anomalies)} instances of unusual spikes (> {int(threshold)} daily ops). Highest spike at {labels[0] if labels else 'None'}.")

    # Idea 6: Financial Inclusion
    def idea_6_financial(self, state_filter=None, district_filter=None):
        # Mocking logic based on "Updates" as proxy for financial activity
        d_df = self.filter_data(self.loader.demographic_df, state_filter, district_filter)
        group_col = 'pincode' if district_filter and district_filter != "All" else 'district'
        
        activity = d_df.groupby(group_col).size().reset_index(name='value').sort_values('value').head(15)
        if group_col == 'pincode': 
            activity[group_col] = activity[group_col].apply(lambda x: self._get_area_name(x))
        
        return self._format_response(6, activity[group_col].tolist(), activity['value'].tolist(), 
                                     f"Areas with lowest digital footprint updates, candidates for Jan Dhan linkage campaigns.")

    # Idea 7: Language Support
    def idea_7_language_support(self, state_filter=None, district_filter=None):
        lang_map = {
            "Karnataka": "Kannada", "Maharashtra": "Marathi", "Gujarat": "Gujarati", 
            "Tamil Nadu": "Tamil", "Kerala": "Malayalam", "Uttar Pradesh": "Hindi",
            "Bihar": "Hindi", "West Bengal": "Bengali", "Andhra Pradesh": "Telugu",
            "Telangana": "Telugu", "Punjab": "Punjabi", "Odisha": "Odia"
        }
        
        e_df = self.filter_data(self.loader.enrolment_df, state_filter, district_filter)
        
        group_col = 'pincode' if district_filter and district_filter != "All" else ('district' if state_filter and state_filter != "All" else 'state')
        
        activity = e_df.groupby(group_col).size().reset_index(name='value').sort_values('value', ascending=False).head(15)
        
        labels = activity[group_col].astype(str).tolist()
        if group_col == 'pincode':
             labels = [self._get_area_name(l) for l in labels]
        
        # Determine likely language
        current_lang = "Local/Hindi"
        if state_filter and state_filter in lang_map:
            current_lang = lang_map[state_filter]
        
        extra = [current_lang] * len(labels)
        
        return self._format_response(7, labels, activity['value'].tolist(), 
                                     f"High volume {group_col}s requiring {current_lang} support interfaces.", extra_info=extra)

    # Idea 8: Center Health Monitor
    def idea_8_health_monitor(self, state_filter=None, district_filter=None):
        d_df = self.filter_data(self.loader.demographic_df, state_filter, district_filter)
        b_df = self.filter_data(self.loader.biometric_df, state_filter, district_filter)
        
        # Always Pincode for health monitor
        d_pin = d_df.groupby('pincode').size()
        b_pin = b_df.groupby('pincode').size()
        
        merged = pd.concat([d_pin, b_pin], axis=1, keys=['demo_count', 'bio_count']).fillna(0)
        faulty_centers = merged[(merged['demo_count'] > 20) & (merged['bio_count'] < 2)].sort_values('demo_count', ascending=False).head(15)
        
        labels = [self._get_area_name(p) for p in faulty_centers.index]
        
        return self._format_response(8, labels, faulty_centers['demo_count'].tolist(), 
                                     f"Identified {len(faulty_centers)} pincodes with high 'Demographic-Only' updates, suggesting biometric device failure.")

    # Idea 9: Disaster Relief
    def idea_9_disaster_planning(self, state_filter=None, district_filter=None):
        disaster_districts = ["Cuddalore", "Nagapattinam", "Puri", "Kendrapara", "Darbhanga", "Gorakhpur", "Wayanad", "Chamoli"]
        
        d_df = self.filter_data(self.loader.demographic_df, state_filter, district_filter)
        if not state_filter:
             d_df = d_df[d_df['district'].isin(disaster_districts)]
        
        if d_df.empty: return self._format_response(9, [], [], "No filtered disaster districts found.")

        group_col = 'pincode' if district_filter and district_filter != "All" else 'district'

        district_updates = d_df.groupby(group_col)[['age_5_17', 'age_18_above']].sum().sum(axis=1).sort_values(ascending=False).head(15)
        
        labels = district_updates.index.tolist()
        if group_col == 'pincode':
            labels = [self._get_area_name(l) for l in labels]
            
        insight = f"Highest displacement/update activity observed in {labels[0]}." if labels else "No significant movement."
        
        return self._format_response(9, labels, district_updates.values.tolist(), insight)

    # Idea 10: Urban Traffic
    def idea_10_urban_traffic(self, state_filter=None, district_filter=None):
        urban_districts = ["Bengaluru", "Mumbai", "Pune", "Chennai", "Hyderabad", "Ahmedabad", "Gurgaon", "Noida", "Kolkata", "Delhi"]
        
        merged_df = pd.concat([self.loader.enrolment_df, self.loader.demographic_df, self.loader.biometric_df])
        merged_df = self.filter_data(merged_df, state_filter, district_filter)
        
        if not state_filter and not district_filter:
            merged_df = merged_df[merged_df['district'].isin(urban_districts)]
        
        group_col = 'pincode'
        
        pincode_traffic = merged_df.groupby(group_col).size().sort_values(ascending=False).head(15)
        
        labels = [self._get_area_name(l) for l in pincode_traffic.index]
        
        return self._format_response(10, labels, pincode_traffic.values.tolist(), 
                                     f"Highest traffic density observed in {labels[0] if labels else 'N/A'}.")

    def get_category_analysis(self, category, state_filter=None, district_filter=None):
        """
        Generic analysis for Enrolment, Demographic, Biometric categories.
        Returns Top/Bottom performers, Reasons (Why), and Government Solutions.
        """
        category = category.lower()
        
        df = None
        if category == 'enrolment':
            df = self.loader.enrolment_df
            # Sum all age groups for total enrolment
            df['total_val'] = df['age_0_5'] + df['age_5_17'] + df['age_18_above']
            metric_label = "Total Enrolment"
            solution = "Strategically deploy mobile Aadhaar vans and increase operator strength in identified high-activity districts to ensure 100% service coverage."
        
        elif category == 'demographic':
            df = self.loader.demographic_df
            df['total_val'] = df['age_5_17'] + df['age_18_above']
            metric_label = "Demographic Updates"
            solution = "Mandatory deployment of multi-lingual support interfaces and local language translators at regional hubs to reduce error rates."
        
        elif category == 'biometric':
            df = self.loader.biometric_df
            df['total_val'] = df['age_5_17'] + df['age_18_above']
            metric_label = "Biometric Updates"
            solution = "Organize Mandatory Biometric Update Camps synchronized with local fair-price shops and schools in low-compliance areas."
        
        else:
            return {"error": "Invalid Category"}

        # Filter Data
        df = self.filter_data(df, state_filter, district_filter)
        
        if df.empty:
            return {"error": "No data available"}

        # Determine Grouping
        if district_filter and district_filter != "All":
            group_col = 'pincode'
            entity_label = "Pincode"
        elif state_filter and state_filter != "All":
            group_col = 'district'
            entity_label = "District"
        else:
            group_col = 'state'
            entity_label = "State"

        # Aggregate
        agg = df.groupby(group_col)['total_val'].sum().sort_values(ascending=False)
        total_volume = int(agg.sum())
        
        if agg.empty:
             return {"error": "No aggregated data"}

        # Top Performer
        top_name = agg.index[0]
        top_val = int(agg.iloc[0])
        top_formatted = self._get_area_name(top_name) if group_col == 'pincode' else top_name
        
        # Bottom Performer
        bottom_name = agg.index[-1]
        bottom_val = int(agg.iloc[-1])
        bottom_formatted = self._get_area_name(bottom_name) if group_col == 'pincode' else bottom_name

        # Average for comparison
        avg_val = agg.mean()

        # "Why" Narrative Logic
        def generate_reason(is_high, val, avg):
            deviation = (val / avg) if avg > 0 else 0
            if is_high:
                if deviation > 2:
                    return "Significantly above average due to high population density or recent special verification drives."
                else:
                    return "Moderately high activity consistent with regional population trends."
            else:
                if val == 0:
                    return "Zero activity detected; potential data gap or severe infrastructure lack."
                elif deviation < 0.5:
                    return "Significantly below average; indicates saturation saturation or accessibility barriers."
                else:
                    return "Lower activity likely due to demographic saturation in this region."

        top_reason = generate_reason(True, top_val, avg_val)
        bottom_reason = generate_reason(False, bottom_val, avg_val)

        # Labels for Chart (Top 10)
        chart_data = agg.head(10)
        chart_labels = [self._get_area_name(i) if group_col == 'pincode' else i for i in chart_data.index]
        
        return {
            "category": category.capitalize(),
            "total_volume": total_volume,
            "metric_label": metric_label,
            "entity_label": entity_label,
            "solution": solution,
            "top_performer": {
                "name": top_formatted,
                "value": top_val,
                "reason": top_reason
            },
            "bottom_performer": {
                "name": bottom_formatted,
                "value": bottom_val,
                "reason": bottom_reason
            },
            "chart_labels": chart_labels,
            "chart_data": chart_data.values.tolist(),
            "active_regions": len(agg)
        }
