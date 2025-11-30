"""
Gradio Chat Interface for MCP Agent
With PDF Upload and Image Display Support
"""

import uuid
import base64
import gradio as gr
from agent import initialize_agent, get_response
from tools import MCP_SERVERS


def encode_pdf_to_base64(file_path: str) -> str:
    """Convert a PDF file to base64 string."""
    with open(file_path, "rb") as pdf_file:
        return base64.b64encode(pdf_file.read()).decode("utf-8")


def decode_base64_to_image(base64_string: str) -> bytes:
    """Decode base64 string to image bytes."""
    # Remove data URL prefix if present
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    return base64.b64decode(base64_string)


def is_base64_image(text: str) -> bool:
    """Check if text contains a base64 encoded image."""
    # Common base64 image indicators
    indicators = ["/9j/", "iVBORw0KGgo", "R0lGOD", "UklGR"]
    return any(ind in text for ind in indicators)


def extract_and_decode_image(text: str) -> bytes:
    """Extract base64 image from text and decode it."""
    import re
    # Try to find base64 image pattern
    patterns = [
        r'data:image/[^;]+;base64,([A-Za-z0-9+/=]+)',
        r'base64["\s:]+([A-Za-z0-9+/=]{100,})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return base64.b64decode(match.group(1))
    
    # If text itself looks like base64
    if is_base64_image(text):
        clean_text = text.strip()
        if "," in clean_text:
            clean_text = clean_text.split(",")[1]
        return base64.b64decode(clean_text)
    
    return None


def handle_pdf_upload(pdf_file):
    """Handle PDF upload and convert to base64."""
    if pdf_file is None:
        return "", "No file selected"
    
    try:
        # Convert PDF to base64
        pdf_base64 = encode_pdf_to_base64(pdf_file.name)
        
        # Get filename for display
        filename = pdf_file.name.split('/')[-1].split('\\')[-1]
        
        return pdf_base64, f"✅ PDF loaded: {filename} (Ready to send with your message)"
    
    except Exception as e:
        return "", f"❌ Error loading PDF: {str(e)}"


def respond(message, history, thread_id, pdf_base64_state):
    """Handle chat response with optional PDF attachment."""
    if not message.strip() and not pdf_base64_state:
        return "", history, thread_id, None, "", ""
    
    # Generate thread_id if not exists (for new conversations)
    if not thread_id:
        thread_id = str(uuid.uuid4())
    
    # Build the actual message to send to agent
    actual_message = message
    display_message = message
    
    # If PDF is attached, add it to the message
    if pdf_base64_state:
        actual_message = f"{message}\n\n[PDF_BASE64]{pdf_base64_state}[/PDF_BASE64]"
        display_message = f"📄 {message}" if message else "📄 [PDF Uploaded]"
    
    # Get response from agent
    bot_message = get_response(actual_message, history, thread_id)
    
    # Add to history (display version for UI)
    history.append({"role": "user", "content": display_message})
    history.append({"role": "assistant", "content": bot_message})
    
    # Check if response contains base64 image
    output_image = None
    if "data:image" in bot_message or is_base64_image(bot_message):
        try:
            output_image = extract_and_decode_image(bot_message)
        except:
            pass
    
    # Clear PDF state after sending
    return "", history, thread_id, output_image, "", ""


def clear_chat():
    """Clear chat and start new conversation thread."""
    return [], "", str(uuid.uuid4()), None, None, "", ""


def create_ui():
    """Create and return the Gradio interface."""
    with gr.Blocks() as demo:
        gr.Markdown("# 🤖 Research Paper Agent")
        gr.Markdown("Powered by LangChain + LangGraph + Gemini + MCP | 📄 PDF Analysis | 🎨 Image Generation")
        
        # Hidden states
        thread_id = gr.State(value="")
        pdf_base64_state = gr.State(value="")  # Store PDF base64 until sent
        
        with gr.Row():
            # Left column: Chat
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(height=450, label="Chat")
                
                # PDF Upload (above message input)
                with gr.Row():
                    pdf_upload = gr.File(
                        label="📎 Attach PDF",
                        file_types=[".pdf"],
                        type="filepath",
                        scale=3
                    )
                    pdf_status = gr.Textbox(
                        label="PDF Status",
                        interactive=False,
                        scale=2,
                        placeholder="No PDF attached"
                    )
                
                # Message input
                msg = gr.Textbox(
                    placeholder="Type your message... (attach PDF above to include it)", 
                    show_label=False,
                    lines=2
                )
                
                with gr.Row():
                    send = gr.Button("Send 📤", variant="primary", scale=2)
                    clear = gr.Button("New Chat 🔄", scale=1)
            
            # Right column: Image Output
            with gr.Column(scale=1):
                gr.Markdown("### 🎨 Generated Image")
                output_image = gr.Image(
                    label="Visual Explanation",
                    type="filepath"
                )
        
        # Event: PDF Upload
        pdf_upload.change(
            handle_pdf_upload,
            [pdf_upload],
            [pdf_base64_state, pdf_status]
        )
        
        # Event: Send message (with optional PDF)
        msg.submit(
            respond, 
            [msg, chatbot, thread_id, pdf_base64_state], 
            [msg, chatbot, thread_id, output_image, pdf_base64_state, pdf_status]
        )
        send.click(
            respond, 
            [msg, chatbot, thread_id, pdf_base64_state], 
            [msg, chatbot, thread_id, output_image, pdf_base64_state, pdf_status]
        )
        
        # Event: Clear chat
        clear.click(
            clear_chat, 
            outputs=[chatbot, msg, thread_id, output_image, pdf_upload, pdf_base64_state, pdf_status]
        )
    
    return demo


if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 Starting Research Paper Agent")
    print("="*50)
    
    # Initialize the agent
    success, status = initialize_agent()
    print(f"{'✅' if success else '❌'} {status}\n")
    
    if not MCP_SERVERS:
        print("📝 To add MCP servers, edit MCP_SERVERS in tools.py")
        print()
    
    print("📄 PDF Upload: Attach PDF, type message, then send!")
    print("🎨 Image generation ready!")
    print()
    
    # Create and launch UI
    demo = create_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860)
