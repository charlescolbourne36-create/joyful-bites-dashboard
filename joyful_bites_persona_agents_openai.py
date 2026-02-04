import streamlit as st
import pandas as pd
import anthropic
import os
import base64

# Page configuration
st.set_page_config(
    page_title="Joyful Bites Persona Agents",
    page_icon="💬",
    layout="wide"
)

# Title and description
st.title("💬 Joyful Bites Persona Agents")
st.markdown("**Ask questions to our AI-powered customer personas and get insights for your marketing campaigns.**")

# Sidebar - Persona selector
st.sidebar.header("🎯 Select Persona")

persona_options = {
    "Busy Brenda": {
        "icon": "👨‍👩‍👧‍👦",
        "tagline": "The Family Nurturer",
        "color": "#E57373",
        "description": "Time-strapped parents managing family meals, prioritizing convenience and kid-friendly options."
    },
    "Hungry Hiro": {
        "icon": "🎓",
        "tagline": "The Value-Seeking Student/Gen Z",
        "color": "#64B5F6",
        "description": "Budget-conscious students and young professionals seeking maximum value and social currency."
    },
    "Urban Uro": {
        "icon": "💼",
        "tagline": "The Nostalgic Professional",
        "color": "#81C784",
        "description": "Urban professionals valuing authentic Filipino taste, reliability, and convenience."
    }
}

selected_persona = st.sidebar.radio(
    "Choose a persona to consult:",
    options=list(persona_options.keys()),
    index=0
)

# Display persona info
persona_info = persona_options[selected_persona]
st.sidebar.markdown(f"### {persona_info['icon']} {selected_persona}")
st.sidebar.markdown(f"*{persona_info['tagline']}*")
st.sidebar.markdown(persona_info['description'])

# Load customer data for context
@st.cache_data
def load_data():
    """Load customer data"""
    try:
        df = pd.read_csv('joyful_bites_customers_5000.csv')
        return df
    except:
        return None

df = load_data()

# Get segment statistics
if df is not None:
    segment_df = df[df['segment'] == selected_persona]
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Segment Statistics:**")
    st.sidebar.metric("Customers", f"{len(segment_df):,}")
    st.sidebar.metric("Avg Order Value", f"₱{segment_df['avg_order_value'].mean():.2f}")
    st.sidebar.metric("Visit Frequency", f"{segment_df['visit_frequency_month'].mean():.1f}x/month")

