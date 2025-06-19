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
       
        # Process form elements
        question_id = 0
        for label in section.find_all('label'):
            question = {
                "id": question_id,
                "label": label.text.strip(),
                "answer": ""
            }
            section_data["questions"].append(question)  # Fixed: was appending to sections[0]
            question_id += 1
       
        sections.append(section_data)
   
    # Get title with fallback
    title_tag = soup.find('title')
    title = title_tag.text.strip() if title_tag else "Untitled Document"
    
    return {
        "title": title,
        "metadata": metadata,
        "sections": sections
    }

def save_json_output(data, output_filename=None):
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

# Example usage
if __name__ == "__main__":
    convert_all_html_files()