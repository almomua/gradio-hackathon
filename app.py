"""
Gradio Chat Interface for MCP Agent
Custom Black & Orange Theme with Animations
"""

import uuid
import re
import gradio as gr
from agent import initialize_agent, get_response
from tools import MCP_SERVERS


def extract_images_from_text(text):
    """Extract image URLs from text and return text with large, clickable markdown images."""
    # Handle None or non-string input
    if not text or not isinstance(text, str):
        return text, []
    
    images = []
    modified_text = text
    
    # Pattern for direct image URLs
    image_url_pattern = r'(https?://[^\s\)]+\.(?:png|jpg|jpeg|gif|webp|svg)(?:\?[^\s\)]*)?)'
    
    # Find all image URLs
    matches = list(re.finditer(image_url_pattern, text, re.IGNORECASE))
    
    # Process matches in reverse to avoid index issues
    for match in reversed(matches):
        url = match.group(1)
        # Check if it's not already in markdown format
        start = match.start()
        if start < 2 or text[start-2:start] != '](':
            # Replace URL with markdown image with descriptive text
            modified_text = (
                modified_text[:start] + 
                f'\n\n📸 **Click image to view full size:**\n\n![Generated Image]({url})\n\n' + 
                modified_text[match.end():]
            )
            images.append(url)
    
    return modified_text, images


def respond(message, history, thread_id):
    """Handle chat response with memory and image rendering."""
    if not message.strip():
        return "", history, thread_id
    
    # Generate thread_id if not exists (for new conversations)
    if not thread_id:
        thread_id = str(uuid.uuid4())
    
    bot_message = get_response(message, history, thread_id)
    
    # Process bot message for images
    processed_message, images = extract_images_from_text(bot_message)
    
    # Debug: print if images were found
    if images:
        print(f"📸 Found {len(images)} image(s) in response")
        for img in images:
            print(f"   - {img}")
    
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": processed_message})
    
    return "", history, thread_id


def clear_chat():
    """Clear chat and start new conversation thread."""
    return [], "", str(uuid.uuid4())


# Custom CSS with Black & Orange theme and animations
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap');

:root {
    --primary-orange: #ff6b35;
    --dark-orange: #e85d2f;
    --light-orange: #ff8c61;
    --black-bg: #0a0a0a;
    --dark-gray: #1a1a1a;
    --medium-gray: #2a2a2a;
    --light-gray: #3a3a3a;
    --text-primary: #ffffff;
    --text-secondary: #b0b0b0;
}

/* Global Styles */
.gradio-container {
    font-family: 'Space Grotesk', sans-serif !important;
    background: var(--black-bg) !important;
    max-width: 95% !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 0 2rem !important;
}

/* Animated Header */
.custom-header {
    text-align: center;
    padding: 2.5rem 2rem;
    background: linear-gradient(135deg, var(--dark-gray) 0%, var(--medium-gray) 100%);
    border-radius: 20px;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
    animation: fadeIn 0.8s ease-in;
    border: 2px solid var(--light-gray);
}

.custom-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 4px;
    background: linear-gradient(90deg, 
        transparent, 
        var(--primary-orange), 
        var(--dark-orange),
        transparent
    );
    animation: shimmer 3s infinite;
}

.custom-header h1 {
    font-size: 3rem;
    font-weight: 700;
    background: linear-gradient(135deg, var(--primary-orange) 0%, var(--light-orange) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5rem;
    animation: slideDown 0.6s ease-out;
}

.custom-header p {
    color: var(--text-secondary);
    font-size: 1.1rem;
    margin-top: 0.5rem;
    animation: slideDown 0.8s ease-out;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: var(--medium-gray);
    padding: 0.5rem 1rem;
    border-radius: 20px;
    margin-top: 1rem;
    border: 1px solid var(--light-gray);
    animation: pulse 2s infinite;
}

.status-dot {
    width: 8px;
    height: 8px;
    background: var(--primary-orange);
    border-radius: 50%;
    animation: blink 1.5s infinite;
}

/* Chatbot Styling */
#chat-interface {
    background: var(--dark-gray) !important;
    border: 2px solid var(--light-gray) !important;
    border-radius: 20px !important;
    padding: 1.5rem !important;
    box-shadow: 0 10px 40px rgba(255, 107, 53, 0.1) !important;
    animation: fadeIn 1s ease-in;
}

.message {
    animation: messageSlide 0.4s ease-out;
    margin: 0.75rem 0 !important;
    padding: 1rem 1.25rem !important;
    border-radius: 15px !important;
    max-width: 95% !important;
    width: fit-content !important;
    position: relative;
    overflow: visible !important;
}

