from fastapi import FastAPI, File, UploadFile, HTTPException
from bs4 import BeautifulSoup
import json
from typing import Dict, Any

app = FastAPI(title="HTML to JSON Converter", version="1.0.0")

def convert_html_to_json(html_content: str) -> Dict[str, Any]:
    """Convert HTML content to JSON format"""
    soup = BeautifulSoup(html_content, 'html.parser')
   
    # Extract metadata
    metadata = {}
    meta_fields = {
        "identifier": 'dcterms.identifier',
        "language": 'dcterms.language',
        "publisher": 'dcterms.publisher',
        "date": 'dcterms.date',
        "creator": 'dcterms.creator'
    }
    
    for key, meta_name in meta_fields.items():
        meta_tag = soup.find('meta', {'name': meta_name})
        metadata[key] = meta_tag['content'] if meta_tag and meta_tag.get('content') else None
   
    # Extract sections
    sections = []
    for section in soup.find_all('section'):
        section_name = section.get('data-section-name')
        if not section_name:
            header = section.find('header')
            section_name = header.text.strip() if header else f"Section {len(sections) + 1}"
        
        section_data = {
            "name": section_name,
            "questions": []
        }
       
        question_id = 0
        
        # Handle textareas (medical report style)
        textareas = section.find_all('textarea')
        if textareas:
            for textarea in textareas:
                textarea_id = textarea.get('id', '')
                label_element = section.find('label', {'for': textarea_id})
                label_text = label_element.text.strip() if label_element and label_element.text.strip() else section_name
                default_content = textarea.text.strip() if textarea.text else ""
                
                question = {
                    "id": question_id,
                    "label": label_text,
                    "answer": default_content,
                    "field_type": textarea.get('data-field-type', 'TEXTAREA'),
                    "element_id": textarea_id
                }
                section_data["questions"].append(question)
                question_id += 1
        
        # Handle labels (original form style)
        else:
            labels = section.find_all('label')
            for label in labels:
                if label.text.strip():
                    question = {
                        "id": question_id,
                        "label": label.text.strip(),
                        "answer": "",
                        "field_type": "LABEL"
                    }
                    section_data["questions"].append(question)
                    question_id += 1
        
        # Fallback: create question from section if no form elements
        if not section_data["questions"]:
            question = {
                "id": 0,
                "label": section_name,
                "answer": "",
                "field_type": "SECTION"
            }
            section_data["questions"].append(question)
       
        sections.append(section_data)
   
    title_tag = soup.find('title')
    title = title_tag.text.strip() if title_tag else "Untitled Document"
    
    return {
        "title": title,
        "metadata": metadata,
        "sections": sections
    }

@app.post("/convert")
async def convert_html_file(file: UploadFile = File(...)):
    """
    Convert uploaded HTML file to JSON format
    
    Args:
        file: HTML file to convert
        
    Returns:
        JSON representation of the HTML form
    """
    if not file.filename.endswith('.html'):
        raise HTTPException(status_code=400, detail="File must be an HTML file")
    
    try:
        # Read file content
        html_content = await file.read()
        html_content = html_content.decode('utf-8')
        
        # Convert to JSON
        result = convert_html_to_json(html_content)
        
        return {
            "status": "success",
            "filename": file.filename,
            "data": result
        }
        
    except UnicodeDecodeError:
        try:
            html_content = html_content.decode('latin-1')
            result = convert_html_to_json(html_content)
            return {
                "status": "success", 
                "filename": file.filename,
                "data": result
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error decoding file: {str(e)}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/")
async def root():
    """API information"""
    return {
        "message": "HTML to JSON Converter API",
        "endpoints": {
            "POST /convert": "Upload HTML file and convert to JSON",
            "GET /": "This information page"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)