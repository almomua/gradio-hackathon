"""
Simple function to download PDF from URL and convert to base64
"""

import base64
import requests


def pdf_url_to_base64(url: str) -> str:
    """
    Download PDF from URL and convert to base64 string.
    
    Args:
        url: URL to the PDF file
        
    Returns:
        Base64 encoded string of the PDF
        
    Example:
        >>> base64_pdf = pdf_url_to_base64("https://arxiv.org/pdf/1506.02640")
        >>> print(f"PDF size: {len(base64_pdf)} characters")
    """
    try:
        # Download the PDF
        print(f"📥 Downloading PDF from: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Raise error for bad status codes
        
        # Convert to base64
        pdf_bytes = response.content
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        
        print(f"✅ PDF downloaded and encoded!")
        print(f"   Size: {len(pdf_bytes):,} bytes")
        print(f"   Base64 length: {len(base64_pdf):,} characters")
        
        return base64_pdf
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading PDF: {e}")
        raise
    except Exception as e:
        print(f"❌ Error encoding PDF: {e}")
        raise


if __name__ == "__main__":
    # Test with YOLO paper
    url = "https://arxiv.org/pdf/1506.02640"
    
    print("\n" + "="*60)
    print("Testing PDF to Base64 Conversion")
    print("="*60 + "\n")
    
    base64_pdf = pdf_url_to_base64(url)
    
    # Show preview of base64 string
    print(f"\n📋 Base64 preview (first 100 chars):")
    print(f"   {base64_pdf[:100]}...")
    
    # Optional: Save to file
    save_option = input("\n💾 Save base64 to file? (y/n): ").lower()
    if save_option == 'y':
        with open("yolo_paper_base64.txt", "w") as f:
            f.write(base64_pdf)
        print("✅ Saved to yolo_paper_base64.txt")

