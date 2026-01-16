import os
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd
import json
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

class GeminiAnalyzer:
    def __init__(self):
        """Initialize the Gemini API client."""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-flash-latest')
        self.chat_session = None

    def start_chat(self, history=None):
        """Start a new chat session."""
        self.chat_session = self.model.start_chat(history=history or [])
        return self.chat_session

    
    def chat_response(self, message: str, context: str = "", image_data: bytes = None, language: str = 'en') -> str:
        """
        Get a chat response from Gemini.
        """
        if not self.chat_session:
            self.start_chat()

        lang_map = {
            'hi': 'Hindi (Devanagari script)',
            'gu': 'Gujarati',
            'en': 'English'
        }
        target_lang = lang_map.get(language, 'English')

        prompt_parts = []
        
        system_instruction = f"""
        You are 'Aadhaar Sahayak', an advanced AI assistant for the UIDAI Data Hackathon 2026.
        Your goal is to provide deeply analytical, comprehensive, and helpful responses regarding Aadhaar enrolment, demographic, and biometric data.
        
        **CRITICAL INSTRUCTION**: You MUST provide your ENTIRE response in **{target_lang}**.
        
        Data Context Summary:
        {context}
        
        Guidelines for Response:
        1. **Adaptive Analysis**:
            - IF specific State/District data is provided in the context (under "SPECIFIC DATA FOR..."), YOU MUST USE IT.
            - Provide a deeper analysis for these regions, comparing them to national averages if possible.
        2. **Structured Format (CRITICAL)**:
            - **Observation**: What does the data show? (Cite specific numbers).
            - **Reasoning**: Why might this be the case? (Infer from demographics, urbanization, or known socio-economic factors).
            - **Solution**: What actionable steps can the government take? (Be specific: e.g., "Mobile vans for rural updates", "Camp mode for biometrics").
        3. **Tone & Style**:
            - Professional, data-driven, yet accessible.
            - Use Markdown tables for comparisons.
            - **Strictly adhere to {target_lang}**.
        4. **General Q&A**:
            - If the user asks a simple fact, keep it brief.
            - If they ask for "State wise" or "District wise" analysis, summarize the key leaders/laggards from the provided Top 10/Top 5 lists.
        """

        if image_data:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(image_data))
            prompt_parts.append(img)
        
        full_prompt = f"{system_instruction}\n\nUser Message: {message}"
        prompt_parts.append(full_prompt)

        try:
            response = self.chat_session.send_message(prompt_parts)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

    def analyze_data(self, data: pd.DataFrame, analysis_type: str = "insights") -> str:
        """
        Analyze the given data using Gemini and return insights.
        """
        data_sample = data.head().to_string()
        data_columns = "\n".join([f"- {col}" for col in data.columns])
        
        prompt = f"""
        Analyze this government data sample ({analysis_type}):
        {data_sample}
        
        Columns: {data_columns}
        
        Provide key observations, trends, and recommendations in markdown.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

    def generate_visualization_suggestions(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Suggest appropriate visualizations for the given data.
        """
        data_sample = data.head().to_string()
        prompt = f"Suggest JSON visualizations for this data sample:\n{data_sample}"
        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            return {"error": str(e)}

def load_data(file_path: str) -> pd.DataFrame:
    """
    Load data from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        pd.DataFrame: Loaded data
    """
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        raise Exception(f"Error loading data: {str(e)}")

if __name__ == "__main__":
    # Example usage
    try:
        # Initialize the analyzer
        analyzer = GeminiAnalyzer()
        
        # Example: Load data (replace with your actual data path)
        # data = load_data("path/to/your/data.csv")
        
        # Example: Generate insights
        # insights = analyzer.analyze_data(data, "insights")
        # print("\nInsights:", insights)
        
        # Example: Get visualization suggestions
        # viz_suggestions = analyzer.generate_visualization_suggestions(data)
        # print("\nVisualization Suggestions:", json.dumps(viz_suggestions, indent=2))
        
        print("Gemini Analyzer initialized successfully!")
        print("To use this module, import it and create an instance of GeminiAnalyzer.")
        
    except Exception as e:
        print(f"Error: {str(e)}")
