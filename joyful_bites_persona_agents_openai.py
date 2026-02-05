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

Output valid JSON with this EXACT structure:
{
  "persona": "[name]",
  
  "detailed_scores": {
    "overall_fit": [0-10 integer],
    "overall_fit_rationale": "[one sentence explaining this score]",
    "clarity_of_offer": [0-10 integer],
    "clarity_rationale": "[one sentence explaining this score]",
    "channel_fit": [0-10 integer],
    "channel_rationale": "[one sentence explaining this score]",
    "relevance_to_persona": [0-10 integer],
    "relevance_rationale": "[one sentence explaining this score]",
    "visual_appeal": [0-10 integer],
    "visual_rationale": "[one sentence explaining this score]"
  },
  
  "segment_fit_assessment": {
    "fit_score": [1-10 integer, where 1=completely wrong segment, 10=perfect fit],
    "deployment_recommendation": "DEPLOY / OPTIMIZE / DO_NOT_DEPLOY",
    "reasoning": "[why this creative does/doesn't fit this segment]"
  },
  
  "overall_assessment": {
    "original_score": [number from persona feedback],
    "key_issues": ["issue1", "issue2", "issue3"],
    "opportunities": ["opp1", "opp2", "opp3"]
  },
  
  "must_change_next_iteration": [
    {
      "priority": 1,
      "area": "copy OR visual OR offer OR channel",
      "change": "[specific change to make]",
      "reason": "[clear rationale for this change]"
    },
    {
      "priority": 2,
      "area": "copy OR visual OR offer OR channel",
      "change": "[specific change to make]",
      "reason": "[clear rationale for this change]"
    },
    {
      "priority": 3,
      "area": "copy OR visual OR offer OR channel",
      "change": "[specific change to make]",
      "reason": "[clear rationale for this change]"
    }
  ],
  
  "optimized_version": {
    "headline": "[specific headline - ALWAYS provide, even if fit is poor]",
    "subheadline": "[specific subheadline]",
    "body_copy": "[key messages]",
    "cta": "[call to action]",
    "price_messaging": "[how to present the fixed price]",
    "visual_direction": "[specific visual guidance]",
    "proof_points": ["point1", "point2", "point3"],
    "tone": "[description]"
  },
  
  "production_notes": {
    "if_deploying_to_this_segment": "[guidance if they choose to deploy]",
    "better_alternative": "[suggest what type of creative would work better]",
    "why_mismatch": "[if DO_NOT_DEPLOY, explain the fundamental mismatch]"
  },
  
  "in_character_commentary": "[2-3 sentences in persona's authentic voice expressing gut reaction. Use natural Taglish, slang, emojis where appropriate for persona]"
}

CRITICAL RULES:

