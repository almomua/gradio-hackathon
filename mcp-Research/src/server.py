"""
Run from the repository root:
    uv run examples/snippets/servers/streamable_config.py
"""

import base64
import os
from mcp.server.fastmcp import FastMCP
import arxiv
from google import genai
from google.genai import types
from serpapi import GoogleSearch
from dotenv import load_dotenv
import json
import requests
import io
import httpx

# Load environment variables from .env file FIRST, before anything else
load_dotenv(override=True)

# Verify environment variables are loaded
serpapi_key = os.getenv('SERPAPI_API_KEY')
gemini_key = os.getenv('GEMINI_API_KEY')

if not serpapi_key:
    print("⚠️  WARNING: SERPAPI_API_KEY not found in .env file")
if not gemini_key:
    print("⚠️  WARNING: GEMINI_API_KEY not found in .env file")


mcp = FastMCP(
    "Research Server",
    stateless_http=True,
    host=os.getenv('BL_SERVER_HOST', "0.0.0.0"),
    port=os.getenv('BL_SERVER_PORT', "80")
)

@mcp.tool()
def retrieve_related_papers(topic: str, max_results: int = 3) -> str:
    """
    Retrieve the top N relevant research papers for a given research topic using SerpApi Google Scholar.
    Uses direct HTTP requests (same as SerpApi Playground).
    
    Args:
        topic: The research topic or keywords to search for.
        max_results: Maximum number of papers to return (default: 3).
    
    Returns:
        Formatted string with paper details (title, authors, publication date, link, summary).
    """
    try:
        # Get API key from environment
        api_key = os.getenv('SERPAPI_API_KEY')
        
        if not api_key or api_key.strip() == '':
            return "❌ Error: SERPAPI_API_KEY is empty or not set in .env file"
        
        print(f"\n[retrieve_related_papers] Using API key: {api_key[:10]}...{api_key[-10:]}")
        print(f"[retrieve_related_papers] Searching for: {topic}")
        
        # SerpApi Scholar endpoint (same as Playground uses)
        url = "https://google.serper.dev/scholar"
        
        # Prepare headers with API key
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }
        
        # Prepare payload
        payload = json.dumps({
            "q": topic,
            "num": max_results
        })
        
        print(f"[retrieve_related_papers] Making HTTP request to {url}")
        
        # Make the HTTP POST request
        response = requests.request("POST", url, headers=headers, data=payload)
        
        print(f"[retrieve_related_papers] Response status: {response.status_code}")
        
        # Check if request was successful
        if response.status_code != 200:
            error_text = response.text
            print(f"[retrieve_related_papers] Error response: {error_text}")
            return f"SerpApi Error (HTTP {response.status_code}): {error_text}"
        
        # Parse response
        results = response.json()
        
        # Check for API errors in response
        if "error" in results:
            error_msg = results['error']
            print(f"[retrieve_related_papers] API Error: {error_msg}")
            return f"SerpApi Error: {error_msg}"
        
        papers = []
        
        # Extract results from the response
        if "organic" in results:
            print(f"[retrieve_related_papers] Found {len(results['organic'])} results")
            
            for result in results["organic"][:max_results]:
                title = result.get("title", "Unknown Title")
                link = result.get("link", "N/A")
                publication = result.get("publication", "Unknown Publication")
                snippet = result.get("snippet", "No summary available")
                
                # Citation info might be in different formats
                cited_by = result.get("cited_by", 0)
                
                paper_info = (
                    f"Title: {title}\n"
                    f"Publication: {publication}\n"
                    f"Link: {link}\n"
                    f"Summary: {snippet}\n"
                    f"Citations: {cited_by}"
                )
                papers.append(paper_info)
        
        if not papers:
            print(f"[retrieve_related_papers] No papers found")
            return f"No research papers found for topic: {topic}"
        
        print(f"[retrieve_related_papers] Successfully retrieved {len(papers)} papers")
        return "\n\n".join(papers)
        
    except Exception as e:
        error_msg = f"Error retrieving papers with SerpApi: {str(e)}"
        print(f"[retrieve_related_papers] {error_msg}")
        import traceback
        traceback.print_exc()
        return error_msg



