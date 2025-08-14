"""
Data Processor Service - Handles zip file extraction and AI-powered data reformatting
"""

import os
import zipfile
import tempfile
import pandas as pd
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from .gemini_service import GeminiService

logger = logging.getLogger(__name__)

class DataProcessorService:
    """Service for processing zip files and reformatting data with AI assistance"""
    
    def __init__(self):
        try:
            self.gemini_service = GeminiService()
        except ValueError as e:
            logger.warning(f"Gemini service not available: {e}")
            self.gemini_service = None
        self.supported_formats = ['.csv', '.json', '.xlsx', '.xls', '.txt']
        
    def process_zip_file(self, zip_path: str, target_schema: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a zip file containing data files
        
        Args:
            zip_path: Path to the zip file
            target_schema: Optional target schema for reformatting
            
        Returns:
            Dict containing processing results
        """
        try:
            # Extract zip file
            extracted_data = self._extract_zip_file(zip_path)
            if not extracted_data['success']:
                return extracted_data
            
            # Process extracted files
            processed_data = self._process_extracted_files(extracted_data['files'])
            
            # Apply AI reformatting if schema provided
            if target_schema:
                reformatted_data = self._reformat_with_ai(processed_data, target_schema)
            else:
                reformatted_data = self._basic_reformat(processed_data)
            
            return {
                'success': True,
                'original_data': processed_data,
                'reformatted_data': reformatted_data,
                'schema_used': target_schema or self._generate_basic_schema(processed_data)
            }
            
        except Exception as e:
            logger.error(f"Error processing zip file: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_zip_file(self, zip_path: str) -> Dict[str, Any]:
        """Extract files from zip archive"""
        try:
            extracted_files = []
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Create temporary directory
                temp_dir = tempfile.mkdtemp()
                
                # Extract all files
                zip_ref.extractall(temp_dir)
                
                # Process extracted files
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_ext = Path(file).suffix.lower()
                        
                        if file_ext in self.supported_formats:
                            extracted_files.append({
                                'name': file,
                                'path': file_path,
                                'extension': file_ext,
                                'size': os.path.getsize(file_path)
                            })
            
            return {
                'success': True,
                'files': extracted_files,
                'temp_dir': temp_dir
            }
            
        except Exception as e:
            logger.error(f"Error extracting zip file: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_extracted_files(self, files: List[Dict]) -> Dict[str, Any]:
        """Process extracted files into structured data"""
        processed_data = {}
        
        for file_info in files:
            try:
                file_path = file_info['path']
                file_name = file_info['name']
                file_ext = file_info['extension']
                
                if file_ext == '.csv':
                    df = pd.read_csv(file_path)
                    processed_data[file_name] = {
                        'type': 'dataframe',
                        'data': df.to_dict('records'),
                        'columns': df.columns.tolist(),
                        'shape': df.shape,
                        'dtypes': df.dtypes.to_dict()
                    }
                    
                elif file_ext == '.json':
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    processed_data[file_name] = {
                        'type': 'json',
                        'data': data
                    }
                    
                elif file_ext in ['.xlsx', '.xls']:
                    df = pd.read_excel(file_path)
                    processed_data[file_name] = {
                        'type': 'dataframe',
                        'data': df.to_dict('records'),
                        'columns': df.columns.tolist(),
                        'shape': df.shape,
                        'dtypes': df.dtypes.to_dict()
                    }
                    
                elif file_ext == '.txt':
                    with open(file_path, 'r') as f:
                        content = f.read()
                    processed_data[file_name] = {
                        'type': 'text',
                        'data': content
                    }
                    
            except Exception as e:
                logger.error(f"Error processing file {file_info['name']}: {e}")
                processed_data[file_name] = {
                    'type': 'error',
                    'error': str(e)
                }
        
        return processed_data
    
    def _reformat_with_ai(self, data: Dict[str, Any], target_schema: Dict) -> Dict[str, Any]:
        """Use AI to reformat data according to target schema"""
        try:
            # Check if Gemini service is available
            if not self.gemini_service:
                logger.warning("Gemini service not available, using basic reformatting")
                return {
                    'fallback_data': self._basic_reformat(data),
                    'note': 'AI service not available, used basic reformatting'
                }
            
            # Prepare data summary for AI
            data_summary = self._create_data_summary(data)
            
            # Create prompt for AI reformatting
            prompt = f"""
            Please reformat the following data according to the target schema.
            
            Data Summary:
            {json.dumps(data_summary, indent=2)}
            
            Target Schema:
            {json.dumps(target_schema, indent=2)}
            
            Please provide:
            1. Reformatted data structure
            2. Data quality assessment
            3. Recommendations for ML usage
            4. Any data issues found
            
            Return as JSON format.
            """
            
            # Get AI response
            ai_response = self.gemini_service.generate_content(prompt)
            
            # Parse AI response
            try:
                ai_result = json.loads(ai_response)
            except json.JSONDecodeError:
                # Fallback to basic reformatting if AI response is not valid JSON
                ai_result = {
                    'reformatted_data': self._basic_reformat(data),
                    'ai_response': ai_response,
                    'note': 'AI response was not valid JSON, used basic reformatting'
                }
            
            return {
                'gemini_analysis': ai_result,
                'reformatted_data': ai_result.get('reformatted_data', self._basic_reformat(data)),
                'recommendations': ai_result.get('recommendations', []),
                'data_quality': ai_result.get('data_quality', {})
            }
            
        except Exception as e:
            logger.error(f"Error in AI reformatting: {e}")
            return {
                'error': str(e),
                'fallback_data': self._basic_reformat(data)
            }
    
    def _basic_reformat(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Basic data reformatting without AI"""
        reformatted = {}
        
        for file_name, file_data in data.items():
            if file_data['type'] == 'dataframe':
                df = pd.DataFrame(file_data['data'])
                
                # Basic cleaning
                df = df.drop_duplicates()
                df = df.fillna(method='ffill')
                
                reformatted[file_name] = {
                    'cleaned_data': df.to_dict('records'),
                    'shape': df.shape,
                    'columns': df.columns.tolist()
                }
        
        return reformatted
    
    def _generate_basic_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a basic ML schema from data"""
        schema = {
            'fields': {},
            'target_variable': None,
            'ml_task': 'classification'
        }
        
        # Analyze first dataframe to suggest schema
        for file_name, file_data in data.items():
            if file_data['type'] == 'dataframe' and file_data.get('columns'):
                for col in file_data['columns']:
                    # Basic type inference
                    if 'price' in col.lower() or 'value' in col.lower():
                        schema['fields'][col] = {'type': 'float', 'description': 'Numeric value'}
                        if not schema['target_variable']:
                            schema['target_variable'] = col
                            schema['ml_task'] = 'regression'
                    elif 'id' in col.lower():
                        schema['fields'][col] = {'type': 'string', 'description': 'Identifier'}
                    elif 'date' in col.lower() or 'time' in col.lower():
                        schema['fields'][col] = {'type': 'datetime', 'description': 'Date/time field'}
                    else:
                        schema['fields'][col] = {'type': 'string', 'description': 'General field'}
                break
        
        return schema
    
    def _create_data_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the data for AI processing"""
        summary = {}
        
        for file_name, file_data in data.items():
            if file_data['type'] == 'dataframe':
                summary[file_name] = {
                    'type': 'dataframe',
                    'columns': file_data.get('columns', []),
                    'shape': file_data.get('shape', [0, 0]),
                    'sample_data': file_data.get('data', [])[:3]  # First 3 rows
                }
            else:
                summary[file_name] = {
                    'type': file_data['type'],
                    'preview': str(file_data.get('data', ''))[:200]  # First 200 chars
                }
        
        return summary
    
    def export_processed_data(self, processed_data: Dict[str, Any], output_format: str) -> Optional[str]:
        """Export processed data to specified format"""
        try:
            # Create output directory
            output_dir = tempfile.mkdtemp()
            
            if output_format == 'csv':
                output_file = os.path.join(output_dir, 'processed_data.csv')
                # Convert to DataFrame and save
                if 'reformatted_data' in processed_data:
                    for file_name, file_data in processed_data['reformatted_data'].items():
                        if 'cleaned_data' in file_data:
                            df = pd.DataFrame(file_data['cleaned_data'])
                            df.to_csv(output_file, index=False)
                            return output_file
            
            elif output_format == 'json':
                output_file = os.path.join(output_dir, 'processed_data.json')
                with open(output_file, 'w') as f:
                    json.dump(processed_data, f, indent=2)
                return output_file
            
            return None
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return None