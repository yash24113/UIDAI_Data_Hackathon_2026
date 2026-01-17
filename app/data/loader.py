
import pandas as pd
import os
import glob

class DataLoader:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.enrolment_df = None
        self.demographic_df = None
        self.biometric_df = None
        
    def load_data(self):
        """Loads data from the three subdirectories."""
        print("Loading Enrolment Data...")
        self.enrolment_df = self._load_csvs_from_dir(os.path.join(self.data_dir, "aadhar_enrolment"))
        self._normalize_enrolment()
        
        print("Loading Demographic Data...")
        self.demographic_df = self._load_csvs_from_dir(os.path.join(self.data_dir, "aadhar_demographic"))
        self._normalize_demographic()
        
        print("Loading Biometric Data...")
        self.biometric_df = self._load_csvs_from_dir(os.path.join(self.data_dir, "aadhar_biometric"))
        self._normalize_biometric()
        
        print("Data Loading Complete.")

    def _load_csvs_from_dir(self, directory):
        all_files = glob.glob(os.path.join(directory, "*.csv"))
        df_list = []
        for filename in all_files:
            try:
                df = pd.read_csv(filename, index_col=None, header=0)
                df_list.append(df)
            except Exception as e:
                print(f"Error reading {filename}: {e}")
        
        if not df_list:
            return pd.DataFrame()
        
        return pd.concat(df_list, axis=0, ignore_index=True)

    def _normalize_enrolment(self):
        # Expected: date,state,district,pincode,age_0_5,age_5_17,age_18_above
        # Check actual columns from provided sample: "date,state,district,pincode,age_0_5,age_5_17,age_18_greater"
        rename_map = {
            "age_18_greater": "age_18_above",
            "age_18_plus": "age_18_above"
        }
        self.enrolment_df.rename(columns=rename_map, inplace=True)
        self._clean_common_columns(self.enrolment_df)

    def _normalize_demographic(self):
        # Expected: date,state,district,pincode,age_5_17,age_18_above
        # Sample headers: date,state,district,pincode,demo_age_5_17,demo_age_17_
        rename_map = {
            "demo_age_5_17": "age_5_17",
            "demo_age_17_": "age_18_above", # Assuming demo_age_17_ means 18 and above or >17
            "demo_age_18_above": "age_18_above"
        }
        self.demographic_df.rename(columns=rename_map, inplace=True)
        self._clean_common_columns(self.demographic_df)

    def _normalize_biometric(self):
        # Sample headers: date,state,district,pincode,bio_age_5_17,bio_age_17_
        rename_map = {
            "bio_age_5_17": "age_5_17",
            "bio_age_17_": "age_18_above",
            "bio_age_18_above": "age_18_above"
        }
        self.biometric_df.rename(columns=rename_map, inplace=True)
        self._clean_common_columns(self.biometric_df)

    def _clean_common_columns(self, df):
        # Standardize State/District names (Title Case, strip whitespace)
        if 'state' in df.columns:
            # canonical mapping (stripped of spaces and lowercase)
            canonical_map = {
                "westbengal": "West Bengal",
                "uttarpradesh": "Uttar Pradesh",
                "andhrapradesh": "Andhra Pradesh",
                "tamilnadu": "Tamil Nadu",
                "telangana": "Telangana",
                "telengana": "Telangana",
                "chhattisgarh": "Chhattisgarh",
                "chattisgarh": "Chhattisgarh",
                "madhyapradesh": "Madhya Pradesh",
                "arunachalpradesh": "Arunachal Pradesh",
                "himachalpradesh": "Himachal Pradesh",
                "jk": "Jammu And Kashmir",
                "jammuandkashmir": "Jammu And Kashmir",
                "dadraandnagarhavelianddamananddiu": "Dadra And Nagar Haveli And Daman And Diu",
                "dnhanddd": "Dadra And Nagar Haveli And Daman And Diu"
            }
            
            def standardize(val):
                val = str(val).strip().lower()
                # Remove spaces, dots, dashes for comparison
                clean = "".join(c for c in val if c.isalnum())
                return canonical_map.get(clean, val.title())

            df['state'] = df['state'].apply(standardize)

        if 'district' in df.columns:
            df['district'] = df['district'].astype(str).str.strip().str.title()
        
        # Ensure numeric columns are numeric
        numeric_cols = ['age_0_5', 'age_5_17', 'age_18_above']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)


# Fix path to be relative to this file
current_dir = os.path.dirname(os.path.abspath(__file__))
# app/data/loader.py -> app/data -> app -> project_root -> Dataset
dataset_path = os.path.join(current_dir, '..', '..', 'Dataset')
loader = DataLoader(dataset_path)