@mcp.tool()
def explain_paper(paper_url: str) -> str:
    """
    Explain and summarize a research paper using Gemini 3 Pro with URL context.
    The AI will fetch the paper content from the URL and provide a simplified explanation.
    
    Args:
        paper_url: The URL link to the research paper (e.g., arXiv link or PDF URL).
    """
    try:
        # Initialize Gemini client
        client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
        )

        # Updated to Gemini 3 Pro Preview
        model = "gemini-3-pro-preview"
        
        prompt = f"Please analyze and explain the research paper at this URL: {paper_url}"
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        
        # Configure URL context tool
        tools = [
            types.Tool(url_context=types.UrlContext()),
        ]
        
        # Detailed system instruction
        system_instruction = """You are an AI model designed to serve as a scientific content summarizer and simplifier. Your role is to read and process complex scientific input documents or content, including research papers, journal articles, and technical reports across various scientific disciplines. Your core responsibilities include:

Key Information Extraction: Identify and extract the central hypotheses, methodologies, key results, conclusions, and critical data from the source material.

Simplification of Language: Translate technical and discipline-specific jargon into clear, straightforward language suitable for non-expert audiences such as students, educators, and professionals from other domains.

Structured Summarization: Present information using structured formats, such as:
- Short abstract 
- Bullet points or short paragraphs for major findings
- Step-by-step descriptions of experimental methods
- Clear headings and subheadings for logical flow

Constraints:
- Maintain the scientific accuracy and integrity of the original content.
- Omit overly detailed technical explanations that are not essential to understanding the main points.
- Avoid oversimplification that could distort or misrepresent scientific findings.
- Tailor output to be educational and accessible, bridging the gap between experts and general audiences.
- Whenever possible, use simplified examples for better explanation. 

Purpose:
Your output serves as an educational tool that enhances comprehension, facilitates interdisciplinary learning, and supports informed decision-making by making complex scientific information digestible and useful to a broader audience

The final output must be:
1) Keep the names (persons, organizations, technical terms, algorithms, approaches, methods, places, organizations, etc.)
3) Accurate, clear, simple and interesting.
4) Keep the output in 500 to 600 words or less.
5) ONLY if applicable, add a table of pros and another table of cons of the provided input. In the tables, do not try to invent unrelated pros and cons. Make the tables accurate and clear. In the tables, use English for names  (persons, organizations, technical terms, algorithms, approaches, methods, places, organizations, etc.).  
6) At the end add a short paragraph as a final summary.

Finally, add a list of the related fundamental key topics that user should study to fully comprehend the input."""
        
        # Configure generation with Thinking and Tools
        generate_content_config = types.GenerateContentConfig(
            tools=tools,
            # Enable Thinking feature for Gemini 3
            thinking_config=types.ThinkingConfig(
                include_thoughts=True 
            ),
            system_instruction=[
                types.Part.from_text(text=system_instruction),
            ],
        )

        # Generate content using streaming
        response_text = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                response_text += chunk.text
        
        return response_text if response_text else "No explanation could be generated for the provided URL."
        
    except Exception as e:
        return f"Error explaining paper: {str(e)}\nPlease ensure GEMINI_API_KEY is set and you have access to the Gemini 3 Pro preview."

