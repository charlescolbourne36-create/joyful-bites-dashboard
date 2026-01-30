# JOYFUL BITES CUSTOMER DASHBOARD
## Project Resonance - Module 1: Data Visualization

A professional Streamlit dashboard for exploring customer segments and behavioral patterns across the Joyful Bites customer base.

---

## 📋 WHAT'S INCLUDED

### Dashboard Features
- **Overview Page**: Top-level KPIs, segment distribution, revenue contribution
- **Segment Comparison**: Side-by-side performance metrics across all personas
- **Persona Deep Dives**: Detailed analysis for each of the 3 customer segments
- **Behavioral Insights**: Correlation analysis, patterns, and key findings

### The Three Personas
1. **👨‍👩‍👧‍👦 Busy Brenda** - The Family Nurturer (34% of customers)
2. **🎓 Hungry Hiro** - The Value-Seeking Student/Gen Z (40% of customers)
3. **💼 Urban Uro** - The Nostalgic Professional (26% of customers)

---

## 🚀 QUICK START

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Ensure data file is present**
Make sure `joyful_bites_customers_5000.csv` is in the same directory as `joyful_bites_dashboard.py`

3. **Run the dashboard**
```bash
streamlit run joyful_bites_dashboard.py
```

4. **Access the dashboard**
The dashboard will automatically open in your browser at `http://localhost:8501`

---

## 📁 FILE STRUCTURE

```
project_folder/
│
├── joyful_bites_dashboard.py          # Main dashboard application
├── joyful_bites_customers_5000.csv    # Customer dataset (5,399 records)
├── requirements.txt                    # Python dependencies
├── generate_joyful_bites_dataset.py   # Dataset generator script
└── joyful_bites_data_dictionary.txt   # Data documentation
```

---

## 📊 DASHBOARD SECTIONS

### 1. Overview (📊)
**What it shows:**
- Total customers, revenue, orders, and average LTV
- Segment distribution (pie chart)
- Revenue contribution by segment (bar chart)

**Use case:** Executive-level snapshot of customer base

---

### 2. Segment Comparison (📈)
**What it shows:**
- Average order value by segment
- Visit frequency comparison
- Customer lifetime value
- Average party size
- Detailed metrics table

**Use case:** Compare performance across all three personas

---

### 3. Busy Brenda Deep Dive (👨‍👩‍👧‍👦)
**What it shows:**
- Key metrics (customers, AOV, frequency, LTV, party size)
- Preferred order channels
- Primary order times
- Payment method preferences
- Engagement metrics (promos, loyalty)
- Popular menu items
- Demographics (age, city, occupation)

**Use case:** Understand family-focused customer behavior

---

### 4. Hungry Hiro Deep Dive (🎓)
**What it shows:**
- Same detailed analysis as Brenda, tailored to Gen Z/student segment
- Emphasis on promo usage and digital payment preferences
- Solo meal ordering patterns

**Use case:** Understand budget-conscious youth behavior

---

### 5. Urban Uro Deep Dive (💼)
**What it shows:**
- Same detailed analysis as other personas
- Emphasis on delivery preferences and weekday patterns
- Professional dining habits

**Use case:** Understand convenience-focused professional behavior

---

### 6. Behavioral Insights (🔍)
**What it shows:**
- Order value distribution (box plots)
- Visit frequency vs. Lifetime Value (scatter with trendline)
- Tenure vs. Total Spent correlation
- Key insights for each segment

**Use case:** Identify patterns and correlations for strategic planning

---

## 🎨 DESIGN FEATURES

