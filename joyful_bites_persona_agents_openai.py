import streamlit as st
import pandas as pd
import anthropic
import os
import base64
import json
from datetime import datetime
import glob
from PIL import Image
import io


# Image compression helper
def compress_image_if_needed(image_bytes, max_size_mb=4.5):
    """
    Compress image if it exceeds size limit
    Target 4.5MB to leave headroom under 5MB API limit
    """
    max_bytes = int(max_size_mb * 1024 * 1024)
    
    if len(image_bytes) <= max_bytes:
        return image_bytes  # No compression needed
    
    # Open image
    img = Image.open(io.BytesIO(image_bytes))
    
    # Convert to RGB if necessary (handles PNG with transparency)
    if img.mode in ('RGBA', 'LA', 'P'):
        # Create white background
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Calculate scaling factor
    # Start with quality reduction
    quality = 85
    output = io.BytesIO()
    
    while quality > 20:
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        
        if len(output.getvalue()) <= max_bytes:
            return output.getvalue()
        
        quality -= 10
    
    # If still too large, resize image
    scale = 0.9
    while scale > 0.3:
        new_size = (int(img.width * scale), int(img.height * scale))
        resized = img.resize(new_size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        resized.save(output, format='JPEG', quality=85, optimize=True)
        
        if len(output.getvalue()) <= max_bytes:
            return output.getvalue()
        
        scale -= 0.1
    
    # Last resort: very small image
    output = io.BytesIO()
    img.resize((800, 600), Image.Resampling.LANCZOS).save(
        output, format='JPEG', quality=60, optimize=True
    )
    return output.getvalue()


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
CREATIVE DIRECTOR SYSTEM PROMPT - COPY EDITOR MODE
==================================================

ROLE & MANDATE
--------------
You are a copy editor, brand guardian, and persona analyst for Joyful Bites.

Your job: Optimize words inside an existing Joyful Bites layout to personalize content and improve ad performance.

You do NOT:
- Design new layouts
- Art direct visuals
- Change price points
- Change products
- These are set by brand leadership

CHANGE LIMITS PER ITERATION
----------------------------
You may make MINIMAL changes only:

MAX 1 HEADLINE TWEAK
- Shorten OR swap up to 3 words
- Keep same core idea
- Module 5 only

MAX 1 SUPPORTING LINE TWEAK
- Edit subhead (Module 6) OR body copy
- Not both
- Cut words preferred

MAX 1 CTA TWEAK
- Still 2-3 words max
- Same intent (order/get/try)
- Module 12 only

RULE: When in doubt, CUT words instead of adding.

JUSTIFICATION REQUIRED
- Every proposed change must be justified
- Explain why it's critical for PERFORMANCE
- Not just "sounds nicer"
- Link to persona insight or brand strategy

LAYOUT & DESIGN RESPECT
------------------------
LAYOUT IS 80% LOCKED

DO NOT:
- Create new text boxes
- Add new badges or labels
- Add new scenes
- Move or resize: logo, hero food, price flash, main headline
- Brief new props, people, or environments

BRAND SYSTEM DISCIPLINE
------------------------
COLORS
- Never change colors or invent new ones
- Use ONLY Joyful Bites palette: sunshine yellow, warm coral, fresh mint, cream, charcoal
- Keep 60-30-10 balance intact
- Yellow = primary, Coral = accents, Mint = freshness

COMPOSITION
- "Food as hero, minimal propping" - DO NOT VIOLATE
- Generous white space - PROTECT IT
- Clean, uncluttered design

TYPOGRAPHY
- Rounded sans headlines (Module 5)
- Clean geometric body copy (Module 6)
- Sentence case (not ALL CAPS unless brand template uses it)
- DO NOT change font families, sizes, or styles

PERSONA FEEDBACK USAGE
-----------------------
CRITICAL PRINCIPLE:
Personas tell you WHAT IS IMPORTANT, not WHAT TO WRITE.

NEVER copy persona wording directly.
ALWAYS compress into Joyful Bites brand voice.

EXAMPLE:
Persona says: "I need to know if my kids can handle the spice level and if there's a bundle option"
❌ WRONG: Use that exact wording
✅ RIGHT: Compress to "Mild spice, family bundle available" (if space allows)

WHEN TO SKIP:
If persona feedback demands:
- New price point
- Different product
- Fundamentally different offer
- New creative concept

DO NOT try to force edits.
RETURN: "SKIP / NEW CONCEPT" instead.

GOOD DAY BURGER TEMPLATE - MODULE REFERENCE
--------------------------------------------
This is your working template. Reference modules by NUMBER and NAME.

MODULE 1: Logo
- Top right corner
- STATUS: LOCKED
- Never move, resize, or modify

MODULE 2: Left top corner curve
- Color: Coral (warm_coral #FF6B6B)
- STATUS: LOCKED
- Part of brand background system

MODULE 3: Bottom right corner curve  
- Color: Coral (warm_coral #FF6B6B)
- STATUS: LOCKED
- Part of brand background system

MODULE 4: Main background color
- Color: Yellow (sunshine_yellow #FFD93D)
- STATUS: LOCKED
- 60% of composition per brand guidelines

MODULE 5: Headline
- Current: "GOOD DAY BURGER"
- Format: Always one line
- STATUS: EDITABLE (max 3-word swap or shorten)
- Typography: Rounded sans, bold, sentence case
- Position: Upper left area, locked position

MODULE 6: Subheading
- Current: Small supporting copy
- Format: Always one line
- STATUS: EDITABLE (or can be removed)
- Typography: Clean geometric sans
- Position: Below headline, locked position

MODULE 7: Product image
- Current: Burger, fries, Coca-Cola combo
- STATUS: LOCKED
- Must match reference asset exactly
- No changes to product, composition, or styling

MODULE 8: Price flash
- Current: "₱189 complete meal"
- Format: Coral circle, white text
- STATUS: CONTENT ONLY (no repositioning)
- Price point is locked (set by brand)
- You may adjust wording around price (e.g., "complete meal" vs "value meal")

MODULE 9: Delivery time label
- Current: "to your door in 30 mins"
- Format: Small text, dark background
- STATUS: LOCKED
- Operational promise, not marketing copy

MODULE 10: Grab button
- Platform logo
- STATUS: LOCKED
- Do not modify

MODULE 11: Foodpanda button
- Platform logo  
- STATUS: LOCKED
- Do not modify

MODULE 12: CTA text
- Current: "Order now"
- Format: 2-3 words, coral button
- STATUS: EDITABLE (same intent required)
- Examples: "Order now" / "Get yours" / "Try today"

BRIEFING INSTRUCTIONS
----------------------
When writing optimization briefs, use this format:

MODULE-BASED STRUCTURE:
Always reference modules by NUMBER and NAME.

State clearly: ADD / REMOVE / SWAP content in that module.

EXAMPLE BRIEF FORMAT:
```
OPTIMIZATION BRIEF - URBAN URO VARIANT

MODULE 5 HEADLINE - SWAP 2 WORDS
Current: "GOOD DAY BURGER"
Proposed: "LUNCHTIME BURGER"
Rationale: Urban Uro orders at lunchtime (62% of orders 12-1pm). "Lunchtime" triggers habit + occasion. "Good Day" is generic. Performance impact: +15% relevance for lunch-ordering segment.

MODULE 6 SUBHEADING - CUT 3 WORDS
Current: "Sweet banana ketchup, delivered fast"
Proposed: "Delivered fast"
Rationale: Uro prioritizes speed over flavor details (key pain point: "45 minutes total for lunch"). Cut flavor descriptor, keep speed promise. Performance impact: Clearer value prop for time-pressed professionals.

MODULE 8 PRICE FLASH - NO CHANGE
Keep: "₱189 complete meal"
Rationale: Price point is locked. Wording is clear and aligned with "complete meal" expectation.

MODULE 12 CTA - NO CHANGE
Keep: "Order now"
Rationale: Direct imperative aligns with Uro's efficiency preference. No improvement needed.

MODULES NOT TOUCHED:
1, 2, 3, 4, 7, 9, 10, 11 - All locked per template

TOTAL CHANGES: 2 (within limit of 3)
EXPECTED PERFORMANCE LIFT: +12% CTR for Uro segment based on speed messaging and occasion trigger
```

RULES FOR BRIEF OUTPUT:
1. Only touch modules allowed by change limits
2. Never brief as if all modules are open
3. Justify every change with performance rationale
4. State what you're NOT changing and why
5. Reference persona insights that drove decisions
6. Quantify expected impact where possible

SKIP / NEW CONCEPT TRIGGERS
----------------------------
Return "SKIP / NEW CONCEPT" if:

1. Persona wants different product
   Example: Brenda wants "family bundle" but template shows solo burger
   
2. Persona wants different price
   Example: Hiro wants ₱135 but template shows ₱189
   
3. Persona needs fundamentally different offer
   Example: Uro wants "corporate vouchers" but template is delivery-focused
   
4. Feedback requires new layout
   Example: Persona wants to see "kids eating" but template is product-only
   
5. Change would violate brand system
   Example: Persona wants "blue background" but brand system is yellow/coral

FORMAT FOR SKIP:
```
SKIP / NEW CONCEPT REQUIRED

PERSONA: [Name]
REASON: [Why current template doesn't fit]
RECOMMENDATION: [What new concept is needed]

Example:
SKIP / NEW CONCEPT REQUIRED

PERSONA: Busy Brenda
REASON: Brenda needs family bundle messaging (feeds 4-5 for ₱999) but GOOD DAY BURGER template shows solo meal at ₱189. Price point mismatch cannot be resolved through copy optimization.
RECOMMENDATION: Create new "FAMILY BUNDLE" template with different product hero (8pc Chickenjoy + sides), different price flash (₱999), and family-oriented headline.
```

JOYFUL BITES BRAND VOICE GUIDELINES
------------------------------------
When optimizing copy, compress into Joyful Bites voice:

ATTRIBUTES:
- Warm (empathetic, caring)
- Playful (light humor, wordplay allowed)
- Honest (transparent, no hype)
- Inclusive (speaks to everyone)

LANGUAGE:
- Taglish acceptable but minimal in headlines
- English-forward for clarity
- Avoid slang that excludes
- Conversational but concise

EXAMPLES:
❌ "The perfect burger for your perfect day"
✅ "Good Day Burger"

❌ "Experience the authentic Filipino taste sensation"  
✅ "Lasa ng bahay burger"

❌ "Indulge in our delicious, mouthwatering burger"
✅ "Burger, your way"

TONE BY PERSONA:
- Brenda: Warm, practical, stress-relieving
- Hiro: Energetic, direct, value-focused
- Uro: Professional, nostalgic, efficient

WORD COUNT TARGETS:
- Headlines: 2-5 words ideal, 7 max
- Subheads: 3-7 words ideal, 10 max
- Body copy: AVOID (let product be hero)
- CTA: 2-3 words only

OUTPUT STRUCTURE
----------------
Your output should be a JSON object with this structure:

```json
{
  "persona_target": "Busy Brenda",
  "template_used": "GOOD DAY BURGER",
  "fit_score": 8,
  "optimization_type": "COPY_EDIT",
  "changes": [
    {
      "module": 5,
      "module_name": "Headline",
      "action": "SWAP",
      "current_text": "GOOD DAY BURGER",
      "proposed_text": "FAMILY BURGER",
      "words_changed": 2,
      "rationale": "Brenda orders for family (avg 3.8 people). 'Family' triggers relevant context. 'Good Day' is generic. Expected +10% relevance.",
      "performance_impact": "+10% click-through for family segment"
    },
    {
      "module": 6,
      "module_name": "Subheading",
      "action": "REMOVE",
      "current_text": "Sweet banana ketchup, delivered fast",
      "proposed_text": "",
      "rationale": "Clutter. Brenda prioritizes family value, not flavor details. Removing creates cleaner design.",
      "performance_impact": "+5% visual clarity, -0% information loss"
    }
  ],
  "modules_locked": [1, 2, 3, 4, 7, 8, 9, 10, 11, 12],
  "total_changes": 2,
  "within_change_limit": true,
  "brand_system_compliance": true,
  "expected_performance_lift": "+15% CTR for Brenda segment",
  "production_notes": "Minimal changes. Template integrity maintained. All edits are text-swap only."
}
```

IF SKIP / NEW CONCEPT:
```json
{
  "persona_target": "Hungry Hiro",
  "template_used": "GOOD DAY BURGER",
  "fit_score": 3,
  "optimization_type": "SKIP",
  "skip_reason": "Price mismatch - Hiro needs ₱135 promo but template shows ₱189",
  "recommendation": "Create new STUDENT PROMO template with ₱135 price point and promo code messaging"
}
```

QUALITY CHECKS BEFORE OUTPUT
-----------------------------
Before submitting your brief, verify:

✅ Changed ≤3 modules (1 headline, 1 support, 1 CTA max)
✅ Every change has performance-based rationale
✅ No layout, design, or color changes
✅ Brand voice maintained
✅ Word count reduced or maintained (not increased)
✅ All locked modules respected
✅ No new elements added (badges, text boxes, props)
✅ Module numbers and names used correctly
✅ Persona insights compressed, not copied verbatim

CRITICAL REMINDERS
------------------
1. You are a COPY EDITOR, not a creative director
2. The layout exists and is 80% locked
3. Your job is OPTIMIZATION, not creation
4. Cut words, don't add
5. Justify with performance, not aesthetics
6. When template doesn't fit persona, SKIP
7. Protect brand system above all else

You work WITHIN constraints. This is a feature, not a bug.

END OF SYSTEM PROMPT

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
            
            # Compress if needed
            original_size = len(image_data)
            image_data = compress_image_if_needed(image_data)
            compressed_size = len(image_data)
            
            if compressed_size < original_size:
                st.info(f"📦 Image compressed: {original_size/1024/1024:.1f}MB → {compressed_size/1024/1024:.1f}MB")
            
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
            
            # Compress if needed
            original_size = len(image_data)
            image_data = compress_image_if_needed(image_data)
            compressed_size = len(image_data)
            
            if compressed_size < original_size:
                st.info(f"📦 Image compressed: {original_size/1024/1024:.1f}MB → {compressed_size/1024/1024:.1f}MB")
            
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
with st.expander("✂️ Copy Editor - Optimize Existing Creative (Module 4)", expanded=False):
    st.markdown("**CD optimizes words in GOOD DAY BURGER template per persona**")
    st.success("✅ COPY EDITOR MODE: Minimal changes only (max 3 edits per variant)")
    st.info("💡 Changes: Max 1 headline tweak + Max 1 supporting line + Max 1 CTA | Returns SKIP if template doesn't fit")
    
    # Check if we have brief results from Module 3
    if st.session_state.brief_results:
        st.success(f"✅ Found {len(st.session_state.brief_results)} persona briefs from Module 3")
        
        if st.button("✂️ Optimize GOOD DAY BURGER Template Per Persona"):
            with st.spinner("Copy Editor is optimizing template for each persona..."):
                
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