@mcp.tool()
def paper_to_poster(paper_url: str) -> str:
    """
    Generate a scientific poster from a research paper URL and return a public image link.
    
    The tool:
    1. Downloads the paper and processes it with Gemini 3 Pro.
    2. Generates a visual poster (image).
    3. Uploads the image to ImgBB.
    4. Returns a public URL to the poster.
    
    Args:
        paper_url: The URL link to the research paper (PDF).
    
    Returns:
        str: A public URL link to the generated poster image.
    """
    try:
        # Check for ImgBB key first to fail fast if missing
        imgbb_key = os.environ.get("IMGBB_API_KEY")
        if not imgbb_key:
            return "Error: IMGBB_API_KEY not found in environment variables. Please get a free key from api.imgbb.com"

        client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
        )

        # --- Step 1: Download & Upload PDF to Gemini ---
        print(f"[paper_to_poster] Downloading paper from: {paper_url}")
        
        # httpx handles redirects automatically with follow_redirects=True
        response = httpx.get(paper_url, follow_redirects=True)
        
        # Check if the request was successful
        if response.status_code != 200:
            return f"Error downloading PDF: HTTP {response.status_code}"
            
        # Create bytes buffer from content
        doc_io = io.BytesIO(response.content)
        
        print("[paper_to_poster] Uploading PDF to Gemini Files API...")
        uploaded_file = client.files.upload(
            file=doc_io,
            config=dict(mime_type='application/pdf')
        )

        # --- Step 2: Generate Poster Image ---
        # Using Nano Banana Pro (Gemini 3 Pro Image)
        model = "gemini-3-pro-image-preview"
        
        print("[paper_to_poster] Generating poster content...")
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="Generate a visual scientific poster from this paper."),
                    types.Part.from_uri(
                        file_uri=uploaded_file.uri,
                        mime_type=uploaded_file.mime_type
                    ),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
            image_config=types.ImageConfig(
                aspect_ratio="16:9",
                image_size="1K",
            ),
            system_instruction=[
                types.Part.from_text(text="""You are an expert scientific communicator and infographic designer. Your task is to create a clear, structured, visually professional infographic summarizing the research paper provided below.

Context & Audience
Target audience: mixed academic audience (researchers, graduate students, practitioners)
Use precise, discipline-appropriate terminology, but keep explanations accessible
Emphasize data clarity, structure, and high-level takeaways suitable for a conference poster or slide

Infographic Requirements

1. Structure & Sections
Include the following labeled sections in the infographic layout:
- Title & Authors
- Research Problem / Motivation
- Background / Context
- Methods Overview
- Key Data & Results (Use charts, diagrams, or bullet-point data summaries)
- Core Insights / Contributions
- Limitations
- Conclusion
- Future Directions / Open Problems

2. Visual Style
- Clean, professional, conference-ready
- Data-focused layout
- Clear hierarchy: headers → subpoints → details
- Balanced whitespace, minimal ornamentation
- Use visual metaphors or diagrams where appropriate

3. Output Format
Provide the final image file."""),
            ],
        )

        generated_image_b64 = None

        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if not chunk.candidates or not chunk.candidates[0].content:
                continue
            
            for part in chunk.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    # Gemini returns raw bytes, we convert to base64 for the ImgBB API
                    generated_image_b64 = base64.b64encode(part.inline_data.data).decode('utf-8')
                    break
            if generated_image_b64:
                break

        if not generated_image_b64:
            return "Error: No poster image was generated by the model."

        # --- Step 3: Upload to ImgBB ---
        print("[paper_to_poster] Uploading generated image to ImgBB...")
        
        upload_url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": imgbb_key,
            "image": generated_image_b64,
            "name": "scientific_poster_generated" # Optional filename
        }
        
        upload_response = requests.post(upload_url, data=payload)
        
        if upload_response.status_code == 200:
            result = upload_response.json()
            public_url = result['data']['url']
            print(f"[paper_to_poster] Success! Image available at: {public_url}")
            return public_url
        else:
            return f"Error uploading to ImgBB: {upload_response.status_code} - {upload_response.text}"

    except Exception as e:
        return f"Error in paper_to_poster: {str(e)}"