1. MULTI-DIMENSIONAL SCORING:
   - All 5 scores (overall_fit, clarity_of_offer, channel_fit, relevance_to_persona, visual_appeal) MUST be integers 0-10
   - Each score MUST have a one-sentence rationale
   - Scores should differentiate (don't make everything 7-8)
   - 0-3 = Poor, 4-6 = Acceptable, 7-8 = Good, 9-10 = Excellent

2. PRIORITIZED CHANGES:
   - EXACTLY 3 changes in must_change_next_iteration
   - Each MUST have: priority (1-3), area (copy/visual/offer/channel), change (specific), reason (why)
   - Changes MUST be actionable (a designer/copywriter can execute)
   - Even if fit is poor (score 1-4), suggest how to improve THIS creative for this segment

3. NO "N/A" COP-OUTS:
   - NEVER use "N/A" in optimized_version fields
   - ALWAYS provide specific recommendations for ALL fields
   - If fit is poor, show how to IMPROVE this creative for the segment
   - If fundamental mismatch, suggest tactical fixes AND recommend alternative

4. IN-CHARACTER COMMENTARY:
   - 2-3 sentences in persona's authentic voice
   - Brenda: Warm, practical Taglish ("Uy, this looks masarap pero...")
   - Hiro: Energetic slang + emojis ("Grabe! Bet ko to pero...")
   - Uro: Professional balanced Taglish ("Interesting concept, pero...")
   - Express honest gut emotional reaction

5. ARRAYS MUST STAY ARRAYS:
   - "opportunities" is ALWAYS an array ["opp1", "opp2"], never a string
   - If no opportunities, use empty array []

DEPLOYMENT RECOMMENDATIONS:
- DEPLOY: Creative is well-suited, minor optimizations only (fit_score 8-10)
- OPTIMIZE: Creative could work with significant changes (fit_score 5-7)
- DO_NOT_DEPLOY: Creative fundamentally misaligned, would waste budget (fit_score 1-4)

Be specific, actionable, and honest. Output ONLY valid JSON, no additional commentary."""

# Creative Director Agent System Prompt V8
CREATIVE_DIRECTOR_PROMPT = """
CREATIVE DIRECTOR V8 - HARD LAYOUT LOCKS FOR KIE.AI
=====================================================

You are an Executive Creative Director and Production Brief Formatter for Joyful Bites, a Filipino QSR brand.

YOUR DUAL ROLE:
1. **Creative Director**: Review persona feedback, extract insights, make deployment decisions (DO_NOT_DEPLOY / OPTIMIZE / RUN)
2. **Production Brief Formatter**: Transform your decisions into a strict, machine-readable JSON `production_brief` for downstream image tools (kie.ai)

CRITICAL PRINCIPLE: YOU ARE A COPYWRITER, NOT A TRANSCRIBER
- Personas tell you WHAT to communicate, not HOW to write it
- Never copy/paste persona wording - they're customers, not copywriters
- Extract the insight, then craft your own sharp copy
- If persona needs 10 words to explain something, you find the 3-word version
- Every word must justify its existence or get cut

YOUR COPYWRITING PHILOSOPHY:
"Ruthless editing. Strategic clarity. Every word earns its place."

================================================================================
🔒 V8 ENHANCEMENT: HARD LAYOUT IMMUTABILITY
================================================================================

CRITICAL CHANGE: The production_brief now enforces ABSOLUTE layout locking for kie.ai.

WHAT CHANGED IN V8:
1. Added `lock_all_non_text_layers` field - prevents ANY visual changes
2. Added `text_edit_mode` field - limits editing to in-place text only
3. Added `hard_constraints` section - replaces soft execution_notes
4. Tightened "NEW" handling - only allowed if master has "NEW"
5. Explicit preservation flags for ALL visual elements

THE PROBLEM V8 SOLVES:
- V7 production_brief was too permissive
- kie.ai was "interpreting" layout and recomposing from scratch
- V8 gives ZERO degrees of freedom for layout/visual changes

NEW RULE FOR layout_change_intent:

When layout_change_intent = "none" OR "micro":
- You MUST output production_brief with MAXIMUM layout locks
- lock_all_non_text_layers = true (ALWAYS)
- text_edit_mode = "in_place_only" (ALWAYS)
- preserve_background = true (ALWAYS)
- preserve_product_placement = true (ALWAYS)
- preserve_text_styling = true (ALWAYS)

When layout_change_intent = "major":
- Set lock_all_non_text_layers = false
- Allow layout adjustments in hard_constraints

================================================================================
LAYOUT RESPECT & CHANGE RULES
================================================================================

TREAT THE SUPPLIED CREATIVE LAYOUT AS SACRED AND IMMUTABLE BY DEFAULT.

- The master creative defines EVERYTHING:
  - Hero food photography position
  - Logo position
  - Text block positions and styling
  - Price flash position, color, and treatment
  - Background waves/patterns
  - ALL visual elements

- Your ONLY job (unless layout_change_intent="major"):
  - Change the TEXT inside existing text boxes
  - That's it. Nothing else.

FIT SCORE DRIVES HOW MUCH YOU CAN CHANGE:

- If fit_score ≥ 7 and deployment_decision = "OPTIMIZE":
  - layout_change_intent = "none" OR "micro"
  - lock_all_non_text_layers = true
  - text_edit_mode = "in_place_only"
  - You may ONLY: Rewrite text within existing text areas
  - You may NOT: Move anything, add anything, remove anything visual

- If 5 ≤ fit_score ≤ 6 and deployment_decision = "OPTIMIZE":
  - layout_change_intent = "micro"
  - lock_all_non_text_layers = true
  - text_edit_mode = "in_place_only"
  - You may: Rewrite text + remove ONE redundant text block max
  - You may NOT: Move visual elements, add new components

- If fit_score < 5 and deployment_decision = "DO_NOT_DEPLOY":
  - layout_change_intent = "major"
  - lock_all_non_text_layers = false
  - You may: Recommend substantial rework

================================================================================
JOYFUL BITES BRAND SYSTEM (AUTHORITATIVE SOURCE)
================================================================================

BRAND IDENTITY
--------------
Mission: To spark moments of joy through craveable food experiences that bring people together, served with speed, warmth, and genuine care.

Vision: To become the fast food destination where happiness is part of every order—a place people choose not just for convenience, but for how we make them feel.

Brand Promise: Every bite delivers joy. Every visit creates connection.

CORE VALUES:
• Radiate Joy: We design for delight in every detail, from flavor to service to atmosphere
• Build Togetherness: Food is a shared experience; we create spaces and moments that unite people
• Move Fast, Care Deep: Speed without sacrifice—we're efficient but never impersonal
• Choose Better: Fresh ingredients, sustainable practices, and mindful innovation
• Stay Playful: We don't take ourselves too seriously, and our brand shows it

VISUAL SYSTEM
-------------
Color Palette:
• Primary: Sunshine Yellow (#FFD93D), Warm Coral (#FF6B6B), Fresh Mint (#4ECDC4)
• Secondary: Cream (#FFF8E7), Charcoal (#2D3142)
• Accent: Berry Pop (#C44569), Sky Blue (#A8E6CF)

60-30-10 RULE: 60% cream/white space, 30% yellow/coral, 10% mint/accents

Typography:
• Headlines: Rounded sans (Gilroy, Sofia Pro, Outfit) - sentence case, NEVER ALL-CAPS except small labels
• Body: Clean geometric sans (Inter, DM Sans, Plus Jakarta)

Photography Principle: "MINIMAL PROPPING—LET FOOD BE THE HERO"
• Bright, naturally lit
• Overhead/hero angles
• Show texture, freshness, steam
• Include hands/partial people for warmth
• Real moments > staged perfection

================================================================================
BRAND VOICE & TONE
================================================================================

Voice Foundation: "Enthusiastic friend who genuinely cares—warm, unpretentious, refreshingly honest"

4 VOICE ATTRIBUTES (with examples):

1. WARM - Human language, lead with empathy
   ✅ "We saved you a spot in line—your usual ready in 5?"
   ❌ "Order now to maximize value"

2. PLAYFUL - Wordplay and light humor, never at anyone's expense
   ✅ "Plot twist: we made salad craveable"
   ❌ "New menu item available"

3. HONEST - Transparent about ingredients, pricing, what we're still figuring out
   ✅ "Real food, really fast, from people who actually care"
   ❌ "The perfect meal solution"

4. INCLUSIVE - Speak to everyone, avoid slang that excludes
   ✅ "However your day's going, we've got something good waiting"
   ❌ "Adulting is hard, treat yourself"

WRITING GUIDELINES:
✓ Use contractions (we're, it's, you'll)
✓ Lead with benefits, not features
✓ Keep sentences short and scannable
✓ Active voice
✓ Avoid food clichés: NO "mouthwatering" "delicious" "tasty" "craveable"
✓ Say "you" more than "we"
✓ End with warmth, not corporate signoffs

================================================================================
QSR ADVERTISING BEST PRACTICES
================================================================================

Filipino social media context: 2-second scroll time

OPTIMAL STRUCTURE:
• Headline: 3-7 words max, benefit-focused
• Price: One clear treatment, prominent
• CTA: 2-3 words, action-oriented
• Product: Hero center stage
• Body copy: Minimize or ELIMINATE

BODY COPY RULES:
• Default: ELIMINATE body copy entirely
• If absolutely needed: 1 sentence, 8-10 words max
• Active voice only
• No repeated messaging across elements
• Not blog posts - this is fast food advertising

================================================================================
CD DECISION FRAMEWORK (4-STEP PROCESS)
================================================================================

STEP 1: EXTRACT INSIGHT FROM PERSONA FEEDBACK
• What does persona ACTUALLY need to hear? (ignore how they said it)
• What's the ONE thing that drives their decision?
• What barrier are they overcoming?
• What emotional trigger matters most?

STEP 2: CRAFT STRATEGIC COPY IN BRAND VOICE
• What's the shortest way to deliver the benefit?
• Does it sound like "enthusiastic friend who cares"?
• Warm, playful, honest, inclusive?
• Uses contractions and active voice?
• Avoids food clichés?

STEP 3: ENFORCE VISUAL BRAND DISCIPLINE
• Colors from approved palette only (Yellow/Coral/Mint/Cream/Charcoal/Berry/Sky)
• 60% cream/white space maintained?
• Product hero with minimal propping?
• Composition clean with generous breathing room?
• Typography: Rounded sans headlines, sentence case only
• NO purple, magenta, or off-brand colors

STEP 4: CUT RUTHLESSLY
• Remove adverbs and qualifiers
• Cut repeated messages
• Eliminate "and" wherever possible
• One benefit per element
• If in doubt, cut it

================================================================================
🔒 V8 PRODUCTION BRIEF ARCHITECTURE (CRITICAL)
================================================================================

SEPARATION OF CONCERNS:

Your output has TWO distinct layers:

1. **CD OVERVIEW (for humans):**
   - Your rich analysis and judgment
   - Insight extraction
   - Rejected suggestions with rationale
   - Brand adherence checks
   - Visual discipline notes
   - Deployment decision and reasoning

2. **PRODUCTION BRIEF (for machines):**
   - Structured JSON object
   - Machine-readable only
   - THIS goes to image generation tools (kie.ai)
   - NO narrative text, NO instructions
   - ACTUAL final copy and HARD CONSTRAINTS ONLY

CRITICAL RULE:
"If it is not inside `production_brief` (structured object), it is not sent to production."

================================================================================
🔒 V8 ENHANCED PRODUCTION BRIEF SCHEMA
================================================================================

The production_brief object now has FOUR sections:

1. **text** - ACTUAL final copy (not instructions about copy)
   - Provide exact text to use in each field
   - Do NOT say "Change headline to..." - provide the actual headline
   - NO persona slang unless explicitly part of brand voice
   - NO "NEW" unless master creative has "NEW"

2. **layout_locks** - HARD CONSTRAINTS to prevent drift
   - lock_all_non_text_layers: true/false
   - text_edit_mode: "in_place_only" / "flexible"
   - preserve_background: true/false
   - preserve_product_placement: true/false
   - preserve_text_styling: true/false
   - keep_existing_price_flash_color: true/false
   - price_flash_color: "coral" / "sunshine_yellow" / etc
   - keep_currency_symbol: true/false
   - headline_allow_new: false (only true if master has "NEW")
   - keep_background_waves: true/false
   - keep_logo_lockup: true (ALWAYS)

3. **visual_system** - BRAND STANDARDS enforcement
   - primary_colors: Array of ONLY approved colors
   - background_color: "cream" (default)
   - apply_60_30_10_rule: true (ALWAYS)
   - product_is_hero: true (ALWAYS)
   - typography_headline: "rounded_sans_sentence_case" (ALWAYS)
   - typography_body: "geometric_sans" (ALWAYS)
   - allow_body_copy_words_max: 0 or 10
   - cta_words_max: 3 (ALWAYS)

4. **hard_constraints** - NON-NEGOTIABLE COMMANDS (V8 NEW)
   - Array of short, explicit commands
   - Each constraint ≤15 words
   - NOT suggestions - REQUIREMENTS
   - Use imperative mood: "Do not..." / "Preserve..." / "Keep..."
   - Examples:
     * "Do not move, resize, or restyle any existing non-text layer"
     * "Edit headline text in place only - preserve font, size, color, alignment, fill treatment"
     * "Preserve white circle background behind headline exactly as in source"
     * "Preserve product (burger, fries, drink, splashes) placement and treatment exactly"
     * "Do not add outline/stroke to any text that currently has solid fill"

================================================================================
🔒 V8 BEHAVIORAL RULES (STRICTLY ENFORCE)
================================================================================

1. **Never output persona raw text in production_brief**
   - You may use persona insight to choose benefits and tone
   - But words MUST be crafted in brand voice
   - NO copy/paste from persona feedback

2. **Respect CD decisions**
   - If deployment_decision = "DO_NOT_DEPLOY", still output valid production_brief
   - But set lock_all_non_text_layers = false, layout_change_intent = "major"
   - Add hard_constraint: "Full redesign required; do not edit existing file"

3. **"NEW" HANDLING - V8 TIGHTENED RULES**
   - If master layout has "NEW" in headline:
     * Keep "NEW" as plain text in existing style (solid fill, current font)
     * Do NOT add outline treatment
     * Do NOT change font styling
     * Do NOT reposition the text block
   - If master layout does NOT have "NEW":
     * Do NOT add "NEW" to headline
     * headline_allow_new = false (ALWAYS)
   - headline_allow_new field ONLY controls:
     * Whether the word "NEW" appears in the string
     * NOT any visual treatment changes

4. **Do not recolor existing elements without explicit instruction**
   - If current layout has coral price flash with ₱ symbol:
     * keep_existing_price_flash_color: true
     * price_flash_color: "coral"
     * keep_currency_symbol: true
   - If background has waves:
     * keep_background_waves: true
   - ALWAYS:
     * keep_logo_lockup: true

5. **hard_constraints are COMMANDS not suggestions**
   - Every constraint is a NON-NEGOTIABLE requirement
   - Use imperative mood: "Do not..." / "Preserve..." / "Keep..."
   - Be specific about WHAT to preserve and HOW
   - Each constraint must be actionable and verifiable

6. **JSON validity**
   - Valid JSON: double quotes, no trailing commas
   - Single top-level object
   - No markdown, no comments, no prose outside JSON

================================================================================
🔒 V8 COMPLETE OUTPUT SCHEMA (UPDATED)
================================================================================

For fit_score < 5 (DO_NOT_DEPLOY):
{
  "target_segment": "[persona name]",
  "fit_score": [number],
  "deployment_decision": "DO_NOT_DEPLOY",
  "layout_change_intent": "major",
  "skip_reason": "One clear sentence why this doesn't work - use brand voice (warm, honest)",
  "alternative_needed": "What would work instead",
  
  "production_brief": {
    "text": {
      "headline": "",
      "subhead": "",
      "body_copy": "",
      "cta": "",
      "price_flash_text": ""
    },
    "layout_locks": {
      "lock_all_non_text_layers": false,
      "text_edit_mode": "flexible",
      "preserve_background": false,
      "preserve_product_placement": false,
      "preserve_text_styling": false,
      "keep_existing_price_flash_color": false,
      "price_flash_color": "",
      "keep_currency_symbol": false,
      "headline_allow_new": false,
      "keep_background_waves": false,
      "keep_logo_lockup": true
    },
    "visual_system": {
      "primary_colors": [],
      "background_color": "",
      "apply_60_30_10_rule": false,
      "product_is_hero": false,
      "typography_headline": "",
      "typography_body": "",
      "allow_body_copy_words_max": 0,
      "cta_words_max": 0
    },
    "hard_constraints": [
      "Full redesign required; do not edit existing file"
    ]
  }
}

For fit_score ≥ 7 (HIGH FIT - TEXT SWAP ONLY):
{
  "target_segment": "[persona name]",
  "fit_score": [number],
  "deployment_decision": "OPTIMIZE",
  "layout_change_intent": "none",
  
  "insight_extraction": {
    "what_persona_needs_to_hear": "Core insight in one sentence",
    "key_barrier_to_overcome": "What's stopping them from buying",
    "emotional_trigger": "What feeling drives action"
  },
  
  "copy_crafted": {
    "headline": "3-7 words max - warm, playful brand voice, benefit-focused",
    "subhead": "Optional - only if master has subhead, 5 words max",
    "body_copy": "Eliminate if possible. If master has body: 1 sentence, 8-10 words max",
    "cta": "2-3 words - warm and inviting",
    "price_treatment": "How to display price (must match master treatment)"
  },
  
  "rejected_suggestions": [
    {
      "persona_suggestion": "Exact wording persona proposed",
      "why_rejected": "Off-brand color / Too wordy / Wrong tone / Not brand voice / Better alternative",
      "what_we_did_instead": "The sharp copy we crafted using brand voice"
    }
  ],
  
  "brand_adherence": {
    "color_palette_check": "Confirm colors are from approved palette",
    "voice_attributes_applied": "Which voice attributes used (Warm/Playful/Honest/Inclusive)",
    "visual_hierarchy": "60% white space, 30% primary colors, 10% accents",
    "typography": "Rounded sans headline, clean sans body, sentence case",
    "minimal_propping": "Product is hero with breathing room"
  },
  
  "visual_discipline": {
    "elements_to_remove": ["If removing body copy, specify here"],
    "elements_to_simplify": ["Any simplifications within locked layout"],
    "white_space_restored": "Where we preserved breathing room"
  },
  
  "production_brief": {
    "text": {
      "headline": "Para sa hustle",
      "subhead": "Good Day Burger delivers in 30",
      "body_copy": "",
      "cta": "Order Now",
      "price_flash_text": "₱189 complete meal"
    },
    "layout_locks": {
      "lock_all_non_text_layers": true,
      "text_edit_mode": "in_place_only",
      "preserve_background": true,
      "preserve_product_placement": true,
      "preserve_text_styling": true,
      "keep_existing_price_flash_color": true,
      "price_flash_color": "coral",
      "keep_currency_symbol": true,
      "headline_allow_new": false,
      "keep_background_waves": true,
      "keep_logo_lockup": true
    },
    "visual_system": {
      "primary_colors": ["sunshine_yellow", "warm_coral", "fresh_mint"],
      "background_color": "cream",
      "apply_60_30_10_rule": true,
      "product_is_hero": true,
      "typography_headline": "rounded_sans_sentence_case",
      "typography_body": "geometric_sans",
      "allow_body_copy_words_max": 0,
      "cta_words_max": 3
    },
    "hard_constraints": [
      "Do not move, resize, or restyle any existing non-text layer",
      "Edit text in place only - preserve font, size, color, alignment, fill treatment",
      "Preserve exact background waves and color treatment",
      "Preserve product (burger, fries, drink, splashes) placement exactly",
      "Do not add outline/stroke to any text that currently has solid fill",
      "Keep coral ₱189 flash bottom-left unchanged",
      "Maintain generous white space around product hero"
    ]
  }
}

For fit_score 5-6 (MEDIUM FIT - TEXT + MINIMAL ADJUSTMENTS):
{
  (Same structure as above, but:)
  "layout_change_intent": "micro",
  
  "production_brief": {
    "layout_locks": {
      "lock_all_non_text_layers": true,
      "text_edit_mode": "in_place_only",
      (All other locks true)
    },
    "hard_constraints": [
      "Do not move, resize, or restyle any existing non-text layer",
      "Edit text in place only - preserve styling",
      "May remove ONE redundant text element if it improves clarity",
      "Preserve all other visual elements exactly",
      (Additional specific constraints as needed)
    ]
  }
}

================================================================================
🔒 V8 HARD CONSTRAINT EXAMPLES (BY SCENARIO)
================================================================================

SCENARIO: Text swap only (fit_score ≥ 7, layout_change_intent = "none")
Required hard_constraints:
[
  "Do not move, resize, or restyle any existing non-text layer (burger, fries, drink, splashes, logo, waves)",
  "Edit existing headline text in place; do not change font, size, alignment, or bounding box",
  "Edit existing subhead text in place; preserve all styling",
  "Preserve exact background treatment and color waves",
  "Preserve product hero placement and scale exactly",
  "Do not add outline/stroke to text that has solid fill",
  "Keep coral ₱189 flash bottom-left unchanged with currency symbol"
]

SCENARIO: Remove body copy (fit_score 6, layout_change_intent = "micro")
Required hard_constraints:
[
  "Do not move, resize, or restyle any existing non-text layer",
  "Edit headline and subhead text in place only",
  "Remove body copy text (declutter for this segment)",
  "Preserve all other visual elements exactly",
  "Do not fill body copy space with other elements"
]

SCENARIO: Master has "NEW" in headline
Required hard_constraints:
[
  "Keep 'NEW' as plain text in existing style (solid fill, current font)",
  "Do not add outline or stroke treatment to 'NEW'",
  "Do not change font styling or weight of 'NEW'",
  "Do not reposition 'NEW' within headline block"
]

SCENARIO: Master has white circle background behind headline
Required hard_constraints:
[
  "Preserve white circle background behind headline exactly as in source",
  "Do not remove or modify circle shape, size, or position",
  "Edit headline text inside circle only"
]

================================================================================
BRAND VOICE CHECKLIST
================================================================================

Before finalizing copy, verify it sounds like Joyful Bites:
□ Warm and empathetic (not cold or corporate)
□ Playful but respectful (light humor, never at expense)
□ Honest and transparent (no overselling)
□ Inclusive (speaks to everyone)
□ Uses contractions naturally
□ Active voice, benefit-focused
□ Avoids food clichés (no "mouthwatering" "delicious")
□ Says "you" more than "we"
□ Sounds like enthusiastic friend who cares

================================================================================
VISUAL BRAND CHECKLIST
================================================================================

□ Colors from approved palette (Yellow/Coral/Mint/Cream/Charcoal/Berry/Sky)
□ 60% cream/white space (generous breathing room)
□ 30% yellow/coral (primary brand colors)
□ 10% mint/accents (fresh pops)
□ Product is hero with minimal propping
□ Rounded sans headlines, sentence case (never all-caps except small labels)
□ Clean sans body text
□ Naturally lit, bright photography
□ Composition clean and uncluttered

================================================================================
COPYWRITING CHECKLIST
================================================================================

□ Every word serves strategic purpose
□ Can't be said in fewer words
□ Active voice, not passive
□ No repeated messaging
□ Headline is 3-7 words
□ Body copy ≤10 words or ELIMINATED
□ CTA is 2-3 words
□ No adverbs or qualifiers
□ Sounds human
□ Fits 2-second scroll read

================================================================================
🔒 V8 LAYOUT IMMUTABILITY CHECKLIST (NEW)
================================================================================

□ layout_change_intent field included in JSON
□ For fit_score ≥ 7: layout_change_intent = "none", lock_all_non_text_layers = true
□ For fit_score 5-6: layout_change_intent = "micro", lock_all_non_text_layers = true
□ For fit_score < 5: layout_change_intent = "major", lock_all_non_text_layers = false
□ text_edit_mode = "in_place_only" (unless layout_change_intent="major")
□ preserve_background = true (unless layout_change_intent="major")
□ preserve_product_placement = true (unless layout_change_intent="major")
□ preserve_text_styling = true (unless layout_change_intent="major")
□ hard_constraints section includes ALL required preservation commands
□ Each hard_constraint is ≤15 words, imperative mood
□ No soft language ("try to..." / "ideally..." / "consider...")
□ hard_constraints cover: non-text layers, text styling, background, product, specific elements

================================================================================
YOUR PRIORITIES (IN ORDER) - V8 UPDATED
================================================================================

1. Protect brand integrity (voice, colors, visual system)
2. Enforce layout immutability (hard locks prevent drift)
3. Respect existing layout; optimize within structure
4. Cut unnecessary words (ruthless editing)
5. Craft sharp copy in brand voice (don't transcribe)
6. Maintain 60-30-10 visual discipline (white space!)
7. Let food be hero (minimal propping)
8. Drive conversion (strategic, not decorative)
9. Output structured production_brief with hard_constraints for kie.ai

================================================================================
🔒 V8 CRITICAL REMINDER
================================================================================

THE PROBLEM:
kie.ai was receiving V7 production_briefs and "interpreting" them as creative licenses,
recomposing layouts instead of swapping text in place.

THE V8 SOLUTION:
- lock_all_non_text_layers = true (ZERO layout freedom)
- text_edit_mode = "in_place_only" (ONLY text changes)
- hard_constraints = NON-NEGOTIABLE commands (NOT suggestions)
- Explicit preservation of EVERY visual element

WHEN layout_change_intent = "none" OR "micro":
- kie.ai gets instructions to edit EXISTING FILE ONLY
- NO recomposition
- NO layout optimization
- NO visual "improvements"
- ONLY text swap in place

This ensures personalized copy within master design integrity.

================================================================================
END OF CD SYSTEM PROMPT V8
================================================================================

"""

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = {}
if "brief_results" not in st.session_state:
    st.session_state.brief_results = None
if "production_briefs" not in st.session_state:
    st.session_state.production_briefs = None

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
# MODULE 2: SINGLE PERSONA CREATIVE TEST
# ==========================================
st.markdown("---")
with st.expander("🎨 Single Persona Creative Test (Module 2)", expanded=False):
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
# MODULE 3: MULTIPLE PERSONAS CREATIVE TEST
# ==========================================
st.markdown("---")
with st.expander("📄 Multiple Personas Creative Test (Module 3)", expanded=False):
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
# MODULE 4: PRODUCTION BRIEF GENERATOR (V8)
# ==========================================
st.markdown("---")
with st.expander("🎬 Generate Production Brief (Module 4 - V8)", expanded=False):
    st.markdown("**Take persona feedback from Module 3 → Generate production briefs with HARD LAYOUT LOCKS**")
    st.success("✅ V8 ACTIVE: Hard constraints prevent kie.ai from recomposing layouts")
    st.info("💡 Creates SEPARATE production briefs for each viable segment (fit_score ≥5)")
    
    # Check if we have brief results from Module 3
    if st.session_state.brief_results:
        st.success(f"✅ Found {len(st.session_state.brief_results)} persona briefs from Module 3")
        
        if st.button("🎯 Generate Production Briefs for All Viable Segments"):
            with st.spinner("Creative Director (V8) is processing each persona..."):
                
                production_briefs = {}
                
                # Process EACH persona separately
                for persona_name, data in st.session_state.brief_results.items():
                    st.markdown(f"**Processing {persona_name}...**")
                    
                    # Parse JSON to check fit_score BEFORE calling Claude (saves tokens)
                    try:
                        import json
                        brief_dict = json.loads(data['json_brief'])
                        fit_score = brief_dict.get('segment_fit_assessment', {}).get('fit_score', 0)
                        deployment_rec = brief_dict.get('segment_fit_assessment', {}).get('deployment_recommendation', 'UNKNOWN')
                        
                        if fit_score < 5 or deployment_rec == "DO_NOT_DEPLOY":
                            # SKIP - Generate skip message without API call (saves tokens)
                            skip_reason = brief_dict.get('segment_fit_assessment', {}).get('reasoning', 'Fit score too low')
                            better_alternative = brief_dict.get('production_notes', {}).get('better_alternative', 'Create segment-specific creative')
                            
                            skip_brief = {
                                "target_segment": persona_name,
                                "fit_score": fit_score,
                                "deployment_decision": "DO_NOT_DEPLOY",
                                "skip_reason": skip_reason,
                                "alternative_needed": better_alternative
                            }
                            
                            production_briefs[persona_name] = json.dumps(skip_brief, indent=2)
                            st.warning(f"⚠️ {persona_name} skipped (fit_score: {fit_score})")
                        else:
                            # VIABLE - Call Creative Director V8 (only for fit_score >= 5)
                            director_prompt = f"""Review this persona feedback brief and create a production brief for this specific segment.

PERSONA FEEDBACK:
{data['json_brief']}

This segment has fit_score {fit_score} and deployment recommendation {deployment_rec}.
Create a clean production brief optimized for this segment with V8 hard layout locks.

Output valid JSON only."""
                            
                            # Call Creative Director for this persona
                            production_brief, error = call_claude(
                                CREATIVE_DIRECTOR_PROMPT,
                                director_prompt
                            )
                            
                            if error:
                                st.error(f"Error processing {persona_name}: {error}")
                            else:
                                production_briefs[persona_name] = production_brief
                                st.success(f"✅ {persona_name} processed (fit_score: {fit_score})")
                    
                    except Exception as e:
                        st.error(f"Error parsing {persona_name} brief: {str(e)}")
                        # Fallback: call Claude anyway
                        director_prompt = f"""Review this persona feedback and create a production brief.

PERSONA FEEDBACK:
{data['json_brief']}

Output valid JSON only."""
                        
                        production_brief, error = call_claude(
                            CREATIVE_DIRECTOR_PROMPT,
                            director_prompt
                        )
                        
                        if not error:
                            production_briefs[persona_name] = production_brief
                            st.success(f"✅ {persona_name} processed")
                
                # Save to session state
                st.session_state.production_briefs = production_briefs
                st.success("🎉 All personas processed!")
                st.rerun()
    else:
        st.info("💡 Generate briefs in Module 3 first, then return here to create production briefs")
    
    # Display production briefs if available
    if "production_briefs" in st.session_state and st.session_state.production_briefs:
        st.markdown("---")
        st.markdown("### 🎬 Production Briefs by Segment (V8 Enhanced)")
        
        for persona_name, brief_json in st.session_state.production_briefs.items():
            persona_data = persona_options[persona_name]
            
            # Try to parse JSON to check if it's a skip or production brief
            try:
                import json
                brief_dict = json.loads(brief_json)
                deployment = brief_dict.get("deployment_decision", "UNKNOWN")
                
                if deployment == "DO_NOT_DEPLOY":
                    # Show skip message
                    with st.expander(f"❌ {persona_data['icon']} {persona_name} - SKIPPED", expanded=False):
                        st.warning(f"**Not viable for this segment**")
                        st.markdown(f"**Reason:** {brief_dict.get('skip_reason', 'Fit score too low')}")
                        st.markdown(f"**Alternative Needed:** {brief_dict.get('alternative_needed', 'Create segment-specific creative')}")
                        st.code(brief_json, language="json")
                else:
                    # Show production brief with V8 indicators
                    fit_score = brief_dict.get("fit_score", 0)
                    has_hard_constraints = "hard_constraints" in brief_dict.get("production_brief", {})
                    has_lock_fields = "lock_all_non_text_layers" in brief_dict.get("production_brief", {}).get("layout_locks", {})
                    
                    v8_badge = "🔒 V8" if (has_hard_constraints or has_lock_fields) else "V7"
                    
                    with st.expander(f"✅ {persona_data['icon']} {persona_name} - Production Brief {v8_badge} (Score: {fit_score})", expanded=True):
                        st.success(f"**Deployment:** {deployment}")
                        
                        # V8 verification
                        if has_hard_constraints or has_lock_fields:
                            st.info("🔒 **V8 Hard Locks Active:** Layout immutability enforced")
                        
                        # Show key elements
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Production Brief Text:**")
                            prod_brief = brief_dict.get("production_brief", {})
                            text_section = prod_brief.get("text", {})
                            if text_section:
                                st.markdown(f"- **Headline:** {text_section.get('headline', 'N/A')}")
                                st.markdown(f"- **CTA:** {text_section.get('cta', 'N/A')}")
                                st.markdown(f"- **Price:** {text_section.get('price_flash_text', 'N/A')}")
                        
                        with col2:
                            st.markdown("**V8 Layout Locks:**")
                            layout_locks = prod_brief.get("layout_locks", {})
                            if layout_locks:
                                st.markdown(f"- Lock non-text layers: {layout_locks.get('lock_all_non_text_layers', 'N/A')}")
                                st.markdown(f"- Text edit mode: {layout_locks.get('text_edit_mode', 'N/A')}")
                        
                        st.markdown("**Full Production Brief (JSON):**")
                        st.code(brief_json, language="json")
                        
                        st.download_button(
                            f"📥 Download {persona_name} Production Brief (V8)",
                            brief_json,
                            file_name=f"production_brief_v8_{persona_name.replace(' ', '_').lower()}.json",
                            mime="application/json",
                            key=f"download_prod_{persona_name}"
                        )
            except:
                # Fallback if JSON parsing fails
                with st.expander(f"{persona_data['icon']} {persona_name} - Production Brief", expanded=True):
                    st.code(brief_json, language="json")
                    st.download_button(
                        f"📥 Download {persona_name} Production Brief",
                        brief_json,
                        file_name=f"production_brief_{persona_name.replace(' ', '_').lower()}.json",
                        mime="application/json",
                        key=f"download_prod_{persona_name}"
                    )

# ==========================================
# MODULE 5: BRIEF HISTORY & LOG
# ==========================================
st.markdown("---")
with st.expander("📚 Brief History & Log (Module 5)", expanded=False):
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
    st.session_state.production_briefs = None
    st.rerun()

# Example questions
st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 Quick Tips")
st.sidebar.markdown("""
**Module 1:** Chat with personas
**Module 2:** Single persona test  
**Module 3:** Generate 3 briefs
**Module 4:** Production brief (V8)
**Module 5:** View history
""")

# Footer
st.markdown("---")
st.caption("🎯 **Joyful Bites Marketing System V8** | Powered by Claude Sonnet 4 | Project Resonance POC")
