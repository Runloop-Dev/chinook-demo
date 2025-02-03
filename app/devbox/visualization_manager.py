import os
import json
import logging
from io import StringIO
import openai
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

class VisualizationManager:
    def __init__(self, openai_api_key=None):
        """
        Initialize VisualizationManager with optional OpenAI API key.
        
        Args:
            openai_api_key (str, optional): OpenAI API key for code generation
        """
        self.logger = logging.getLogger(__name__)
        openai.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')

    def analyze_data_structure(self, query_response: str) -> str:
        """
        Analyzes the structure of query response data as a JSON string.
        
        Args:
            query_response (str): Query result as a JSON string
            
        Returns:
            str: Detailed description of data structure and suitable visualization approaches
        """
        try:
            # Parse JSON string
            data = json.loads(query_response)
            if not data:
                return "Empty dataset"
                
            # Get sample record
            sample_record = data[0]
            
            # Analyze structure
            analysis = []
            analysis.append(f"Dataset contains {len(data)} records")
            
            # Categorize fields
            numeric_fields = []
            date_fields = []
            categorical_fields = []
            
            for field, value in sample_record.items():
                if isinstance(value, (int, float)):
                    numeric_fields.append(field)
                elif isinstance(value, str):
                    # Check if it might be a date
                    if 'date' in field.lower() or 'time' in field.lower():
                        date_fields.append(field)
                    else:
                        categorical_fields.append(field)
                        
            # Add field information
            if numeric_fields:
                analysis.append(f"Numeric fields: {', '.join(numeric_fields)}")
            if date_fields:
                analysis.append(f"Date/Time fields: {', '.join(date_fields)}")
            if categorical_fields:
                analysis.append(f"Categorical fields: {', '.join(categorical_fields)}")
                
            # Suggest visualizations
            suggestions = []
            if date_fields and numeric_fields:
                suggestions.append("Time series plots for temporal analysis")
            if len(numeric_fields) >= 2:
                suggestions.append("Scatter plots or line charts for numeric relationships")
            if categorical_fields and numeric_fields:
                suggestions.append("Bar charts or box plots for categorical-numeric relationships")
            if categorical_fields:
                suggestions.append("Pie charts or bar charts for categorical distributions")
                
            if suggestions:
                analysis.append("Suggested visualizations: " + "; ".join(suggestions))
                
            return "\n".join(analysis)
        except Exception as e:
            self.logger.error(f"Error analyzing data structure: {e}")
            return f"Error analyzing data structure: {str(e)}"

    def generate_visualization_code(self, query_response: str, prompt_description: str) -> str:
        """
        Generate Python code for visualizing JSON string data using OpenAI API.

        Args:
            query_response (str): Query result as a JSON string
            prompt_description (str): Description of how the data should be visualized

        Returns:
            str: Python code for visualization
        """
        try:
            data_analysis = self.analyze_data_structure(query_response)
            
            system_prompt = f"""
            You are an expert data visualization assistant. 
            Generate the raw Python code to visualize JSON string data using pandas and matplotlib.

            Data Structure Analysis:
            {data_analysis}

            Data Sample (as JSON string):
            {query_response}

            Requirements:
            - Convert the JSON string to DataFrame using pd.read_json with StringIO
            - Handle datetime fields appropriately using pd.to_datetime
            - Use matplotlib for visualizations
            - Include proper labels, titles, and legends
            - Match the visualization to the user's description
            - Ensure the code is well-commented
            - Handle potential errors (empty data, missing values, etc.)
            - Use plt.tight_layout() for better spacing
            - Set appropriate figure size using plt.figure(figsize=(width, height))

            VERY IMPORTANT: 
            - Do NOT include any markdown code block markers (```python or ```)
            - Do NOT include any explanatory text
            - Return ONLY the raw Python code itself
            - The code should start directly with Python statements
            - The code should end with the last Python statement
            """

            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt_description}
                ],
                temperature=0.1
            )

            # Get the response and clean it
            code = response.choices[0].message.content.strip()
            
            # Remove any potential markdown code blocks
            if code.startswith('```python'):
                code = code[9:]
            elif code.startswith('```'):
                code = code[3:]
            if code.endswith('```'):
                code = code[:-3]
                
            return code.strip()

        except Exception as e:
            self.logger.error(f"Error generating visualization code: {e}")
            raise

    def visualize_query_results(self, query_response: str, prompt_description: str):
        """
        Generate and execute Python code to visualize query results from JSON string data.

        Args:
            query_response (str): Query results as a JSON string
            prompt_description (str): Description of how the data should be visualized

        Returns:
            dict: Visualization information and potential error
        """
        try:
            # First analyze and print data structure
            data_analysis = self.analyze_data_structure(query_response)
            
            # Generate visualization code
            visualization_code = self.generate_visualization_code(query_response, prompt_description)
            
            # Create DataFrame from JSON string
            df = pd.read_json(StringIO(query_response))
            
            # Convert date columns to datetime
            date_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
            for col in date_columns:
                df[col] = pd.to_datetime(df[col])                        
            
            return {
                'data_analysis': data_analysis,
                'visualization_code': visualization_code,
            }

        except Exception as e:
            self.logger.error(f"Error executing visualization: {e}")
            return {
                'error': str(e),
                'data_analysis': None,
                'visualization_code': None,
                'visualization_path': None
            }