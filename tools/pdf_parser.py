import fitz  # PyMuPDF
import requests
import io
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_pdf_from_url(url: str) -> str:
    """
    Downloads a PDF from a URL and extracts its text content.
    
    Args:
        url (str): The URL of the PDF file.
        
    Returns:
        str: The extracted text from the PDF, or an error message.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=20, stream=True)
        response.raise_for_status()
        
        # Open the PDF from the content stream
        with fitz.open(stream=response.content, filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
        
        if not text:
            logging.warning(f"Could not extract text from PDF at {url}. The document might be image-based.")
            return "No text could be extracted from this PDF."
            
        logging.info(f"Successfully parsed PDF from URL: {url}")
        return text
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download PDF from {url}. Error: {e}")
        return f"Error: Could not download PDF. {e}"
    except Exception as e:
        logging.error(f"An error occurred while parsing the PDF from {url}. Error: {e}")
        return f"Error: Could not parse PDF. {e}"
