from bs4 import BeautifulSoup
import json
import os

def convert_html_to_json(filename):
    """
    Convert HTML file to JSON format
    
    Args:
        filename (str): Name of the HTML file in the same folder
    
    Returns:
        dict: JSON representation of the HTML content
    """
    # Get the current directory and construct file path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"HTML file '{filename}' not found in the current directory")
    
    # Read HTML content from file
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        with open(file_path, 'r', encoding='latin-1') as file:
            html_content = file.read()
    
    # Check if we actually read HTML content
    if not html_content or len(html_content.strip()) == 0:
        raise ValueError(f"The file '{filename}' appears to be empty")
    
    print(f"Successfully read {len(html_content)} characters from {filename}")
    
    soup = BeautifulSoup(html_content, 'html.parser')
   
    # Extract metadata with error handling
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
        if meta_tag and meta_tag.get('content'):
            metadata[key] = meta_tag['content']
        else:
            metadata[key] = None
            print(f"Warning: Meta tag '{meta_name}' not found or empty")
   
    # Extract sections
    sections = []
    for section in soup.find_all('section'):
        # Get section name with fallback options
        section_name = section.get('data-section-name')
        if not section_name:
            header = section.find('header')
            section_name = header.text.strip() if header else f"Section {len(sections) + 1}"
        
        section_data = {
            "name": section_name,
            "questions": []
        }
       
        # Process form elements - handle both label-only and textarea-based forms
        question_id = 0
        
        # Strategy 1: Look for textareas (medical report style)
        textareas = section.find_all('textarea')
        if textareas:
            for textarea in textareas:
                # Get label text - look for associated label or use section name
                label_text = ""
                textarea_id = textarea.get('id', '')
                
                # Try to find associated label
                label_element = section.find('label', {'for': textarea_id})
                if label_element and label_element.text.strip():
                    label_text = label_element.text.strip()
                else:
                    # Use section name or textarea id as fallback
                    label_text = section_name or textarea_id.replace('Text', '').replace('_', ' ').title()
                
                # Get pre-filled content as default answer
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
        
        # Strategy 2: Look for labels (original form style)
        else:
            labels = section.find_all('label')
            for label in labels:
                if label.text.strip():  # Only process labels with actual text
                    question = {
                        "id": question_id,
                        "label": label.text.strip(),
                        "answer": "",
                        "field_type": "LABEL"
                    }
                    section_data["questions"].append(question)
                    question_id += 1
        
        # Strategy 3: If no form elements found, create a single question from section
        if not section_data["questions"]:
            question = {
                "id": 0,
                "label": section_name,
                "answer": "",
                "field_type": "SECTION"
            }
            section_data["questions"].append(question)
       
        sections.append(section_data)
   
    # Get title with fallback
    title_tag = soup.find('title')
    title = title_tag.text.strip() if title_tag else "Untitled Document"
    
    return {
        "title": title,
        "metadata": metadata,
        "sections": sections
    }

