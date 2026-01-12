
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
        if state_filter:
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

    # Idea 1: District-Level Activity Insights
    def idea_1_district_activity(self, state_filter=None, district_filter=None):
        e_df = self.loader.enrolment_df
        d_df = self.loader.demographic_df
        b_df = self.loader.biometric_df

        # Filter
        e_df = self.filter_data(e_df, state_filter, district_filter)
        d_df = self.filter_data(d_df, state_filter, district_filter)
        b_df = self.filter_data(b_df, state_filter, district_filter)

        # Default to State-wise if no filter, else District-wise
        group_col = 'state' if not state_filter and not district_filter else 'district'
        
        e_grp = e_df.groupby(group_col)[['age_0_5', 'age_5_17', 'age_18_above']].sum().sum(axis=1)
        d_grp = d_df.groupby(group_col)[['age_5_17', 'age_18_above']].sum().sum(axis=1)
        b_grp = b_df.groupby(group_col)[['age_5_17', 'age_18_above']].sum().sum(axis=1)

        total_activity = (e_grp.add(d_grp, fill_value=0).add(b_grp, fill_value=0)).sort_values(ascending=False).head(15)
        
        return self._format_response(1, total_activity.index.tolist(), total_activity.values.tolist(), 
                                     f"Top 15 {group_col}s by Enrolment + Update activity.")

    # Idea 2: Biometric Update Camps
    def idea_2_biometric_camps(self, state_filter=None):
        d_df = self.filter_data(self.loader.demographic_df, state_filter)
        b_df = self.filter_data(self.loader.biometric_df, state_filter)

        # Always analyze by district for finding camps
        d_grp = d_df.groupby('district')[['age_5_17', 'age_18_above']].sum().sum(axis=1)
        b_grp = b_df.groupby('district')[['age_5_17', 'age_18_above']].sum().sum(axis=1)

        merged = pd.concat([d_grp, b_grp], axis=1, keys=['demo', 'bio']).fillna(0)
        merged = merged[merged['demo'] > 100] 
        merged['bio_ratio'] = merged['bio'] / merged['demo']
        
        target_districts = merged.sort_values('bio_ratio').head(10)

        return self._format_response(2, target_districts.index.tolist(), target_districts['bio_ratio'].round(2).tolist(), 
                                     "Districts with lowest Biometric/Demographic update ratio.")

    # Idea 3: Zero-Knowledge Age Verifier
    def idea_3_age_verifier(self, state_filter=None):
        e_df = self.loader.enrolment_df
        e_df = self.filter_data(e_df, state_filter)
        
        group_col = 'state' if not state_filter else 'district'
        
        if 'age_18_above' not in e_df.columns: return self._format_response(3, [], [], "No 18+ data.")
        
        voter_potential = e_df.groupby(group_col)['age_18_above'].sum().sort_values(ascending=False).head(10)
        
        return self._format_response(3, voter_potential.index.tolist(), voter_potential.values.tolist(), 
                                     f"Top {group_col}s with new adult enrolment.")

    # Idea 4: Ghost Child Indicator
    def idea_4_ghost_child(self, state_filter=None):
        e_df = self.loader.enrolment_df
        e_df = self.filter_data(e_df, state_filter)
        
        # Analyze by district to find specific problem areas
        grp = e_df.groupby('district')['age_0_5'].sum()
        mean_enrolment = grp.mean()
        
        low_enrolment = grp[grp < (0.2 * mean_enrolment)].sort_values().head(10)
        
        return self._format_response(4, low_enrolment.index.tolist(), low_enrolment.values.tolist(), 
                                     f"Districts with anomalously low 0-5 child enrolment (Avg: {int(mean_enrolment)}).")

    # Idea 5: Integrity Shield
    def idea_5_integrity_shield(self):
        d_df = self.loader.demographic_df
        # Anomaly detection ideally needs granular data. Using Pincode aggregations.
        daily_pincode_activity = d_df.groupby(['date', 'pincode']).size().reset_index(name='count')
        anomalies = daily_pincode_activity[daily_pincode_activity['count'] > 50].head(10)
        
        return self._format_response(5, anomalies['pincode'].astype(str).tolist(), anomalies['count'].tolist(), 
                                     "Pincodes with unusual daily update volume spikes.")

    # Idea 6: Placeholder
    def idea_6_financial(self):
        return self._format_response(6, [], [], "Data not available.")

    # Idea 7: Language Support
    def idea_7_language_support(self, state_filter=None):
        lang_map = {
            "Karnataka": "Kannada", "Maharashtra": "Marathi", "Gujarat": "Gujarati", 
            "Tamil Nadu": "Tamil", "Kerala": "Malayalam", "Uttar Pradesh": "Hindi",
            "Bihar": "Hindi", "West Bengal": "Bengali", "Andhra Pradesh": "Telugu",
            "Telangana": "Telugu", "Punjab": "Punjabi", "Odisha": "Odia"
        }
        
        e_df = self.filter_data(self.loader.enrolment_df, state_filter)
        state_activity = e_df.groupby('state')[['age_0_5', 'age_5_17', 'age_18_above']].sum().sum(axis=1).sort_values(ascending=False).head(10)
        
        labels = state_activity.index.tolist()
        languages = [lang_map.get(s, "Hindi/English") for s in labels]
        
        return self._format_response(7, labels, state_activity.values.tolist(), 
                                     "Top states and recommended local languages.", extra_info=languages)

    # Idea 8: Center Health Monitor
    def idea_8_health_monitor(self):
        d_df = self.loader.demographic_df
        b_df = self.loader.biometric_df
        
        d_pin = d_df.groupby('pincode').size()
        b_pin = b_df.groupby('pincode').size()
        
        merged = pd.concat([d_pin, b_pin], axis=1, keys=['demo_count', 'bio_count']).fillna(0)
        faulty_centers = merged[(merged['demo_count'] > 50) & (merged['bio_count'] < 5)].sort_values('demo_count', ascending=False).head(10)
        
        return self._format_response(8, faulty_centers.index.astype(str).tolist(), faulty_centers['demo_count'].tolist(), 
                                     "Pincodes with potential biometric equipment failure.")

    # Idea 9: Disaster Relief
    def idea_9_disaster_planning(self, state_filter=None):
        disaster_districts = ["Cuddalore", "Nagapattinam", "Puri", "Kendrapara", "Darbhanga", "Gorakhpur", "Wayand", "Chamoli"]
        
        d_df = self.filter_data(self.loader.demographic_df, state_filter)
        d_df = d_df[d_df['district'].isin(disaster_districts)]
        
        if d_df.empty: return self._format_response(9, [], [], "No filtered disaster districts found.")

        district_updates = d_df.groupby('district')[['age_5_17', 'age_18_above']].sum().sum(axis=1).sort_values(ascending=False)
        return self._format_response(9, district_updates.index.tolist(), district_updates.values.tolist(), 
                                     "Demographic updates in designated disaster-prone zones.")

    # Idea 10: Urban Traffic
    def idea_10_urban_traffic(self, state_filter=None):
        urban_districts = ["Bengaluru", "Mumbai", "Pune", "Chennai", "Hyderabad", "Ahmedabad", "Gurgaon", "Noida", "Kolkata", "Delhi"]
        
        merged_df = pd.concat([self.loader.enrolment_df, self.loader.demographic_df, self.loader.biometric_df])
        merged_df = self.filter_data(merged_df, state_filter)
        
        urban_data = merged_df[merged_df['district'].isin(urban_districts)]
        pincode_traffic = urban_data.groupby(['district', 'pincode']).size().sort_values(ascending=False).head(10)
        
        labels = [f"{idx[0]}-{idx[1]}" for idx in pincode_traffic.index]
        return self._format_response(10, labels, pincode_traffic.values.tolist(), 
                                     "High-traffic urban pincodes recommended for queue management.")