.message.user {
    background: linear-gradient(135deg, var(--primary-orange), var(--dark-orange)) !important;
    color: var(--text-primary) !important;
    margin-left: auto !important;
    border-bottom-right-radius: 5px !important;
    box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);
}

.message.bot {
    background: var(--medium-gray) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--light-gray) !important;
    border-bottom-left-radius: 5px !important;
    width: 100% !important;
    max-width: 95% !important;
}

/* Input Area */
#message-input {
    background: var(--medium-gray) !important;
    border: 2px solid var(--light-gray) !important;
    border-radius: 15px !important;
    color: var(--text-primary) !important;
    font-size: 1rem !important;
    padding: 1rem 1.25rem !important;
    transition: all 0.3s ease !important;
}

#message-input:focus {
    border-color: var(--primary-orange) !important;
    box-shadow: 0 0 0 3px rgba(255, 107, 53, 0.2) !important;
    transform: translateY(-2px);
}

/* Buttons */
.button-container {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
}

#send-btn {
    background: linear-gradient(135deg, var(--primary-orange), var(--dark-orange)) !important;
    color: var(--text-primary) !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.875rem 2rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    position: relative;
    overflow: hidden;
}

#send-btn::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.3);
    transform: translate(-50%, -50%);
    transition: width 0.6s, height 0.6s;
}

#send-btn:hover::before {
    width: 300px;
    height: 300px;
}

#send-btn:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 20px rgba(255, 107, 53, 0.4) !important;
}

#send-btn:active {
    transform: translateY(-1px) !important;
}

#clear-btn {
    background: var(--medium-gray) !important;
    color: var(--text-secondary) !important;
    border: 2px solid var(--light-gray) !important;
    border-radius: 12px !important;
    padding: 0.875rem 1.5rem !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
}

#clear-btn:hover {
    background: var(--light-gray) !important;
    border-color: var(--primary-orange) !important;
    color: var(--primary-orange) !important;
    transform: translateY(-2px);
}

/* Animations */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes slideDown {
    from {
        opacity: 0;
        transform: translateY(-30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes messageSlide {
    from {
        opacity: 0;
        transform: translateX(-20px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes shimmer {
    0% {
        left: -100%;
    }
    100% {
        left: 200%;
    }
}

@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.7;
    }
}

@keyframes blink {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.3;
    }
}

/* Image Styling in Chat - LARGE & CLICKABLE */
#chat-interface img {
    max-width: 100% !important;
    width: 100% !important;
    min-width: 600px !important;
    height: auto !important;
    border-radius: 12px !important;
    margin: 1rem 0 !important;
    box-shadow: 0 8px 24px rgba(255, 107, 53, 0.3) !important;
    border: 3px solid var(--primary-orange) !important;
    display: block !important;
    cursor: zoom-in !important;
    transition: all 0.3s ease !important;
}

#chat-interface img:hover {
    transform: scale(1.01) !important;
    box-shadow: 0 12px 32px rgba(255, 107, 53, 0.5) !important;
    border-color: var(--light-orange) !important;
}

.message img {
    max-width: 100% !important;
    width: 100% !important;
    min-width: 600px !important;
    height: auto !important;
    border-radius: 12px !important;
    margin: 1rem 0 !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4) !important;
    border: 3px solid var(--light-gray) !important;
    cursor: zoom-in !important;
    transition: all 0.3s ease !important;
}

.message img:hover {
    transform: scale(1.01) !important;
    box-shadow: 0 12px 32px rgba(255, 107, 53, 0.5) !important;
}

.message.bot img {
    border-color: var(--primary-orange) !important;
}

/* Ensure message container fits images */
.message:has(img) {
    width: 100% !important;
    max-width: 95% !important;
    padding: 1.5rem !important;
}

/* Modal/Lightbox Styling */
#image-modal {
    display: none;
    position: fixed;
    z-index: 9999;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.95);
    animation: fadeIn 0.3s ease;
}

#image-modal.active {
    display: flex !important;
    align-items: center;
    justify-content: center;
}

#image-modal img {
    max-width: 95vw !important;
    max-height: 95vh !important;
    min-width: 0 !important;
    object-fit: contain;
    border-radius: 8px;
    box-shadow: 0 20px 60px rgba(255, 107, 53, 0.6);
    cursor: zoom-out;
    animation: zoomIn 0.3s ease;
}

#modal-close {
    position: absolute;
    top: 20px;
    right: 40px;
    font-size: 3rem;
    color: var(--primary-orange);
    cursor: pointer;
    font-weight: bold;
    z-index: 10000;
    transition: all 0.3s ease;
}

#modal-close:hover {
    color: var(--light-orange);
    transform: scale(1.2);
}