def save_json_output(data, filename):
    """
    Analyze HTML file structure to understand its format
    
    Args:
        filename (str): Name of the HTML file
    
    Returns:
        dict: Analysis results
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)
    
    if not os.path.exists(file_path):
        return {"error": f"File '{filename}' not found"}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as file:
            html_content = file.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    analysis = {
        "filename": filename,
        "title": soup.find('title').text if soup.find('title') else "No title",
        "sections_count": len(soup.find_all('section')),
        "textareas_count": len(soup.find_all('textarea')),
        "labels_count": len(soup.find_all('label')),
        "form_type": "unknown"
    }
    
    # Determine form type
    if analysis["textareas_count"] > 0:
        analysis["form_type"] = "textarea_based"
    elif analysis["labels_count"] > 0:
        analysis["form_type"] = "label_based"
    else:
        analysis["form_type"] = "section_only"
    
    # Get section details
    sections_info = []
    for section in soup.find_all('section'):
        section_name = section.get('data-section-name') or (section.find('header').text.strip() if section.find('header') else "Unnamed")
        textareas_in_section = len(section.find_all('textarea'))
        labels_in_section = len(section.find_all('label'))
        
        sections_info.append({
            "name": section_name,
            "textareas": textareas_in_section,
            "labels": labels_in_section
        })
    
    analysis["sections_details"] = sections_info
    # return analysis
    """
    Save the converted data to a JSON file
    
    Args:
        data (dict): The converted data
        output_filename (str): Optional output filename (defaults to input_name.json)
    """
    if output_filename is None:
        output_filename = "converted_output.json"
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"JSON output saved to: {output_filename}")

def convert_all_html_files():
    """
    Convert all HTML files in the current directory to JSON
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_files = [f for f in os.listdir(current_dir) if f.endswith('.html')]
    
    if not html_files:
        print("No HTML files found in the current directory.")
        print(f"Available files: {os.listdir(current_dir)}")
        return
    
    print(f"Found {len(html_files)} HTML files: {html_files}")
    print("="*60)
    
    # First, analyze all files to understand their structure
    print("\nANALYZING FILE STRUCTURES:")
    print("-" * 40)
    for html_file in html_files:
        analysis = analyze_html_structure(html_file)
        if "error" not in analysis:
            print(f"{html_file}:")
            print(f"  - Type: {analysis['form_type']}")
            print(f"  - Sections: {analysis['sections_count']}")
            print(f"  - Textareas: {analysis['textareas_count']}")
            print(f"  - Labels: {analysis['labels_count']}")
    
    print("\n" + "="*60)
    print("CONVERTING FILES:")
    print("="*60)
    
    successful_conversions = 0
    failed_conversions = 0
    
    for i, html_filename in enumerate(html_files, 1):
        print(f"\n[{i}/{len(html_files)}] Processing: {html_filename}")
        print("-" * 40)
        
        try:
            result = convert_html_to_json(html_filename)
            
            # Save to JSON file
            output_name = html_filename.replace('.html', '.json')
            save_json_output(result, output_name)
            
            # Print summary of this file
            print(f"✓ Successfully converted '{html_filename}'")
            print(f"  - Title: {result['title']}")
            print(f"  - Sections: {len(result['sections'])}")
            total_questions = sum(len(section['questions']) for section in result['sections'])
            print(f"  - Total questions: {total_questions}")
            
            # Show question types
            field_types = []
            for section in result['sections']:
                for question in section['questions']:
                    field_type = question.get('field_type', 'UNKNOWN')
                    if field_type not in field_types:
                        field_types.append(field_type)
            print(f"  - Field types: {', '.join(field_types)}")
            print(f"  - Output: {output_name}")
            
            successful_conversions += 1
            
        except Exception as e:
            print(f"✗ Failed to convert '{html_filename}': {e}")
            failed_conversions += 1
            # Optionally print full traceback for debugging
            # import traceback
            # traceback.print_exc()
    
    # Final summary
    print("\n" + "="*60)
    print("CONVERSION SUMMARY")
    print("="*60)
    print(f"Total files processed: {len(html_files)}")
    print(f"Successful conversions: {successful_conversions}")
    print(f"Failed conversions: {failed_conversions}")
    
    if successful_conversions > 0:
        print(f"\nJSON files created:")
        for html_file in html_files:
            json_file = html_file.replace('.html', '.json')
            if os.path.exists(json_file):
                print(f"  - {json_file}")

def analyze_html_structure(filename):
    """
    Analyze HTML file structure to understand its format
    
    Args:
        filename (str): Name of the HTML file
    
    Returns:
        dict: Analysis results
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)
    
    if not os.path.exists(file_path):
        return {"error": f"File '{filename}' not found"}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as file:
            html_content = file.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    analysis = {
        "filename": filename,
        "title": soup.find('title').text if soup.find('title') else "No title",
        "sections_count": len(soup.find_all('section')),
        "textareas_count": len(soup.find_all('textarea')),
        "labels_count": len(soup.find_all('label')),
        "form_type": "unknown"
    }
    
    # Determine form type
    if analysis["textareas_count"] > 0:
        analysis["form_type"] = "textarea_based"
    elif analysis["labels_count"] > 0:
        analysis["form_type"] = "label_based"
    else:
        analysis["form_type"] = "section_only"
    
    # Get section details
    sections_info = []
    for section in soup.find_all('section'):
        section_name = section.get('data-section-name') or (section.find('header').text.strip() if section.find('header') else "Unnamed")
        textareas_in_section = len(section.find_all('textarea'))
        labels_in_section = len(section.find_all('label'))
        
        sections_info.append({
            "name": section_name,
            "textareas": textareas_in_section,
            "labels": labels_in_section
        })
    
    analysis["sections_details"] = sections_info
    return analysis

# Example usage
if __name__ == "__main__":
    convert_all_html_files()