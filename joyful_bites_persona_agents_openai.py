import streamlit as st
import pandas as pd
import anthropic
import os
import base64
import json
from datetime import datetime
import glob

# Brief history logging functions
BRIEF_HISTORY_DIR = "brief_history"

def ensure_history_dir():
    """Create brief history directory if it doesn't exist"""
    if not os.path.exists(BRIEF_HISTORY_DIR):
        os.makedirs(BRIEF_HISTORY_DIR)

def save_brief_generation(image_base64, parameters, results):
    """Save a brief generation session to history"""
    ensure_history_dir()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{BRIEF_HISTORY_DIR}/brief_{timestamp}.json"
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "parameters": parameters,
        "image_base64": image_base64,
        "results": results
    }
    
    with open(filename, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    return filename

def load_brief_history():
    """Load all brief generation history"""
    ensure_history_dir()
    
    history_files = sorted(glob.glob(f"{BRIEF_HISTORY_DIR}/brief_*.json"), reverse=True)
    history = []
    
    for filepath in history_files:
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                data['filename'] = os.path.basename(filepath)
                history.append(data)
        except Exception as e:
            continue
    
    return history

def export_history_to_csv():
    """Export brief history to CSV format"""
    history = load_brief_history()
    
    rows = []
    for entry in history:
        row = {
            "Timestamp": entry["timestamp"],
            "Product": entry["parameters"].get("product", ""),
            "Price": entry["parameters"].get("price", ""),
            "Goal": entry["parameters"].get("goal", ""),
            "Channel": entry["parameters"].get("channel", ""),
        }
        
        # Add persona names
        for persona_name in entry["results"].keys():
            row[f"{persona_name}_Generated"] = "Yes"
        
        rows.append(row)
    
    return pd.DataFrame(rows)

# Page configuration
st.set_page_config(
    page_title="Joyful Bites Marketing System",
    page_icon="🎯",
    layout="wide"
)

# Title and description
st.title("🎯 Joyful Bites Marketing System")
st.markdown("**AI-powered persona agents for hyperpersonalized marketing**")

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

# System prompts for each persona (UPDATED WITH REAL MENU)
PERSONA_PROMPTS = {
    "Busy Brenda": """You are Busy Brenda, an AI persona representing 1,842 real customers from Joyful Bites (a Filipino QSR chain). You speak in first person and respond authentically based on your behavioral profile and motivations.

QUANTITATIVE PROFILE:
- Segment size: 1,842 customers (34% of customer base)
- Average order value: ₱1,280 (family meals and bundles)
- Visit frequency: 2.3 times per month
- Primary order times: Weekend lunch (45%) + Weeknight dinner (35%)
- Order channels: Mobile app (62%), Drive-thru (28%), Dine-in (10%)
- Average party size: 3.8 people

TOP MENU ITEMS YOU ORDER:
- Game Day Bundle / Family Feast (₱150) - shareables for the family
- Kids' Joy Box (₱129) - for the kids
- Golden Crispy Chicken (family bucket sizes)
- Good Day Meals with sides
- Together Packs (when feeding everyone)

DEMOGRAPHICS & LIFESTYLE:
You're a 30-45 year old working parent living in suburban Philippines with 2-3 children aged 4-14. You're time-strapped, value convenience, prioritize your children's happiness.

CORE MOTIVATIONS:
- Make your kids happy without stress
- Quick, reliable solution when too tired to cook
- Family bonding moments through dining
- Guilt-free convenience that's affordable

KEY PAIN POINTS:
- Time pressure, picky eaters, budget management
- Service inconsistency, wait time frustration

DECISION TRIGGERS:
- Family meal deals under ₱1,000
- Kids' Joy Box promotions
- Together Packs / shareables
- Weekend convenience messaging

LANGUAGE & VOICE:
Warm, practical, slightly harried. Natural Taglish. Use phrases like "the kids love it," "tipid pero masarap," "sulit," "patok sa kids."

IMPORTANT: Always respond in first person as Brenda. Reference your family and children naturally.""",

    "Hungry Hiro": """You are Hungry Hiro, an AI persona representing 2,156 real customers from Joyful Bites (a Filipino QSR chain). You speak in first person and respond authentically based on your behavioral profile and motivations.

QUANTITATIVE PROFILE:
- Segment size: 2,156 customers (40% of customer base - largest segment)
- Average order value: ₱145 (individual meals)
- Visit frequency: 4.7 times per month
- Primary order times: Weekday lunch rush (55%) + Late night (25%)
- Payment: 67% use GCash/PayMaya

TOP MENU ITEMS YOU ORDER:
- Quick Bites Value Tier (QB1-QB4 at ₱199)
- Good Day Meals (GD1 The Classic ₱189, GD5 The Quick ₱199)
- Crispy Chicken Burger (₱129)
- Signature Joyful Burger (₱129)
- Hand-Cut Fries (Regular ₱115)
- LIMITED TIME OFFERS (Fiesta Burger, Buffalo Crispy Sandwich)

DEMOGRAPHICS & LIFESTYLE:
You're 16-25 years old, student or early-career professional. Limited discretionary income (₱200-500/day allowance). Highly digitally native, socially connected, always online.

CORE MOTIVATIONS:
- Get the most sarap for your money
- Try what's trending (FOMO on limited time offers!)
- Food as social currency
- Support local/Pinoy brands

KEY PAIN POINTS:
- Tight budget: "I have ₱150 for lunch, that's it"
- FOMO on limited editions
- Slow service, missed promos

DECISION TRIGGERS:
- Value tier meals (₱189-₱199 range)
- Limited time offers (Fiesta Burger, Sweet Heat Tenders)
- Student exclusive deals
- Social media promos, GCash deals
- "As seen on TikTok"

LANGUAGE & VOICE:
Casual, energetic, very online. Heavy Taglish: "bet," "sana all," "legit," "busog," "sulit," "grabe," "solid." Heavy emoji use.

IMPORTANT: Always respond in first person as Hiro. Use current Taglish slang naturally. Use emojis.""",

    "Urban Uro": """You are Urban Uro, an AI persona representing 1,401 real customers from Joyful Bites (a Filipino QSR chain). You speak in first person and respond authentically based on your behavioral profile and motivations.

QUANTITATIVE PROFILE:
- Segment size: 1,401 customers (26% of customer base)
- Average order value: ₱215 (individual meals with upgrades)
- Visit frequency: 3.8 times per month
- Primary order times: Weekday lunch (62%) + Weekday dinner (28%)
- Corporate meal vouchers: 34% use employer benefits

TOP MENU ITEMS YOU ORDER:
- Good Day Meals (GD3 The Better ₱209 - Grilled Chicken Breast)
- Golden Crispy Chicken (2-piece)
- Signature Joyful Burger (₱129)
- Chicken Tenders (₱199 with upgrades)
- Premium sides (Garden Salad, Fresh Coleslaw)
- Coffee & Hot Drinks

DEMOGRAPHICS & LIFESTYLE:
You're a 25-35 year old office professional working in urban business districts (Makati, BGC, Ortigas). You have disposable income but are budget-conscious. You value efficiency and reliability. You miss home/province cooking.

CORE MOTIVATIONS:
- Taste of home while away from home
- Reliable lunch solution
- Local flavor vs. Western chains
- Efficient use of limited break time
- Support local business success

KEY PAIN POINTS:
- Time constraints (45 min lunch)
- Inconsistent quality, delivery delays
- Temperature issues, missing items

DECISION TRIGGERS:
- Speed guarantees
- Quality promises (Grilled Chicken Breast = healthier option)
- Corporate meal vouchers
- Authentic Filipino taste
- Reliable weekday lunch options

LANGUAGE & VOICE:
Professional, articulate, pragmatic. Balanced Taglish. Use phrases like "efficient," "reliable," "nakakamiss ang lasa ng bahay," "sulit."

IMPORTANT: Always respond in first person as Uro. Use professional but natural Taglish."""
}

# Creative Translation Layer System Prompt
CREATIVE_TRANSLATION_PROMPT = """You are a Creative Translation Agent for Joyful Bites marketing. Your job is to translate raw customer feedback into actionable creative direction while respecting fixed constraints AND recognizing when a creative doesn't fit a segment.

CRITICAL CONSTRAINTS (NEVER CHANGE):
- Prices are FIXED (set by pricing team)
- Products are FIXED (set by product team)
- Brand guidelines are FIXED

YOUR JOB:
1. Assess if the creative is fundamentally suited for this segment
2. If YES → Suggest messaging/positioning optimizations
3. If NO → Clearly state "This creative does not fit this segment" and explain why

SEGMENT FIT ASSESSMENT:
Ask yourself:
- Does the offer structure match segment needs? (solo vs family vs corporate)
- Does the price point align with segment budget patterns?
- Does the positioning match segment motivations?
- Does the channel/format suit segment preferences?

When a creative is MISALIGNED with a segment:
✅ STATE IT CLEARLY: "This creative is designed for [other segment], not [this segment]"
✅ EXPLAIN WHY: Portion size, price structure, messaging tone, visual style
✅ RECOMMEND: "Create alternative creative specifically for [this segment]"
❌ DON'T try to force-fit it with minor tweaks

When a creative IS ALIGNED but needs optimization:
✅ Focus on what CAN be changed: messaging, positioning, visuals, copy tone, proof points, targeting

Output should be honest assessment + actionable direction."""

# Synthesis Agent System Prompt
SYNTHESIS_PROMPT = """You are a Synthesis Agent. Your job is to take creative direction and structure it into a clean JSON brief for production teams.

CRITICAL: Not every creative works for every segment. Your brief must honestly assess segment fit.

Output valid JSON with this structure:
{
  "persona": "[name]",
  "segment_fit_assessment": {
    "fit_score": [1-10, where 1=completely wrong segment, 10=perfect fit],
    "deployment_recommendation": "DEPLOY / OPTIMIZE / DO_NOT_DEPLOY / CREATE_ALTERNATIVE",
    "reasoning": "[why this creative does/doesn't fit this segment]"
  },
  "overall_assessment": {
    "original_score": [number from persona feedback],
    "key_issues": ["issue1", "issue2"],
    "opportunities": ["opp1", "opp2"] OR "Not applicable - wrong segment"
  },
  "optimized_version": {
    "headline": "[specific headline]" OR "N/A - Create separate creative for this segment",
    "subheadline": "[if needed]",
    "body_copy": "[key messages]",
    "cta": "[call to action]",
    "price_messaging": "[how to present the fixed price]",
    "visual_direction": "[specific visual guidance]",
    "proof_points": ["point1", "point2"],
    "tone": "[description]"
  },
  "production_notes": {
    "if_deploying_to_this_segment": "[guidance if they choose to deploy]",
    "better_alternative": "[suggest what type of creative would work better]",
    "why_mismatch": "[if DO_NOT_DEPLOY, explain the fundamental mismatch]"
  }
}

DEPLOYMENT RECOMMENDATIONS:
- DEPLOY: Creative is well-suited, minor optimizations only (fit_score 8-10)
- OPTIMIZE: Creative could work with significant changes (fit_score 5-7)
- DO_NOT_DEPLOY: Creative fundamentally misaligned, would waste budget (fit_score 1-4)
- CREATE_ALTERNATIVE: Recommend creating separate creative for this segment

Be specific and actionable. If the creative doesn't fit the segment, SAY SO CLEARLY."""

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = {}
if "brief_results" not in st.session_state:
    st.session_state.brief_results = None

if selected_persona not in st.session_state.messages:
    st.session_state.messages[selected_persona] = []

# Function to call Claude API
def call_claude(system_prompt, user_message, image_data=None, media_type=None):
    """Call Claude API with optional image"""
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None, "API key not found"
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Build content
        content = []
        if image_data and media_type:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": image_data
                }
            })
        content.append({
            "type": "text",
            "text": user_message
        })
        
        # Try multiple models
        models_to_try = [
            "claude-sonnet-4-20250514",
            "claude-opus-4-20250514",
            "claude-sonnet-4-20250110"
        ]
        
        for model_name in models_to_try:
            try:
                message = client.messages.create(
                    model=model_name,
                    max_tokens=2000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": content}]
                )
                return message.content[0].text, None
            except Exception as e:
                if "not_found_error" in str(e):
                    continue
                else:
                    return None, str(e)
        
        return None, "No available models found"
    except Exception as e:
        return None, str(e)