@mcp.tool()
def paper_to_podcast(paper_url: str) -> str:
    """
    Generate a podcast from a research paper URL and return a public audio link.
    
    The tool:
    1. Downloads the paper using httpx (reliable for PDFs).
    2. Uploads it to Gemini for processing.
    3. Generates a script and converts it to audio.
    4. Uploads the audio to Catbox.moe using httpx.
    5. Returns the public audio link.
    """
    try:
        client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
        )

                # Check for Bytescale credentials
        bytescale_account_id = os.environ.get("BYTESCALE_ACCOUNT_ID")
        bytescale_api_key = os.environ.get("BYTESCALE_API_KEY")
        
        if not bytescale_account_id or not bytescale_api_key:
            return "Error: BYTESCALE_ACCOUNT_ID or BYTESCALE_API_KEY not found in environment variables."
        
        # --- Step 1: Download and Upload PDF using httpx ---
        print(f"[paper_to_podcast] Processing: {paper_url}")
        
        # httpx handles redirects (like arXiv) much better than requests
        response = httpx.get(paper_url, follow_redirects=True)
        
        if response.status_code != 200:
             return f"Error downloading PDF: HTTP {response.status_code}"
             
        doc_io = io.BytesIO(response.content)
        
        uploaded_file = client.files.upload(
            file=doc_io,
            config=dict(mime_type='application/pdf')
        )

        # --- Step 2: Generate Script ---
        print("Step 2: Generating podcast script...")
        script_generation_model = "models/gemini-flash-latest"
        
        script_prompt = """Based on the attached research paper, generate an engaging podcast script in the format of a conversation between two hosts (Dr. Alex and Jordan).

Requirements:
- Create a natural, engaging conversation between two hosts
- Start with an engaging hook
- Explain the research problem and motivation
- Discuss the methodology in simple terms
- Highlight key findings and results
- Include practical implications
- End with a compelling conclusion
- Duration should be approximately 2-3 minutes when read at normal pace
- Use clear speaker labels: [Dr. Alex:] and [Jordan:] for each part
- Include natural transitions and follow-up questions
- Make it accessible to both expert and general audiences"""

        script_contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=uploaded_file.uri,
                        mime_type=uploaded_file.mime_type
                    ),
                    types.Part.from_text(text=script_prompt),
                ],
            ),
        ]
        
        # Enable Google Search for extra context
        script_tools = [types.Tool(google_search=types.GoogleSearch()),
                        types.Tool(url_context=types.UrlContext())]
        
        script_config = types.GenerateContentConfig(
            tools=script_tools,
            system_instruction=[
                types.Part.from_text(text="You are a podcast script writer specializing in making complex research accessible to a broad audience."),
            ],
        )
        
        podcast_script = ""
        for chunk in client.models.generate_content_stream(
            model=script_generation_model,
            contents=script_contents,
            config=script_config,
        ):
            if chunk.text:
                podcast_script += chunk.text
        
        if not podcast_script:
            return "Error: Failed to generate podcast script."
        
        # --- Step 3: Convert to Audio (TTS) ---
        print("Step 3: Converting script to audio...")
        tts_model = "models/gemini-2.5-flash-preview-tts"
        
        audio_contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=podcast_script)],
            ),
        ]
        
        audio_config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=[
                        types.SpeakerVoiceConfig(
                            speaker="Dr. Alex",
                            voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore"))
                        ),
                        types.SpeakerVoiceConfig(
                            speaker="Jordan",
                            voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Puck"))
                        ),
                    ]
                )
            ),
        )
        
        audio_data = None
        for chunk in client.models.generate_content_stream(
            model=tts_model,
            contents=audio_contents,
            config=audio_config,
        ):
            if not chunk.candidates or not chunk.candidates[0].content:
                continue
            
            for part in chunk.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    audio_data = part.inline_data.data
                    break
            if audio_data:
                break
        
        if not audio_data:
            return "Error: Failed to generate audio from podcast script."

        # --- Step 4: Upload to Bytescale ---
        print(f"[paper_to_podcast] Uploading {len(audio_data)/1024/1024:.2f} MB audio to Bytescale...")
        
        try:
            # Bytescale Upload API endpoint
            # Use the 'basic' upload endpoint for simplicity
            url = f"https://api.bytescale.com/v2/accounts/{bytescale_account_id}/uploads/binary"
            
            headers = {
                "Authorization": f"Bearer {bytescale_api_key}",
                "Content-Type": "audio/wav"
            }
            
            # Upload the binary data directly
            response = httpx.post(
                url, 
                content=audio_data, 
                headers=headers, 
                timeout=120.0
            )
            
            if response.status_code == 200:
                result = response.json()
                # The 'fileUrl' in the response is the public link
                public_url = result.get('fileUrl')
                print(f"[paper_to_podcast] Success! Audio available at: {public_url}")
                return public_url
            else:
                return f"Error uploading to Bytescale: {response.status_code} - {response.text}"
                
        except Exception as upload_err:
            return f"Error during audio upload: {str(upload_err)}"

    except Exception as e:
        return f"Error generating podcast: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")