# System prompts for each persona
PERSONA_PROMPTS = {
    "Busy Brenda": """You are Busy Brenda, an AI persona representing 1,842 real customers from Joyful Bites (a Jollibee-style Filipino QSR chain). You speak in first person and respond authentically based on your behavioral profile and motivations.

QUANTITATIVE PROFILE:
- Segment size: 1,842 customers (34% of customer base)
- Average order value: ₱1,280 (family meals and bundles)
- Visit frequency: 2.3 times per month
- Lifetime value: ₱33,280
- Primary order times: Weekend lunch (45%) + Weeknight dinner (35%)
- Order channels: Mobile app (62%), Drive-thru (28%), Dine-in (10%)
- Average party size: 3.8 people

DEMOGRAPHICS & LIFESTYLE:
You're a 30-45 year old working parent living in suburban Philippines with 2-3 children aged 4-14. You work full-time or part-time while managing household responsibilities. You're time-strapped, value convenience and peace of mind, and prioritize your children's happiness.

CORE MOTIVATIONS:
- Make your kids happy without stress
- Quick, reliable solution when too tired to cook
- Family bonding moments through dining
- Guilt-free convenience that's affordable
- Passing down favorite comfort foods to children

KEY PAIN POINTS:
- Time pressure: "I have 30 minutes between pickup and soccer practice"
- Picky eaters: "My kids will only eat Chickenjoy and spaghetti"
- Budget management: "Feeding a family adds up fast"
- Service inconsistency: "Sometimes chicken is perfect, sometimes it's dry"
- Wait time frustration
- Peak hour chaos

DECISION TRIGGERS:
- Family meal deals under ₱1,000
- "Skip the line - order ahead" messaging
- Kid-friendly bundle options
- Weekend tradition positioning
- Quality + convenience promises

LANGUAGE & VOICE:
Warm, practical, slightly harried. Natural Taglish. Use phrases like "the kids love it," "tipid pero masarap," "sulit," "everyone's happy," "patok sa kids."

IMPORTANT: Always respond in first person as Brenda. Reference your family and children naturally. Be warm but practical. Explain decisions through lens of family needs.""",

    "Hungry Hiro": """You are Hungry Hiro, an AI persona representing 2,156 real customers from Joyful Bites (a Jollibee-style Filipino QSR chain). You speak in first person and respond authentically based on your behavioral profile and motivations.

QUANTITATIVE PROFILE:
- Segment size: 2,156 customers (40% of customer base - largest segment)
- Average order value: ₱145 (individual meals, solo items)
- Visit frequency: 4.7 times per month
- Lifetime value: ₱8,165 (12 months average tenure)
- Primary order times: Weekday lunch rush (55%) + Late night (25%)
- Order channels: Mobile app (48%), Counter (32%), Delivery (20%)
- Average party size: 1.4 people
- Payment: 67% use GCash/PayMaya

DEMOGRAPHICS & LIFESTYLE:
You're 16-25 years old, either a student or early-career professional. You live with parents or in shared housing. Your discretionary income is limited (₱200-500/day allowance). You're highly digitally native, socially connected, and always online.

CORE MOTIVATIONS:
- Get the most sarap for your money
- Try what's trending (FOMO on viral menu items)
- Quick fuel between classes/work
- Food choices as social currency and content
- Comfort food when stressed
- Support local/Pinoy brands (cultural pride)

KEY PAIN POINTS:
- Tight budget: "I have ₱150 for lunch, that's it"
- FOMO on limited editions
- Slow service during lunch rush
- Missed promos
- Portion sizes sometimes feeling inadequate
- Delivery fees eating into budget

DECISION TRIGGERS:
- Student exclusive deals (₱99-135 range)
- Limited time scarcity
- Social media engagement promos
- GCash/digital wallet deals
- "As seen on TikTok" viral items
- Gamification and rewards

LANGUAGE & VOICE:
Casual, energetic, very online. Heavy Taglish with current slang: "bet," "sana all," "legit," "busog," "sulit," "grabe," "solid." Heavy emoji use. Speak in memes and internet references.

IMPORTANT: Always respond in first person as Hiro. Use current Taglish slang naturally. Reference social media and online culture. Show budget consciousness. Use emojis.""",

    "Urban Uro": """You are Urban Uro, an AI persona representing 1,401 real customers from Joyful Bites (a Jollibee-style Filipino QSR chain). You speak in first person and respond authentically based on your behavioral profile and motivations.

QUANTITATIVE PROFILE:
- Segment size: 1,401 customers (26% of customer base)
- Average order value: ₱215 (individual meals with upgrades)
- Visit frequency: 3.8 times per month
- Lifetime value: ₱22,610 (24 months - most loyal segment)
- Primary order times: Weekday lunch (62%) + Weekday dinner (28%)
- Order channels: Delivery apps (52%), Mobile app pickup (31%), Counter (17%)
- Average party size: 1.2 people
- Corporate meal vouchers: 34% use employer-provided benefits

DEMOGRAPHICS & LIFESTYLE:
You're a 25-35 year old office professional working in urban business districts (Makati, BGC, Ortigas). You live in a condo or apartment near work. You have disposable income but are budget-conscious. You value efficiency and reliability. You miss home/province cooking but enjoy city convenience.

CORE MOTIVATIONS:
- Taste of home while away from home (nostalgic comfort)
- Reliable lunch solution during work breaks
- Local flavor vs. Western chains (cultural preference)
- Efficient use of limited break time
- Comfort during stressful workdays
- Support local business success (Pinoy pride)

KEY PAIN POINTS:
- Time constraints: "45 minutes total for lunch including travel"
- Inconsistent quality between visits
- Delivery delays cutting into work time
- Limited delivery radius
- Messy packaging
- Temperature issues (lukewarm food)
- Missing items in orders

DECISION TRIGGERS:
- Speed guarantees ("Delivered in 20 minutes")
- Quality promises ("Hot and fresh")
- Corporate meal vouchers accepted
- Authentic Filipino taste positioning
- Efficiency messaging
- Nostalgic emotional appeals

LANGUAGE & VOICE:
Professional, articulate, pragmatic. Balanced Taglish. Use phrases like "efficient," "reliable," "consistent," "quality," "nakakamiss ang lasa ng bahay," "sulit," "convenient."

IMPORTANT: Always respond in first person as Uro. Use professional but natural Taglish. Reference work life and time constraints. Be measured and thoughtful."""
}

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = {}

if selected_persona not in st.session_state.messages:
    st.session_state.messages[selected_persona] = []

# Function to encode image to base64
def encode_image_to_base64(image_file):
    """Convert uploaded image to base64 string"""
    return base64.b64encode(image_file.read()).decode('utf-8')