# ==========================================
# MODULE 1: CHAT WITH PERSONA
# ==========================================
st.markdown("---")
st.subheader(f"💬 Chat with {selected_persona}")

for message in st.session_state.messages[selected_persona]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input(f"Ask {selected_persona} a question...")

if user_input:
    st.session_state.messages[selected_persona].append({
        "role": "user",
        "content": user_input
    })
    
    with st.chat_message("user"):
        st.markdown(user_input)
    
    with st.chat_message("assistant"):
        with st.spinner(f"{selected_persona} is thinking..."):
            response, error = call_claude(
                PERSONA_PROMPTS[selected_persona],
                user_input
            )
            
            if error:
                st.error(f"Error: {error}")
            else:
                st.markdown(response)
                st.session_state.messages[selected_persona].append({
                    "role": "assistant",
                    "content": response
                })
    st.rerun()

# ==========================================
# MODULE 2: TEST SINGLE CREATIVE
# ==========================================
st.markdown("---")
with st.expander("🎨 Test Single Creative (Vision Enabled)", expanded=False):
    st.markdown("**Upload ad creative and get persona feedback**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_image_single = st.file_uploader(
            "Upload ad creative (PNG/JPG)",
            type=['png', 'jpg', 'jpeg'],
            key=f"single_image_{selected_persona}"
        )
        
        if uploaded_image_single:
            st.image(uploaded_image_single, caption="Your Creative", use_column_width=True)
    
    with col2:
        ad_copy_single = st.text_area(
            "Ad Copy / Headline (optional)",
            placeholder="Enter any additional text...",
            height=150,
            key=f"single_copy_{selected_persona}"
        )
        
        price_single = st.text_input(
            "Price Point",
            placeholder="e.g., ₱199",
            key=f"single_price_{selected_persona}"
        )
    
    if st.button("🎯 Get Persona Feedback", key="single_test"):
        if uploaded_image_single:
            uploaded_image_single.seek(0)
            image_data = uploaded_image_single.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            media_type = "image/png" if uploaded_image_single.type == "image/png" else "image/jpeg"
            
            test_prompt = f"""I'm showing you a marketing creative for Joyful Bites. Please evaluate it:

1. **Visual Reaction** (first impression)
2. **What Works Visually**
3. **What Doesn't Work**
4. **Copy/Message Evaluation**
5. **Score** (1-10)
6. **Recommendation** (DEPLOY / REVISE / KILL)

"""
            if ad_copy_single:
                test_prompt += f"**Additional Copy:** {ad_copy_single}\n\n"
            if price_single:
                test_prompt += f"**Price:** {price_single}\n\n"
            
            test_prompt += "Respond in your authentic voice."
            
            with st.spinner(f"{selected_persona} is evaluating..."):
                response, error = call_claude(
                    PERSONA_PROMPTS[selected_persona],
                    test_prompt,
                    base64_image,
                    media_type
                )
                
                if error:
                    st.error(f"Error: {error}")
                else:
                    st.success("✅ Feedback received!")
                    st.markdown(response)