@keyframes zoomIn {
    from {
        transform: scale(0.5);
        opacity: 0;
    }
    to {
        transform: scale(1);
        opacity: 1;
    }
}

/* Scrollbar Styling */
::-webkit-scrollbar {
    width: 10px;
}

::-webkit-scrollbar-track {
    background: var(--dark-gray);
}

::-webkit-scrollbar-thumb {
    background: var(--primary-orange);
    border-radius: 5px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--dark-orange);
}

/* Loading Animation */
.loading {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid var(--light-gray);
    border-radius: 50%;
    border-top-color: var(--primary-orange);
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
"""

# Custom HTML Header with Modal and JavaScript
HEADER_HTML = """
<div style="text-align: center; margin-bottom: 1.5rem;">
    <div class="status-badge">
        <span class="status-dot"></span>
        <span style="color: var(--text-secondary); font-size: 0.9rem;">System Online</span>
    </div>
</div>

<!-- Image Modal/Lightbox -->
<div id="image-modal">
    <span id="modal-close">&times;</span>
    <img id="modal-image" src="" alt="Full size image">
</div>

<script>
// Image Modal/Lightbox functionality
function initImageModal() {
    const modal = document.getElementById('image-modal');
    const modalImg = document.getElementById('modal-image');
    const closeBtn = document.getElementById('modal-close');
    
    if (!modal || !modalImg || !closeBtn) {
        console.log('Modal elements not ready yet');
        return;
    }
    
    // Add click listeners to all chat images
    document.addEventListener('click', function(e) {
        if (e.target.tagName === 'IMG' && 
            e.target.closest('#chat-interface') && 
            e.target.id !== 'modal-image') {
            
            console.log('Image clicked:', e.target.src);
            
            // Open modal with clicked image
            modal.classList.add('active');
            modalImg.src = e.target.src;
            modalImg.alt = e.target.alt || 'Full size image';
            document.body.style.overflow = 'hidden';
        }
    });
    
    // Close modal on click
    modal.addEventListener('click', function(e) {
        if (e.target === modal || e.target === modalImg || e.target === closeBtn) {
            console.log('Closing modal');
            modal.classList.remove('active');
            document.body.style.overflow = 'auto';
        }
    });
    
    // Close on ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            console.log('ESC pressed, closing modal');
            modal.classList.remove('active');
            document.body.style.overflow = 'auto';
        }
    });
    
    console.log('Image modal initialized');
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initImageModal);
} else {
    initImageModal();
}

// Re-initialize after Gradio updates (when new messages appear)
setInterval(initImageModal, 1000);
</script>
"""


def create_ui():
    """Create and return the Gradio interface with custom styling."""
    with gr.Blocks() as demo:
        # Custom Header
        gr.HTML(HEADER_HTML)
        
        # Welcome Message
        gr.HTML("""
        <div style="text-align: center; padding: 1.5rem 2rem; margin-bottom: 1.5rem; 
                    background: linear-gradient(135deg, var(--dark-gray) 0%, var(--medium-gray) 100%);
                    border-radius: 15px; border: 1px solid var(--light-gray);">
            <h2 style="color: var(--primary-orange); margin-bottom: 0.5rem; font-size: 1.8rem;">
                🔬 Research Paper Agent
            </h2>
            <p style="color: var(--text-secondary); margin: 0; font-size: 1rem;">
                Ask about research papers, analyze topics, or request document analysis
            </p>
        </div>
        """)
        
        # Hidden state for thread_id (conversation memory)
        thread_id = gr.State(value="")
        
        # Chatbot with markdown support for images
        chatbot = gr.Chatbot(
            elem_id="chat-interface",
            height=500,
            show_label=False,
            render_markdown=True
        )
        
        # Message Input
        msg = gr.Textbox(
            placeholder="Ask about research papers, topics, or request analysis...",
            show_label=False,
            elem_id="message-input",
            lines=2
        )
        
        # Buttons
        with gr.Row(elem_classes="button-container"):
            send = gr.Button("Send ✨", elem_id="send-btn", scale=3)
            clear = gr.Button("New Chat 🔄", elem_id="clear-btn", scale=1)
        
        # Event handlers
        msg.submit(respond, [msg, chatbot, thread_id], [msg, chatbot, thread_id])
        send.click(respond, [msg, chatbot, thread_id], [msg, chatbot, thread_id])
        clear.click(clear_chat, outputs=[chatbot, msg, thread_id])
    
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
    
    print("🧠 Conversational memory enabled!")
    print("🎨 Custom UI theme loaded: Black & Orange")
    print()
    
    # Create and launch UI with custom CSS
    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        css=CUSTOM_CSS
    )