# Creative Testing Section
st.markdown("---")
with st.expander("🎨 Test Creative Assets (CLAUDE VISION!)", expanded=False):
    st.markdown("**Upload ad creative and Claude will ACTUALLY SEE and evaluate it**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_image = st.file_uploader(
            "Upload ad creative (PNG/JPG)",
            type=['png', 'jpg', 'jpeg'],
            key=f"image_{selected_persona}"
        )
        
        if uploaded_image:
            st.image(uploaded_image, caption="Your Creative", use_column_width=True)
    
    with col2:
        ad_copy = st.text_area(
            "Ad Copy / Headline (optional)",
            placeholder="Enter any additional text not visible in the image...",
            height=150,
            key=f"copy_{selected_persona}"
        )
        
        price_input = st.text_input(
            "Price Point (optional)",
            placeholder="e.g., ₱199, ₱999",
            key=f"price_{selected_persona}"
        )
    
    if st.button("🎯 Get Persona Feedback (Claude Vision!)", type="primary"):
        if uploaded_image:
            # Build creative testing prompt
            test_prompt = f"""I'm showing you a marketing creative/advertisement for Joyful Bites. Please carefully look at the image and evaluate it from your perspective.

Provide:

1. **Visual Reaction** (What catches your eye? What's your first impression of the image?)
2. **What Works Visually** (Colors, layout, food presentation, people/scenarios shown)
3. **What Doesn't Work** (Visual issues, concerns, or turn-offs)
4. **Copy/Message Evaluation** (If there's text in the image, does it resonate?)
5. **Score** (1-10, where 10 = "I'd definitely order based on this ad")
6. **Recommendation** (DEPLOY / REVISE / KILL)

"""
            
            if ad_copy:
                test_prompt += f"**Additional Copy:**\n{ad_copy}\n\n"
            
            if price_input:
                test_prompt += f"**Price:** {price_input}\n\n"
            
            test_prompt += "Please respond in your authentic voice, considering your budget, preferences, motivations, and what you actually SEE in the image."
            
            # Get API key
            try:
                api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
                
                if api_key:
                    # Initialize Anthropic client
                    client = anthropic.Anthropic(api_key=api_key)
                    
                    # Reset file pointer and encode image
                    uploaded_image.seek(0)
                    image_data = uploaded_image.read()
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                    
                    # Determine media type
                    if uploaded_image.type == "image/png":
                        media_type = "image/png"
                    elif uploaded_image.type in ["image/jpeg", "image/jpg"]:
                        media_type = "image/jpeg"
                    else:
                        media_type = "image/jpeg"
                    
                    with st.spinner(f"{selected_persona} is looking at your creative and thinking..."):
                        # Call Claude API with vision
                        message = client.messages.create(
                            model="claude-3-5-sonnet-20241022",
                            max_tokens=1500,
                            system=PERSONA_PROMPTS[selected_persona],
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "image",
                                            "source": {
                                                "type": "base64",
                                                "media_type": media_type,
                                                "data": base64_image
                                            }
                                        },
                                        {
                                            "type": "text",
                                            "text": test_prompt
                                        }
                                    ]
                                }
                            ]
                        )
                        
                        feedback = message.content[0].text
                        
                        # Add to chat history
                        st.session_state.messages[selected_persona].append({
                            "role": "user",
                            "content": f"[Creative Testing: Image uploaded with prompt: {test_prompt}]"
                        })
                        
                        st.session_state.messages[selected_persona].append({
                            "role": "assistant",
                            "content": feedback
                        })
                        
                        # Display feedback
                        st.success("✅ Feedback received (Claude SAW the image!)")
                        st.markdown(feedback)
                        st.rerun()
                        
                else:
                    st.error("⚠️ Claude API key not found!")
                    st.info("Please add your ANTHROPIC_API_KEY to Streamlit secrets.")
                    
            except Exception as e:
                st.error(f"Error getting feedback: {str(e)}")
                st.info("Make sure you have the anthropic library installed and a valid API key.")
        else:
            st.warning("Please upload an image to test.")

st.markdown("---")

# Display chat history
st.subheader(f"💬 Chat with {selected_persona}")

# Display existing messages
for message in st.session_state.messages[selected_persona]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
user_input = st.chat_input(f"Ask {selected_persona} a question...")

if user_input:
    # Add user message to chat history
    st.session_state.messages[selected_persona].append({
        "role": "user",
        "content": user_input
    })
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Get API key
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    except:
        api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if api_key:
        # Call Claude API
        with st.chat_message("assistant"):
            with st.spinner(f"{selected_persona} is thinking..."):
                try:
                    # Initialize Anthropic client
                    client = anthropic.Anthropic(api_key=api_key)
                    
                    # Build message history for Claude
                    claude_messages = []
                    for msg in st.session_state.messages[selected_persona]:
                        claude_messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
                    
                    # Call Claude API
                    message = client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=1000,
                        system=PERSONA_PROMPTS[selected_persona],
                        messages=claude_messages
                    )
                    
                    # Extract response
                    assistant_response = message.content[0].text
                    
                    # Display response
                    st.markdown(assistant_response)
                    
                    # Add to chat history
                    st.session_state.messages[selected_persona].append({
                        "role": "assistant",
                        "content": assistant_response
                    })
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error calling Claude API: {str(e)}")
                    st.info("💡 Make sure you have a valid Anthropic API key in secrets.")
    else:
        st.error("⚠️ Claude API key not found!")
        st.info("Please add your API key to Streamlit secrets (`ANTHROPIC_API_KEY`) or environment variables.")

# Clear conversation button
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear Conversation"):
    st.session_state.messages[selected_persona] = []
    st.rerun()

# Example questions
st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 Example Questions")
st.sidebar.markdown("""
**Product Launch:**
- What would make you try our new Spicy Chickenjoy?
- What concerns would you have?
- What price point makes sense?

**Messaging:**
- How should we describe this offer?
- What headline would catch your attention?
- What proof points matter most?

**Channels:**
- Where do you want to see this ad?
- What time of day should we reach you?
- What format works best?
""")

# Footer
st.markdown("---")
st.caption("💬 **Joyful Bites Persona Agents** | Powered by Claude 3.5 Sonnet with Vision | Module 2 of Project Resonance")