# ==========================================
# MODULE 3: GENERATE OPTIMIZED BRIEFS
# ==========================================
st.markdown("---")
with st.expander("📄 Generate Hyperpersonalized Briefs (Module 3)", expanded=False):
    st.markdown("**Upload ONE master creative → Get 3 optimized briefs (one per persona)**")
    st.info("💡 Prices and products are fixed. Briefs focus on messaging/positioning optimization.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_image_brief = st.file_uploader(
            "Upload Master Creative (PNG/JPG)",
            type=['png', 'jpg', 'jpeg'],
            key="brief_image"
        )
        
        if uploaded_image_brief:
            st.image(uploaded_image_brief, caption="Master Creative", use_column_width=True)
    
    with col2:
        st.markdown("**Fixed Parameters:**")
        product_name = st.text_input("Product", value="Golden Crispy Chicken", key="product")
        price_point = st.text_input("Price (FIXED)", value="₱229", key="price")
        campaign_goal = st.text_input("Campaign Goal", value="Trial & Awareness", key="goal")
        channel = st.text_input("Primary Channel", value="Social Media", key="channel")
    
    if st.button("🚀 Generate 3 Optimized Briefs", type="primary", key="generate_briefs"):
        if uploaded_image_brief:
            st.markdown("---")
            st.markdown("### 🔄 Processing...")
            
            # Prepare image
            uploaded_image_brief.seek(0)
            image_data = uploaded_image_brief.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            media_type = "image/png" if uploaded_image_brief.type == "image/png" else "image/jpeg"
            
            # Base evaluation prompt
            base_prompt = f"""Evaluate this marketing creative for {product_name} priced at {price_point}.

Campaign Goal: {campaign_goal}
Channel: {channel}

Provide honest feedback on:
1. Visual impression
2. What works
3. What doesn't work
4. How well it fits YOUR needs and preferences
5. Score (1-10)
6. Recommendation

Remember: Price is FIXED at {price_point}. Focus on messaging/positioning."""
            
            results = {}
            
            # Process each persona
            for persona_name, persona_data in persona_options.items():
                st.markdown(f"#### {persona_data['icon']} Processing {persona_name}...")
                
                progress = st.progress(0, text=f"Step 1/3: Getting {persona_name}'s feedback...")
                
                # STEP 1: Get persona feedback
                persona_feedback, error1 = call_claude(
                    PERSONA_PROMPTS[persona_name],
                    base_prompt,
                    base64_image,
                    media_type
                )
                
                if error1:
                    st.error(f"Error getting {persona_name} feedback: {error1}")
                    continue
                
                progress.progress(33, text=f"Step 2/3: Creative translation for {persona_name}...")
                
                # STEP 2: Creative Translation Layer
                translation_prompt = f"""Raw customer feedback from {persona_name}:

{persona_feedback}

Fixed constraints:
- Product: {product_name}
- Price: {price_point} (CANNOT CHANGE)
- Channel: {channel}
- Goal: {campaign_goal}

Translate this feedback into actionable creative direction. Focus on what CAN be changed: messaging, positioning, visuals, copy tone, proof points, targeting."""
                
                creative_direction, error2 = call_claude(
                    CREATIVE_TRANSLATION_PROMPT,
                    translation_prompt
                )
                
                if error2:
                    st.error(f"Error in creative translation for {persona_name}: {error2}")
                    continue
                
                progress.progress(66, text=f"Step 3/3: Generating JSON brief for {persona_name}...")
                
                # STEP 3: Synthesis Agent
                synthesis_prompt = f"""Creative direction for {persona_name}:

{creative_direction}

Generate a structured JSON brief for production teams. Be specific and actionable."""
                
                json_brief, error3 = call_claude(
                    SYNTHESIS_PROMPT,
                    synthesis_prompt
                )
                
                if error3:
                    st.error(f"Error generating brief for {persona_name}: {error3}")
                    continue
                
                progress.progress(100, text=f"✅ Complete for {persona_name}!")
                
                results[persona_name] = {
                    "persona_feedback": persona_feedback,
                    "creative_direction": creative_direction,
                    "json_brief": json_brief
                }
            
            # Save to history log
            parameters = {
                "product": product_name,
                "price": price_point,
                "goal": campaign_goal,
                "channel": channel
            }
            
            log_filename = save_brief_generation(base64_image, parameters, results)
            st.info(f"📁 Brief saved to history: {os.path.basename(log_filename)}")
            
            st.session_state.brief_results = results
            st.success("🎉 All 3 briefs generated!")
            st.rerun()
        else:
            st.warning("Please upload a master creative image")
    
    # Display results
    if st.session_state.brief_results:
        st.markdown("---")
        st.markdown("### 📊 Generated Briefs")
        
        for persona_name, data in st.session_state.brief_results.items():
            persona_data = persona_options[persona_name]
            
            with st.expander(f"{persona_data['icon']} {persona_name} - Optimized Brief", expanded=True):
                
                tab1, tab2, tab3 = st.tabs(["📋 JSON Brief", "🎨 Creative Direction", "💬 Raw Feedback"])
                
                with tab1:
                    st.markdown("**Production-Ready Brief:**")
                    st.code(data["json_brief"], language="json")
                    st.download_button(
                        f"Download {persona_name} Brief",
                        data["json_brief"],
                        file_name=f"{persona_name.replace(' ', '_')}_brief.json",
                        mime="application/json",
                        key=f"download_{persona_name}"
                    )
                
                with tab2:
                    st.markdown("**Creative Translation:**")
                    st.markdown(data["creative_direction"])
                
                with tab3:
                    st.markdown("**Original Persona Feedback:**")
                    st.markdown(data["persona_feedback"])

