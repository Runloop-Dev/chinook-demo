import os
import json
import logging
from io import StringIO
import openai
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisualizationManager:
    def __init__(self, openai_api_key=None):
        """Initialize VisualizationManager with optional OpenAI API key."""
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
            import json
            
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
            logger.error(f"Error analyzing data structure: {e}")
            return f"Error analyzing data structure: {str(e)}"

    def generate_visualization_code(self, query_response: str, visualization_type: str) -> str:
        """
        Generate Python code for creating the specified visualization.
        
        Args:
            query_response (str): Query result as a JSON string
            visualization_type (str): Type of visualization to generate
            
        Returns:
            str: Python code that will print JSON visualization data to stdout
        """
        try:
            system_prompt = """Generate Python code that produces a visualization-ready JSON output.

            Required output format:
            {
                "labels": [...],  # X-axis labels
                "datasets": [{
                    "label": "Dataset Label",
                    "data": [...]  # Y-axis values
                }],
                "type": "chart_type"
            }

            Requirements:
            - Process input JSON string to create visualization data
            - Round numeric values to 2 decimal places
            - Make sure the output JSON is valid
            - Make sure to not use decimal but use float for numeric values to avoid JSON serialization issues
            - Print only the final JSON output string
            - No explanatory text or comments
            - No markdown formatting"""

            user_prompt = f"""Create a {visualization_type} visualization for this data:
            {query_response}"""

            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            
            code = response.choices[0].message.content.strip()
            
            # Clean up any markdown
            if code.startswith('```python'):
                code = code[9:]
            if code.endswith('```'):
                code = code[:-3]
                
            return code.strip()

        except Exception as e:
            self.logger.error(f"Error generating visualization code: {e}")
            raise
        
    def get_visualization_data(self, query_response: str, visualization_type: str) -> dict:
        """
        Generate visualization code and prepare response for frontend.
        
        Args:
            query_response (str): Query results as a JSON string
            visualization_type (str): Type of visualization to generate
            
        Returns:
            dict: Visualization code and metadata
        """
        try:
            code = self.generate_visualization_code(query_response, visualization_type)
                        
            return {
                'code': code,
                'data': query_response,
                'type': visualization_type
            }
        except Exception as e:
            self.logger.error(f"Error preparing visualization: {e}")
            return {'error': str(e)}