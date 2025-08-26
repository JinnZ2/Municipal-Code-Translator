# Municipal Code Translator

**Making Local Government Understandable**

Stop getting lost in bureaucratic maze language. This tool translates zoning laws, building codes, and municipal ordinances into plain English so you can actually understand what you can do with your property.

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Municipal Codes](https://img.shields.io/badge/municipal-codes-supported-brightgreen.svg)

## 🏛️ Why This Matters

Ever tried to figure out if you can:

- Build a deck or add a room?
- Start a business from home?
- Put up a fence or shed?
- Rent out part of your house?

Municipal codes are deliberately written to confuse regular people. **That stops now.**

This tool:

- ✅ Translates bureaucratic jargon into human language
- 🏠 Tells you what you CAN do on your property
- ❌ Warns about restrictions and prohibitions
- 📋 Lists exactly which permits you need
- 💰 Shows fees and costs upfront
- 📞 Gives you contact info for the right departments
- ⏰ Explains deadlines and processing times
- 🎯 Provides clear next steps

## 🚀 Real-World Examples

**Before:** “Conditional use permits for accessory structures exceeding height limitations in R-1 zoning districts require administrative review pursuant to Section 17.64.040…”

**After:** “🏠 Want to build something taller than normal in a residential area? You need special permission. Fill out form XYZ, wait 30 days, neighbors get notified. Fee: $350.”

**Before:** “Home occupations shall not generate vehicular traffic in excess of normal residential patterns…”

**After:** “✅ You can run a business from home / ❌ Can’t have lots of customers driving to your house / 📋 Need home occupation permit ($150) / 📞 Call Planning Dept: (555) 123-4567”

## ⚡ Quick Start

```bash
# Install
git clone https://github.com/yourusername/municipal-code-translator.git
cd municipal-code-translator
pip install -r requirements.txt

# Translate a municipal document
python municipal_translator.py --file zoning-ordinance.pdf

# Scrape your city's website
python municipal_translator.py --url "https://yourcity.gov/zoning-code"

# Get a beautiful report
open municipal_translations/your_city_zoning.html
```

## 🏠 Perfect For

### Homeowners

- **Building projects**: Decks, additions, fences, sheds
- **Property improvements**: Understanding setbacks and height limits
- **ADU/granny flats**: Accessory dwelling unit regulations
- **Home businesses**: What you can legally do from home

### Small Business Owners

- **Licensing requirements**: What permits do I actually need?
- **Zoning compliance**: Can I operate here legally?
- **Signage rules**: What signs are allowed?
- **Parking requirements**: How many spaces do I need?

### Renters & Tenants

- **Housing rights**: What are landlords required to provide?
- **Rental regulations**: Rent control and tenant protections
- **Property maintenance**: Who’s responsible for what?

### Contractors & Developers

- **Permit requirements**: Building, electrical, plumbing permits
- **Code compliance**: Meeting safety and zoning standards
- **Inspection processes**: When and what gets inspected

## 📋 Supported Document Types

- **Zoning ordinances** (residential, commercial, industrial zones)
- **Building codes** (construction, safety, accessibility)
- **Business licensing** (permits, home occupations, signage)
- **Housing regulations** (rental, tenant rights, property maintenance)
- **Development standards** (parking, landscaping, design review)

## 🛠 Installation

```bash
git clone https://github.com/yourusername/municipal-code-translator.git
cd municipal-code-translator
pip install -r requirements.txt
```

**Requirements:**

- Python 3.7+
- BeautifulSoup4 (web scraping)
- Requests (API calls)
- Pandas (data processing)
- PyPDF2/PyMuPDF (PDF processing)

## 📖 Usage Examples

### Command Line

```bash
# Process a local PDF file
python municipal_translator.py --file "city-zoning-code.pdf" --output "my-zoning-explained"

# Scrape city website
python municipal_translator.py --url "https://cityname.gov/municipal-code" --municipality "Your City"

# Process text directly
python municipal_translator.py --text "Your municipal code text here"
```

### Python API

```python
from municipal_translator import MunicipalCodeTranslator

translator = MunicipalCodeTranslator()
result = translator.translate_municipal_code(your_code_text, municipality="Your City")

print(f"What you can do: {result.what_you_can_do}")
print(f"Permits needed: {result.permits_required}")
print(f"Fees: {result.fees}")
print(f"Next steps: {result.next_steps}")
```

## 🏛️ How It Works

### 1. **Smart Detection**

- Automatically identifies document type (zoning, building, business)
- Recognizes your municipality from URLs or document text
- Detects specific zoning designations (R-1, C-2, M-1, etc.)

### 2. **Jargon Translation**

- **500+ municipal terms** translated into plain English
- Context-aware replacements preserve meaning
- Keeps original terms in parentheses for reference

### 3. **Information Extraction**

- **Permitted uses**: What you’re allowed to do
- **Restrictions**: Size limits, setbacks, height restrictions
- **Permit requirements**: Building permits, conditional use permits, variances
- **Fees**: Application fees, inspection costs, impact fees
- **Timelines**: Processing times, expiration dates, renewal requirements
- **Contacts**: Phone numbers, email addresses, department names

### 4. **Actionable Output**

- Clear next steps for your specific situation
- Warning flags for complex requirements
- Contact information for follow-up questions

## 🎯 Example Translations

### Zoning Code

**Input:** “R-1 Single Family Residential district permits single family dwellings and accessory structures not exceeding 15 feet in height with required setbacks of 25 feet front, 10 feet side, and 20 feet rear.”

**Output:**

- ✅ **What you can do**: Build a single family house and small buildings (garage, shed)
- ❌ **Restrictions**: Extra buildings can’t be taller than 15 feet
- 📐 **Setbacks required**: 25 feet from street, 10 feet from side property lines, 20 feet from back
- 🏠 **Zone type**: R-1 (Single family homes only)

### Building Permit

**Input:** “Building permits required for all structures over 200 square feet or exceeding 10 feet in height. Processing time 14-21 business days. Fee schedule available at Planning Department.”

**Output:**

- 📋 **Permit needed**: Building permit for structures over 200 sq ft or 10 feet tall
- ⏰ **Processing time**: 2-3 weeks
- 💰 **Where to find fees**: Planning Department
- ✅ **No permit needed**: Small sheds under 200 sq ft and under 10 feet

## 🤝 Contributing

**Help make municipal codes understandable for everyone!**

### Add Municipal Terms

Know confusing municipal jargon? Add translations to improve the dictionary:

```python
# In municipal_translator.py, add to municipal_jargon:
'your_confusing_term': 'plain English explanation',
```

### Add Your City’s Patterns

Different cities use different language patterns. Help us recognize more:

```python
# Add to code_patterns for better detection:
'your_city_specific_phrase': 'what_it_means',
```

### Test Real Documents

The best way to improve this tool:

1. Try it on your city’s actual codes
1. Report what works well and what needs improvement
1. Share anonymized examples of confusing language

## 📊 Supported Cities

Currently optimized for common municipal code patterns across:

- **California** cities (strong zoning focus)
- **Texas** municipalities (business-friendly regulations)
- **Florida** counties (growth management)
- **General patterns** that work across most US cities

**Adding your city:** If your municipality uses unique terminology, contribute translations and we’ll add support!

## 🚨 Important Disclaimers

**This tool provides information, not legal advice.** Always:

- ✅ Verify information with your local planning/building department
- ✅ Get professional help for complex projects
- ✅ Check for recent code changes
- ✅ Confirm interpretation before making major decisions

**Privacy:** This tool runs locally. Your documents never leave your computer.

**Accuracy:** We aim for high accuracy but municipal codes are complex. Check the confidence score in each report and verify important details.

## 📄 License

MIT License - Use it, modify it, share it. Let’s democratize local government together.

## 🙏 Acknowledgments

Built for everyone who’s ever been frustrated by incomprehensible municipal websites and 47-page zoning ordinances written in legal gibberish.

**Special thanks to:**

- Planning department staff who actually try to help people navigate the system
- Small business owners fighting through licensing maze
- Homeowners just trying to improve their properties
- Anyone who believes local government should be accessible to the people it serves

-----

## 🐛 Found Issues?

**Tell us:**

- What city/document you were processing
- What went wrong vs. what you expected
- The confidence score the tool reported

## 💡 Feature Requests

**Especially want to hear from:**

- Planning department staff
- Building contractors
- Small business owners
- Real estate professionals
- Housing advocates
- Anyone dealing with municipal bureaucracy

**Together, we can make local government understandable for everyone.**

-----

*“The best way to make government work for people is to help people understand how government works.”*