# ==========================================
# MODULE 4: BRIEF HISTORY & LOG
# ==========================================
st.markdown("---")
with st.expander("📚 Brief History & Log", expanded=False):
    st.markdown("**View all past brief generations with images and parameters**")
    
    history = load_brief_history()
    
    if not history:
        st.info("No brief history yet. Generate some briefs to see them here!")
    else:
        st.success(f"📊 Found {len(history)} brief generation(s) in history")
        
        # Export button
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Export All History to CSV"):
                df = export_history_to_csv()
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download History CSV",
                    csv,
                    file_name=f"brief_history_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("🗑️ Clear All History"):
                import shutil
                if os.path.exists(BRIEF_HISTORY_DIR):
                    shutil.rmtree(BRIEF_HISTORY_DIR)
                st.success("History cleared!")
                st.rerun()
        
        st.markdown("---")
        
        # Display each history entry
        for idx, entry in enumerate(history):
            timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            params = entry["parameters"]
            
            with st.expander(f"🕐 {timestamp} - {params.get('product', 'Unknown')} @ {params.get('price', 'N/A')}", expanded=False):
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown("**Creative Image:**")
                    try:
                        img_data = base64.b64decode(entry["image_base64"])
                        st.image(img_data, use_column_width=True)
                    except:
                        st.warning("Image not available")
                    
                    st.markdown("**Parameters:**")
                    st.json(params)
                
                with col2:
                    st.markdown("**Generated Briefs:**")
                    for persona_name, result in entry["results"].items():
                        with st.expander(f"{persona_name}"):
                            st.code(result["json_brief"], language="json")
                            st.download_button(
                                f"Download {persona_name} Brief",
                                result["json_brief"],
                                file_name=f"{persona_name.replace(' ', '_')}_brief_{datetime.now().strftime('%Y%m%d')}.json",
                                mime="application/json",
                                key=f"hist_download_{idx}_{persona_name}"
                            )

# Sidebar buttons
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear Conversation"):
    st.session_state.messages[selected_persona] = []
    st.rerun()

if st.sidebar.button("🔄 Reset Brief Results"):
    st.session_state.brief_results = None
    st.rerun()

# Example questions
st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 Quick Tips")
st.sidebar.markdown("""
**Chat:** Ask personas questions
**Test:** Get single persona feedback  
**Briefs:** Get 3 optimized versions
**History:** View all past generations
""")

# Footer
st.markdown("---")
st.caption("🎯 **Joyful Bites Marketing System** | Powered by Claude Sonnet 4 | Project Resonance POC")