### Professional Styling
- Clean, modern interface with Joyful Bites brand colors
- Consistent color coding across segments:
  - Busy Brenda: Red (#E57373)
  - Hungry Hiro: Blue (#64B5F6)
  - Urban Uro: Green (#81C784)

### Interactive Elements
- Hover tooltips on all charts
- Responsive layout for different screen sizes
- Sidebar navigation for easy access

### Data Visualization
- Plotly charts for professional, interactive visualizations
- Multiple chart types: pie, bar, box plots, scatter plots
- Formatted currency (PHP) and numbers with thousands separators

---

## 💡 USAGE TIPS

### For Demos
1. Start with **Overview** page to set context
2. Move to **Segment Comparison** to show differentiation
3. Deep dive into one persona (suggest Busy Brenda for family appeal)
4. Show **Behavioral Insights** for strategic story

### For Analysis
- Use Segment Comparison to identify opportunities
- Persona Deep Dives for campaign planning
- Behavioral Insights for predictive modeling

### For Client Presentations
- Overview provides executive summary
- Segment Comparison validates strategic segmentation
- Persona pages demonstrate depth of customer intelligence

---

## 🔧 CUSTOMIZATION

### Updating Data
To refresh with new customer data:
1. Run `generate_joyful_bites_dataset.py` to create new dataset
2. Or replace `joyful_bites_customers_5000.csv` with updated file
3. Dashboard will automatically reload on next view

### Modifying Visualizations
- All charts use Plotly - easy to customize in code
- Color scheme defined in `SEGMENT_COLORS` dictionary
- Add new metrics by updating aggregation functions

### Adding New Sections
1. Create new function (e.g., `create_new_analysis(df)`)
2. Add navigation option in sidebar
3. Add routing in `main()` function

---

## 📈 KEY METRICS EXPLAINED

**Average Order Value (AOV)**
- Total spent divided by number of orders
- Indicates purchasing power per transaction

**Visit Frequency**
- Average orders per month
- Shows engagement and loyalty

**Lifetime Value (LTV)**
- Projected total revenue from customer
- Calculated based on historical spend patterns

**Party Size**
- Average number of people per order
- Distinguishes family vs. solo dining

**Promo Engagement**
- Percentage using promotional offers
- Indicates price sensitivity

**Loyalty Metrics**
- Enrolled: Signed up for program
- Active: Regular program usage

---

## 🐛 TROUBLESHOOTING

### Dashboard won't start
- Check Python version: `python --version` (need 3.8+)
- Verify dependencies: `pip list | grep streamlit`
- Ensure CSV file is in correct location

### Charts not displaying
- Check data file format (CSV with correct columns)
- Verify Plotly installation: `pip install --upgrade plotly`

### Performance issues
- Dataset is optimized for 5K records
- If expanding, consider data sampling for large datasets

---

## 📝 TECHNICAL NOTES

### Data Caching
- `@st.cache_data` decorator speeds up repeat loads
- Clear cache in sidebar if data is updated

### Browser Compatibility
- Tested on Chrome, Firefox, Safari
- Best experience on desktop (responsive design included)

### Export Options
- Charts can be downloaded as PNG (hover over chart → camera icon)
- Data tables can be copied to clipboard

---

## 🎯 NEXT STEPS (Module 2)

After the dashboard, the POC continues with:
- **Module 2**: Queryable Persona Agents (Days 3-5)
- **Module 3**: AI-Assisted Brief Generator (Days 6-8)
- **Module 4**: Creative Testing Interface (Days 9-10)

This dashboard provides the **data foundation** that persona agents will reference in their responses.

---

## 📞 SUPPORT

For issues or questions:
- Check data dictionary: `joyful_bites_data_dictionary.txt`
- Review dataset generator: `generate_joyful_bites_dataset.py`
- Streamlit documentation: https://docs.streamlit.io

---

## ✅ VALIDATION CHECKLIST

Before demo:
- [ ] Dashboard loads without errors
- [ ] All 6 navigation sections accessible
- [ ] Charts display correctly
- [ ] Numbers formatted properly (currency, percentages)
- [ ] Sidebar shows correct totals
- [ ] Color scheme consistent across pages
- [ ] Hover tooltips working
- [ ] Data matches documentation

---

## 🎨 BRAND GUIDELINES

**Color Palette:**
- Primary: #D32F2F (Joyful Bites Red)
- Busy Brenda: #E57373 (Light Red)
- Hungry Hiro: #64B5F6 (Blue)
- Urban Uro: #81C784 (Green)
- Backgrounds: #f8f9fa, #ffffff
- Text: #666666, #000000

**Typography:**
- Headers: Bold, 1.5-2.5rem
- Body: 0.9-1rem
- Metrics: Bold, 2rem

---

**DASHBOARD READY FOR DEPLOYMENT** ✅

Module 1 (Data Foundation) Complete.
Ready to proceed with Module 2 (Persona Agents).
