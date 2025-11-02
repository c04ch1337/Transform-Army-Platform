# Vapi.ai Deployment Guide - Transform Army AI Voice Assistants

**Version**: 1.0.0  
**Last Updated**: 2025-11-01  
**Deployment Time**: ~4-6 hours for all 6 assistants  
**Prerequisites**: Vapi.ai account, backend webhook deployed, ElevenLabs account (optional)

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Vapi.ai Account Setup](#vapiai-account-setup)
3. [ElevenLabs Voice Configuration](#elevenlabs-voice-configuration)
4. [Webhook Configuration](#webhook-configuration)
5. [Importing Assistant Configurations](#importing-assistant-configurations)
6. [Phone Number Provisioning](#phone-number-provisioning)
7. [Testing Each Assistant](#testing-each-assistant)
8. [Environment Variables](#environment-variables)
9. [Troubleshooting Guide](#troubleshooting-guide)
10. [Production Deployment Checklist](#production-deployment-checklist)

---

## Pre-Deployment Checklist

Before deploying any voice assistants, ensure you have:

- [ ] **Vapi.ai Account**: Signed up at [https://dashboard.vapi.ai](https://dashboard.vapi.ai)
- [ ] **Backend Webhook Deployed**: Your adapter service accessible via public URL
- [ ] **ElevenLabs Account** (optional): For premium voices at [https://elevenlabs.io](https://elevenlabs.io)
- [ ] **SSL Certificate**: Webhook URL must use HTTPS
- [ ] **API Keys Secured**: Environment variables configured
- [ ] **Payment Method**: Added to Vapi.ai for usage charges
- [ ] **Test Phone Number**: For testing inbound/outbound calls

**Estimated Costs**:
- Vapi.ai: $49/month (Hobby) or $149/month (Growth)
- ElevenLabs: $0-99/month depending on usage
- Phone numbers: ~$2-5/month per number

---

## Vapi.ai Account Setup

### Step 1: Create Vapi.ai Account

1. Navigate to [https://dashboard.vapi.ai](https://dashboard.vapi.ai)
2. Click **"Sign Up"**
3. Enter email and create password
4. Verify email address
5. Complete profile setup

### Step 2: Choose Subscription Plan

**For Development/Testing**:
- Start with **Hobby Plan** ($49/month)
- Includes 500 minutes of calls
- Perfect for testing all 6 assistants

**For Production**:
- Upgrade to **Growth Plan** ($149/month) or higher
- More included minutes
- Better support options

### Step 3: Get API Credentials

1. Go to **Settings** → **API Keys**
2. Click **"Create New Key"**
3. Name it: `Transform Army AI - Production`
4. **Copy and save** both keys:
   - **Public Key**: Used in frontend (`NEXT_PUBLIC_VAPI_PUBLIC_KEY`)
   - **Private Key**: Used in backend (keep secret!)

**Security Note**: Never commit private keys to git. Store in environment variables only.

### Step 4: Configure Webhook Secret

1. Go to **Settings** → **Webhooks**
2. Click **"Generate Webhook Secret"**
3. **Copy and save** the secret string
4. This will be used to verify webhook authenticity

**Format**: Usually a long random string like `vapi_whsec_abc123def456...`

---

## ElevenLabs Voice Configuration

### Why Use ElevenLabs?

- **Superior Quality**: More natural-sounding voices than default TTS
- **Voice Cloning**: Can create custom voices
- **Emotional Range**: Better at conveying empathy, confidence, authority
- **Professional**: Recommended for production deployments

### Step 1: Create ElevenLabs Account

1. Go to [https://elevenlabs.io](https://elevenlabs.io)
2. Sign up for account (free tier available)
3. Navigate to **Voice Library**

### Step 2: Select Voices for Each Agent

For each Transform Army AI agent, select an appropriate voice:

#### Hunter (BDR - ALPHA-1)
**Voice Type**: Professional male, confident, measured
**Recommended Voices**:
- **Josh** (default, confident professional)
- **Adam** (deep, authoritative)  
- **Antoni** (friendly but professional)

**To Get Voice ID**:
1. Click on voice in Voice Library
2. Copy the **Voice ID** (format: `21m00Tcm4TlvDq8ikWAM`)
3. Replace in [`hunter-bdr.json`](vapi-config/assistants/hunter-bdr.json:34): `REPLACE_WITH_ELEVENLABS_VOICE_ID_PROFESSIONAL_MALE`

#### Medic (Support - ALPHA-2)
**Voice Type**: Empathetic female, calm, reassuring
**Recommended Voices**:
- **Rachel** (warm, empathetic)
- **Bella** (younger, friendly)
- **Elli** (soothing, patient)

**Voice ID Location**: `medic-support.json` line 34

#### Scout (Research - BRAVO-1)
**Voice Type**: Analytical male, methodical
**Recommended Voices**:
- **Sam** (neutral, analytical)
- **Adam** (deep, thoughtful)
- **Callum** (measured, intelligent)

**Voice ID Location**: `scout-research.json` line 34

#### Engineer (Ops - BRAVO-2)
**Voice Type**: Authoritative male, direct
**Recommended Voices**:
- **Josh** (confident, authoritative)
- **Clyde** (strong, commanding)
- **Thomas** (direct, professional)

**Voice ID Location**: `engineer-ops.json` line 34

#### Intel (Knowledge - CHARLIE-1)
**Voice Type**: Clear female, educational
**Recommended Voices**:
- **Charlotte** (clear, teacher-like)
- **Nicole** (articulate, organized)
- **Freya** (professional, knowledgeable)

**Voice ID Location**: `intel-knowledge.json` line 34

#### Guardian (QA - CHARLIE-2)
**Voice Type**: Precise male, professional
**Recommended Voices**:
- **Daniel** (precise, measured)
- **Harry** (methodical, clear)
- **Jeremy** (professional, thorough)

**Voice ID Location**: `guardian-qa.json` line 34

### Step 3: Test Voice Quality

Before deploying, test each voice:

1. In ElevenLabs, click voice
2. Enter sample text from agent's `firstMessage`
3. Click **"Generate"**
4. Listen to quality
5. Adjust **Stability** and **Similarity** settings if needed

**Recommended Settings** (already in configs):
- Stability: 0.7-0.85 (higher = more consistent)
- Similarity Boost: 0.75-0.85 (higher = more like original voice)
- Style: 0.2-0.5 (lower = more neutral, higher = more expressive)

---

## Webhook Configuration

### Step 1: Deploy Backend Webhook

Your adapter service must be publicly accessible with HTTPS.

**Option A: Cloud Deployment** (Recommended for Production)
```bash
# Deploy to Railway, Render, or your cloud provider
# Ensure URL is HTTPS and accessible publicly
# Example: https://transform-army-adapter.railway.app
```

**Option B: ngrok for Development**
```bash
# Install ngrok
npm install -g ngrok

# Start your adapter service
cd apps/adapter
python src/main_simple.py

# In another terminal, start ngrok
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
```

**Option C: Cloudflare Tunnel**
```bash
# Install cloudflared
# Windows: Download from cloudflare.com
# Mac: brew install cloudflare/cloudflare/cloudflared

# Start tunnel
cloudflared tunnel --url http://localhost:8000

# Copy the generated HTTPS URL
```

### Step 2: Update Configuration Files

For each assistant config file, replace the webhook URL:

**Find**: `"serverUrl": "https://YOUR_WEBHOOK_URL_HERE/api/v1/vapi/webhook"`  
**Replace with**: `"serverUrl": "https://YOUR_ACTUAL_URL/api/v1/vapi/webhook"`

**Examples**:
- Production: `https://api.transformarmy.ai/api/v1/vapi/webhook`
- ngrok: `https://abc123.ngrok.io/api/v1/vapi/webhook`
- Railway: `https://transform-army-adapter.railway.app/api/v1/vapi/webhook`

### Step 3: Configure Webhook Secret

1. In your backend `.env` file, set:
   ```bash
   VAPI_WEBHOOK_SECRET=vapi_whsec_YOUR_SECRET_FROM_VAPI_DASHBOARD
   ```

2. In each assistant JSON, replace:
   ```json
   "serverUrlSecret": "YOUR_WEBHOOK_SECRET_HERE"
   ```
   With your actual webhook secret from Vapi.ai dashboard.

### Step 4: Test Webhook Connection

Test that Vapi can reach your webhook:

```bash
# From command line, test webhook is accessible
curl https://YOUR_WEBHOOK_URL/api/v1/vapi/webhook

# Should return 405 Method Not Allowed (POST required)
# If you get connection error, webhook is not reachable
```

**Common Issues**:
- ❌ **Connection Refused**: Firewall blocking, service not running
- ❌ **SSL Error**: Certificate invalid or expired
- ❌ **404 Not Found**: Wrong URL path
- ✅ **405 or 422**: Webhook is reachable (correct!)

---

## Importing Assistant Configurations

### Method 1: Manual Import via Dashboard (Easiest)

For each assistant configuration file:

1. **Open Vapi.ai Dashboard** → **Assistants**
2. Click **"Create Assistant"**
3. In the creation form, click **"Import Configuration"** (if available)
4. **OR** manually enter each field:

#### Basic Information Tab

```
Name: [Copy from JSON "name" field]
Example: "Hunter - BDR Concierge (ALPHA-1)"

First Message: [Copy from JSON "firstMessage"]
End Call Message: [Copy from JSON "endCallMessage"]
Voicemail Message: [Copy from JSON "voicemailMessage"]
```

#### Model Tab

```
Provider: openai
Model: gpt-4
Temperature: [Copy from JSON - varies by agent]
Max Tokens: [Copy from JSON - varies by agent]

System Prompt: [Copy entire systemPrompt from JSON]
```

#### Voice Tab

```
Provider: 11labs
Voice ID: [Your ElevenLabs voice ID]
Stability: [Copy from JSON]
Similarity Boost: [Copy from JSON]
Style: [Copy from JSON]
Use Speaker Boost: true
```

#### Functions Tab

For each function in the JSON `functions` array:

1. Click **"Add Function"**
2. Enter **Name**: Exactly as in JSON
3. Enter **Description**: Copy from JSON
4. Click **"Add Parameter"** for each parameter
5. Configure parameter:
   - Name: From JSON
   - Type: From JSON
   - Description: From JSON
   - Required: Check if in JSON "required" array
   - Default: If specified in JSON

Repeat for all 4 functions per assistant.

#### Server/Webhook Tab

```
Server URL: https://YOUR_WEBHOOK_URL/api/v1/vapi/webhook
Server URL Secret: [Your webhook secret]
```

#### Advanced Settings Tab

```
Recording Enabled: true
Silence Timeout: [Copy from JSON - varies by agent]
Max Duration: [Copy from JSON - varies by agent]
Background Sound: off
Backchanneling: [Copy from JSON - varies by agent]
End Call Phrases: [Add each phrase from JSON array]
```

5. Click **"Save Assistant"**
6. **Copy the Assistant ID** (format: `asst_abc123...`)
7. Save this ID for later use

### Method 2: API Import (Advanced)

Use Vapi's API to programmatically create assistants:

```bash
# Set your Vapi private key
export VAPI_PRIVATE_KEY="your_private_key_here"

# For each assistant config file
curl -X POST https://api.vapi.ai/assistant \
  -H "Authorization: Bearer $VAPI_PRIVATE_KEY" \
  -H "Content-Type: application/json" \
  -d @vapi-config/assistants/hunter-bdr.json
```

**Note**: You'll still need to replace placeholders in JSON files first.

---

## Phone Number Provisioning

### Step 1: Purchase Phone Numbers

1. Go to **Phone Numbers** in Vapi dashboard
2. Click **"Buy Phone Number"**
3. **Select Country**: United States (or your region)
4. **Select Area Code**: Choose desired area code
5. **Number Type**: 
   - **Local**: Best for specific regions ($2/month)
   - **Toll-Free**: Professional, works nationwide ($5/month)

### Step 2: Assign Numbers to Assistants

**Recommended Assignment**:

```
📞 Hunter (BDR): (XXX) XXX-XXXX - Sales Inquiry Line
📞 Medic (Support): (XXX) XXX-XXXX - Customer Support Hotline
📞 Scout (Research): (XXX) XXX-XXXX - Intelligence Hotline (internal)
📞 Engineer (Ops): (XXX) XXX-XXXX - Operations Alert Line (internal)
📞 Intel (Knowledge): (XXX) XXX-XXXX - Documentation Hotline (internal)
📞 Guardian (QA): (XXX) XXX-XXXX - Quality Hotline (internal)
```

**Public-Facing** (publish on website):
- Hunter: Main sales/inquiry number
- Medic: Customer support number

**Internal Only** (for team use):
- Scout, Engineer, Intel, Guardian

### Step 3: Configure Number Settings

For each phone number:

1. Click on the number
2. **Assign to Assistant**: Select the appropriate assistant
3. **Inbound Configuration**:
   - Enable: ON
   - Max concurrent calls: 5 (adjust based on plan)
4. **Outbound Configuration** (if needed):
   - Enable: ON for assistants that make outbound calls
5. Click **"Save"**

---

## Importing Assistant Configurations

### Hunter - BDR Concierge (ALPHA-1)

**Configuration File**: [`vapi-config/assistants/hunter-bdr.json`](vapi-config/assistants/hunter-bdr.json:1)

**Before Importing**:

1. **Replace Voice ID** (line 34):
   ```json
   "voiceId": "YOUR_ELEVENLABS_VOICE_ID_HERE"
   ```
   With actual ElevenLabs voice ID (e.g., `21m00Tcm4TlvDq8ikWAM`)

2. **Replace Webhook URL** (line 123):
   ```json
   "serverUrl": "https://YOUR_ACTUAL_WEBHOOK_URL/api/v1/vapi/webhook"
   ```

3. **Replace Webhook Secret** (line 124):
   ```json
   "serverUrlSecret": "YOUR_WEBHOOK_SECRET_FROM_VAPI"
   ```

**Import Steps**:

1. Log into Vapi.ai Dashboard
2. Navigate to **Assistants** → **Create Assistant**
3. **Name**: `Hunter - BDR Concierge (ALPHA-1)`
4. **Model Configuration**:
   - Provider: `openai`
   - Model: `gpt-4`
   - Temperature: `0.3`
   - Max Tokens: `500`
5. **Copy System Prompt**: From JSON `systemPrompt` field (entire text)
6. **Voice Configuration**:
   - Provider: `11labs`
   - Voice ID: Your ElevenLabs voice ID
   - Stability: `0.7`
   - Similarity Boost: `0.8`
   - Style: `0.5`
   - Speaker Boost: `ON`
7. **Messages**:
   - First Message: Copy from JSON
   - End Call Message: Copy from JSON
   - Voicemail: Copy from JSON
8. **Functions** (Add all 4):
   
   **Function 1: search_crm_contact**
   - Name: `search_crm_contact`
   - Description: `Search for existing contact in CRM by email or company to prevent duplicates and retrieve contact history`
   - Parameters:
     - `email` (string, required): Email address to search for in CRM
     - `query` (string, optional): Optional additional search query

   **Function 2: create_crm_contact**
   - Name: `create_crm_contact`
   - Description: `Create new contact in CRM with lead qualification data and BANT scores`
   - Parameters (11 total - see JSON for complete list):
     - `email` (string, required)
     - `first_name` (string, required)
     - `last_name` (string, required)
     - `company` (string, required)
     - `total_score` (number, required)
     - Plus optional: phone, title, budget_score, authority_score, need_score, timeline_score, notes

   **Function 3: check_calendar_availability**
   - Name: `check_calendar_availability`
   - Description: `Check sales team calendar availability for meeting booking`
   - Parameters:
     - `date` (string, required): Preferred date (YYYY-MM-DD)
     - `duration_minutes` (number, optional, default 30)
     - `timezone` (string, optional)

   **Function 4: book_meeting**
   - Name: `book_meeting`
   - Description: `Book discovery meeting with qualified prospect (use only if BANT score ≥70)`
   - Parameters:
     - `contact_email` (string, required)
     - `start_time` (string, required): ISO 8601 format
     - `duration_minutes` (number, optional, default 30)
     - `title` (string, optional)
     - `attendees` (array of strings, optional)
     - `notes` (string, optional)

9. **Server Settings**:
   - Server URL: Your webhook URL
   - Server URL Secret: Your webhook secret
10. **Advanced Settings**:
    - Recording: `ON`
    - Silence Timeout: `30` seconds
    - Max Duration: `900` seconds (15 minutes)
    - Background Sound: `OFF`
    - Backchanneling: `OFF`
11. **End Call Phrases**: Add each phrase:
    - goodbye
    - that's all for now
    - thank you hunter
    - end call

12. Click **"Create Assistant"**
13. **Save Assistant ID**: Copy the generated ID (needed for frontend)

### Medic - Support Concierge (ALPHA-2)

**Configuration File**: [`vapi-config/assistants/medic-support.json`](vapi-config/assistants/medic-support.json:1)

Follow same import process as Hunter, with these specifics:

**Model Settings**:
- Temperature: `0.2` (more deterministic for support)
- Max Tokens: `600`

**Functions** (4 total):
1. `search_knowledge_base` - Search KB for solutions
2. `create_support_ticket` - Create helpdesk ticket
3. `search_past_tickets` - Find historical tickets
4. `escalate_to_human` - Route to human agent

**Advanced Settings**:
- Silence Timeout: `35` seconds (support calls may have longer pauses)
- Max Duration: `600` seconds (10 minutes)
- Backchanneling: `ON` (show understanding with verbal cues)

### Scout - Research Recon (BRAVO-1)

**Configuration File**: [`vapi-config/assistants/scout-research.json`](vapi-config/assistants/scout-research.json:1)

**Model Settings**:
- Temperature: `0.3`
- Max Tokens: `800` (longer for detailed research)

**Functions** (4 total):
1. `search_company_data` - Company background research
2. `analyze_competitor` - Competitive intelligence
3. `generate_battle_card` - Sales battle cards
4. `search_market_news` - Industry news monitoring

**Advanced Settings**:
- Silence Timeout: `40` seconds (research discussions may have pauses)
- Max Duration: `1200` seconds (20 minutes for detailed discussions)

### Engineer - Ops Sapper (BRAVO-2)

**Configuration File**: [`vapi-config/assistants/engineer-ops.json`](vapi-config/assistants/engineer-ops.json:1)

**Model Settings**:
- Temperature: `0.1` (very deterministic for operational data)
- Max Tokens: `600`

**Functions** (4 total):
1. `check_sla_compliance` - SLA monitoring
2. `analyze_data_quality` - Data quality checks
3. `detect_anomalies` - Anomaly detection
4. `generate_ops_report` - Operational reports

**Advanced Settings**:
- Silence Timeout: `30` seconds (brief operational updates)
- Max Duration: `600` seconds (10 minutes)
- Backchanneling: `OFF` (concise military briefing style)

### Intel - Knowledge Librarian (CHARLIE-1)

**Configuration File**: [`vapi-config/assistants/intel-knowledge.json`](vapi-config/assistants/intel-knowledge.json:1)

**Model Settings**:
- Temperature: `0.3`
- Max Tokens: `700`

**Functions** (4 total):
1. `search_knowledge_content` - KB content search
2. `create_kb_article` - Create documentation
3. `update_kb_article` - Update existing docs
4. `analyze_content_gaps` - Gap analysis

**Advanced Settings**:
- Silence Timeout: `35` seconds
- Max Duration: `900` seconds (15 minutes for doc discussions)
- Backchanneling: `ON` (educational conversations)

### Guardian - QA Auditor (CHARLIE-2)

**Configuration File**: [`vapi-config/assistants/guardian-qa.json`](vapi-config/assistants/guardian-qa.json:1)

**Model Settings**:
- Temperature: `0.1` (very deterministic for QA)
- Max Tokens: `700`

**Functions** (4 total):
1. `evaluate_agent_output` - Quality scoring
2. `check_quality_trends` - Trend analysis
3. `detect_performance_drift` - Drift detection
4. `generate_qa_report` - QA reporting

**Advanced Settings**:
- Silence Timeout: `30` seconds
- Max Duration: `900` seconds (15 minutes)
- Backchanneling: `OFF` (formal audit style)

---

## Testing Each Assistant

### Pre-Test Checklist

- [ ] Assistant created in Vapi.ai
- [ ] Phone number assigned
- [ ] Webhook URL configured and accessible
- [ ] Backend adapter service running
- [ ] All function handlers implemented

### Test Procedure for Each Assistant

#### Hunter (BDR) Test Script

**Call Flow Test**:

1. **Dial** Hunter's assigned phone number
2. **Listen** for greeting: "This is Hunter from Transform Army AI..."
3. **Respond**: "Hi Hunter, I'm interested in your AI platform for my company"
4. **Follow** the BANT qualification questions:
   - Budget question
   - Authority/role question
   - Needs/pain point question
   - Timeline question
5. **Provide qualifying answers** (should trigger meeting booking):
   - Budget: "$75K allocated for AI automation this year"
   - Authority: "I'm the VP of Operations, I make the decision"
   - Need: "We need to automate our customer support and reduce response times"
   - Timeline: "Looking to implement within the next 30 days"
6. **Verify**:
   - Hunter searches CRM (listen for "Let me check if you're already in our system...")
   - Hunter creates contact
   - Hunter checks calendar availability
   - Hunter offers meeting time slots
   - You select a time
   - Hunter books the meeting
   - Confirmation message provided
7. **Check backend**:
   ```bash
   # Check webhook received function calls
   curl http://localhost:8000/api/v1/vapi/calls/logs
   ```
8. **Verify CRM**: New contact created with BANT scores

**Expected Outcome**: 
- ✅ Contact created in CRM
- ✅ BANT scores recorded (≥70)
- ✅ Meeting booked on calendar
- ✅ Confirmation email sent

#### Medic (Support) Test Script

**Call Flow Test**:

1. **Dial** Medic's assigned number
2. **Listen** for greeting: "Hi, this is Medic from Transform Army AI support..."
3. **Describe issue**: "I can't log into my account"
4. **Verify**:
   - Medic classifies priority (should be P2)
   - Medic searches knowledge base
   - Medic provides solution steps
   - Medic asks if solution worked
   - If yes: Creates ticket marked as resolved
   - If no: Escalates to human with context
5. **Test escalation** (second call):
   - Call again with complex issue
   - Verify escalation triggered
   - Check escalation context quality

**Expected Outcome**:
- ✅ KB search performed
- ✅ Solution provided
- ✅ Ticket created with proper classification
- ✅ Escalation works when needed

#### Scout (Research) Test Script

**Call Flow Test**:

1. **Dial** Scout's number
2. **Request**: "I need competitive intelligence on [Competitor Name]"
3. **Verify**:
   - Scout acknowledges request
   - Scout asks clarifying questions (depth, focus areas)
   - Scout initiates research function
   - Scout provides preliminary findings
   - Scout confirms delivery method for full report
4. **Check**:
   - Research function executed
   - Report generated
   - Sources cited

**Expected Outcome**:
- ✅ Research initiated
- ✅ Intelligent questions asked
- ✅ Report delivery confirmed

#### <truncated for brevity>

### Testing Checklist

After testing each assistant, verify:

**Voice Quality**:
- [ ] Voice sounds natural and professional
- [ ] Pace is appropriate (not too fast/slow)
- [ ] Audio quality is clear
- [ ] No robotic artifacts

**Functionality**:
- [ ] All functions execute successfully
- [ ] Function calls logged in backend
- [ ] Returns to conversation after function call
- [ ] Handles function errors gracefully

**Conversation Flow**:
- [ ] Greeting is professional and on-brand
- [ ] Questions are clear and contextual
- [ ] Listens and responds appropriately
- [ ] Provides clear next steps
- [ ] End message confirms actions taken

**Error Handling**:
- [ ] Handles unclear responses
- [ ] Asks clarifying questions when confused
- [ ] Gracefully handles function failures
- [ ] Escalates appropriately when stuck

---

## Environment Variables

### Backend Environment Variables

Add to [`apps/adapter/.env`](apps/adapter/.env:1):

```bash
# Vapi.ai API Configuration
VAPI_PUBLIC_KEY=pk_abc123...
VAPI_PRIVATE_KEY=sk_abc123...
VAPI_WEBHOOK_SECRET=vapi_whsec_abc123...

# Vapi Assistant IDs (after creation)
VAPI_ASSISTANT_HUNTER=asst_hunter_abc123
VAPI_ASSISTANT_MEDIC=asst_medic_def456
VAPI_ASSISTANT_SCOUT=asst_scout_ghi789
VAPI_ASSISTANT_ENGINEER=asst_engineer_jkl012
VAPI_ASSISTANT_INTEL=asst_intel_mno345
VAPI_ASSISTANT_GUARDIAN=asst_guardian_pqr678

# ElevenLabs Configuration (optional)
ELEVENLABS_API_KEY=your_elevenlabs_key_here
```

### Frontend Environment Variables

Add to [`apps/web/.env.local`](apps/web/.env.local:1):

```bash
# Vapi.ai Public Configuration (safe for frontend)
NEXT_PUBLIC_VAPI_PUBLIC_KEY=pk_abc123...
NEXT_PUBLIC_VAPI_ORG_ID=your_org_id_here

# Assistant IDs for frontend call buttons
NEXT_PUBLIC_VAPI_ASSISTANT_HUNTER=asst_hunter_abc123
NEXT_PUBLIC_VAPI_ASSISTANT_MEDIC=asst_medic_def456
NEXT_PUBLIC_VAPI_ASSISTANT_SCOUT=asst_scout_ghi789
NEXT_PUBLIC_VAPI_ASSISTANT_ENGINEER=asst_engineer_jkl012
NEXT_PUBLIC_VAPI_ASSISTANT_INTEL=asst_intel_mno345
NEXT_PUBLIC_VAPI_ASSISTANT_GUARDIAN=asst_guardian_pqr678

# Phone Numbers (for display)
NEXT_PUBLIC_PHONE_HUNTER=+15551234567
NEXT_PUBLIC_PHONE_MEDIC=+15551234568
```

**Security Note**: Only `NEXT_PUBLIC_*` variables are exposed to frontend. Never expose private keys or secrets in frontend environment variables.

---

## Troubleshooting Guide

### Issue: "Webhook signature verification failed"

**Symptoms**: 
- Function calls not executing
- Error in backend logs: "Invalid webhook signature"

**Solutions**:

1. **Verify Secret Matches**:
   ```bash
   # Check your .env file
   cat apps/adapter/.env | grep VAPI_WEBHOOK_SECRET
   
   # Should match the secret in Vapi dashboard exactly
   ```

2. **Check Implementation**:
   - Ensure webhook handler uses same secret
   - Verify HMAC-SHA256 algorithm
   - Check header name: `x-vapi-signature`

3. **Temporary Bypass** (development only):
   ```python
   # In main_simple.py, temporarily comment out verification
   # if x_vapi_signature:
   #     if not verify_vapi_signature(...):
   #         raise HTTPException(401, "Invalid signature")
   
   # WARNING: Remove in production!
   ```

### Issue: "Function not found" or "Function failed"

**Symptoms**:
- Assistant says "I encountered an error"
- Backend logs show 400 or 500 error

**Solutions**:

1. **Check Function Name Spelling**:
   - Must match exactly between Vapi config and backend handler
   - Case-sensitive: `search_crm_contact` ≠ `searchCRMContact`

2. **Verify Function Handler Exists**:
   ```python
   # In main_simple.py, check this function exists:
   async def handle_search_crm_contact(params: Dict[str, Any]) -> Dict[str, Any]:
       # Implementation here
   ```

3. **Check Parameter Names**:
   - Parameter names in JSON must match what handler expects
   - Check required vs optional parameters

4. **Test Function Directly**:
   ```bash
   # Send test webhook payload
   curl -X POST http://localhost:8000/api/v1/vapi/webhook \
     -H "Content-Type: application/json" \
     -d '{
       "message": {
         "type": "function-call",
         "functionCall": {
           "name": "search_crm_contact",
           "parameters": {"email": "test@example.com"}
         }
       }
     }'
   ```

### Issue: "Voice sounds robotic or unclear"

**Solutions**:

1. **Adjust Voice Settings**:
   - Increase Stability: `0.7` → `0.85`
   - Increase Similarity Boost: `0.8` → `0.9`
   - Adjust Style: Try `0.3` to `0.7` range

2. **Try Different Voice**:
   - Some voices work better for certain content
   - Test multiple voices for 30-60 seconds each

3. **Check Text Formatting**:
   - Remove excessive punctuation
   - Avoid ALL CAPS (sounds like shouting)
   - Add commas for natural pauses

### Issue: "Webhook not receiving calls"

**Symptoms**:
- No logs in backend when function called
- Assistant seems to wait forever

**Solutions**:

1. **Test Webhook Accessibility**:
   ```bash
   # From external machine (or use online tool)
   curl -X POST https://YOUR_WEBHOOK_URL/api/v1/vapi/webhook \
     -H "Content-Type: application/json" \
     -d '{"message":{"type":"test"}}'
   
   # Should return 200 OK
   ```

2. **Check Firewall/Security Groups**:
   - Ensure port 443 (HTTPS) is open
   - Allow Vapi.ai IP addresses (check their docs)

3. **Verify SSL Certificate**:
   ```bash
   # Test SSL validity
   curl -v https://YOUR_WEBHOOK_URL/health
   
   # Should show valid certificate
   ```

4. **Check URL in Vapi Dashboard**:
   - Go to Assistant settings
   - Verify serverUrl is exactly correct
   - No trailing slashes
   - Includes `/api/v1/vapi/webhook` path

### Issue: "Assistant not responding or timing out"

**Solutions**:

1. **Check Silence Timeout**:
   - May be too short, increase to 40-45 seconds
   - Especially for support calls with typing/searching

2. **Verify Max Duration**:
   - 15 minutes = 900 seconds
   - Increase if calls legitimately run longer

3. **Test End Call Phrases**:
   - Make sure they're simple and clear
   - Say exact phrase: "goodbye" or "end call"

### Issue: "High costs / unexpected charges"

**Monitoring**:

```bash
# Check call logs for volume and duration
curl -H "Authorization: Bearer YOUR_PRIVATE_KEY" \
  https://api.vapi.ai/call?assistantId=YOUR_ASSISTANT_ID
```

**Cost Optimization**:

1. **Reduce Max Duration**: 900 sec → 600 sec
2. **Lower Max Tokens**: 500 → 300 (if possible)
3. **Use GPT-3.5 Turbo** for simpler assistants:
   ```json
   "model": {
     "model": "gpt-3.5-turbo"
   }
   ```
4. **Set Usage Alerts**: In Vapi.ai dashboard → Billing

---

## Production Deployment Checklist

### Pre-Production

- [ ] **All 6 assistants created** in Vapi.ai
- [ ] **Voice quality tested** for each assistant
- [ ] **Functions execute successfully** for all assistants
- [ ] **Phone numbers provisioned** and assigned
- [ ] **Webhook URL is HTTPS** with valid SSL certificate
- [ ] **Webhook signature verification** enabled and working
- [ ] **Environment variables** set in production backend
- [ ] **Monitoring/logging** configured for webhook calls
- [ ] **Error alerting** set up (Slack, email, PagerDuty)

### Security Review

- [ ] **Webhook secret** stored securely (not in code)
- [ ] **API keys** in environment variables only
- [ ] **HTTPS enforced** on all webhook endpoints
- [ ] **Rate limiting** implemented on webhook endpoint
- [ ] **Input validation** on all function parameters
- [ ] **PII handling** complies with GDPR/CCPA
- [ ] **Call recordings** encrypted at rest
- [ ] **Access controls** on call logs and transcripts

### Testing Checklist

- [ ] **Inbound calls** work for all 6 assistants
- [ ] **Outbound calls** work (if configured)
- [ ] **Function execution** completes <2 seconds
- [ ] **Error handling** graceful for all failure modes
- [ ] **Escalation paths** trigger correctly
- [ ] **Call logging** captures all data
- [ ] **Transcripts** accurate and complete
- [ ] **Voice quality** rated ≥4/5 by test users

### Performance Benchmarks

Target metrics before production launch:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Function Response Time** | <2 seconds | Webhook execution logs |
| **Voice Latency** | <500ms | Subjective during calls |
| **Call Success Rate** | ≥95% | Vapi dashboard analytics |
| **Function Success Rate** | ≥98% | Backend webhook logs |
| **Voice Quality Rating** | ≥4.0/5 | User feedback surveys |
| **Conversation Flow** | Natural | User testing feedback |

### Go-Live Checklist

- [ ] **Webhook monitoring** active (uptime monitoring)
- [ ] **Cost alerts** configured ($X per day threshold)
- [ ] **On-call rotation** established for issues
- [ ] **Documentation** updated with phone numbers
- [ ] **Marketing materials** ready with voice features
- [ ] **Support team trained** on voice assistant capabilities
- [ ] **Escalation procedures** documented and tested
- [ ] **Rollback plan** prepared if issues arise

### Post-Launch Monitoring (First 48 Hours)

**Critical Metrics to Watch**:

1. **Call Volume**: Track calls per hour
2. **Success Rate**: >95% calls completing successfully
3. **Function Errors**: <2% error rate on functions
4. **User Feedback**: Collect CSAT scores
5. **Cost per Call**: Should be <$1.00 per call
6. **Escalation Rate**: Monitor for excessive escalations

**Daily Check** (First Week):
```bash
# Get call statistics
curl -H "Authorization: Bearer $VAPI_PRIVATE_KEY" \
  "https://api.vapi.ai/call?assistantId=YOUR_ASSISTANT_ID&startTime=2025-11-01T00:00:00Z"

# Review in your backend
curl http://localhost:8000/api/v1/vapi/calls/logs | jq '.logs[] | {agent_id, outcome, duration_seconds}'
```

---

## Advanced Configuration

### Custom Voice Cloning (ElevenLabs)

For ultimate brand consistency, clone specific voices:

1. **Professional Voice Cloning** (requires ElevenLabs Pro):
   - Record 5-10 minutes of clear audio
   - Upload to ElevenLabs
   - Create cloned voice
   - Get voice ID
   - Use in Vapi configuration

2. **Instant Voice Cloning** (lower quality but faster):
   - Record 1 minute sample
   - Generate cloned voice
   - Test quality

### Multi-Language Support

To add Spanish, French, or other languages:

1. **Update Transcriber**:
   ```json
   "transcriber": {
     "provider": "deepgram",
     "model": "nova-2",
     "language": "es"  // Spanish
   }
   ```

2. **Update System Prompt**: Translate to target language

3. **Test End-to-End**: Ensure functions still work

### Call Transfer/Escalation

To enable human transfer:

1. **Add Transfer Destination**:
   ```json
   "endCallFunctionEnabled": true,
   "endCallFunction": {
     "name": "transfer_to_human",
     "parameters": {
       "phone_number": "+15551234567"
     }
   }
   ```

2. **Update Backend**: Implement transfer function

---

## Monitoring & Analytics

### Built-in Vapi Analytics

Access in Dashboard → Analytics:

- **Call Volume**: Calls per day/week/month
- **Duration**: Average call length
- **Cost**: Daily/monthly spending
- **Success Rate**: Completed vs failed calls
- **Top Functions**: Most-called functions

### Custom Analytics (Your Backend)

```python
# Add analytics endpoint
@app.get("/api/v1/vapi/analytics")
async def vapi_analytics(days: int = 7):
    """Generate custom Vapi analytics."""
    logs = call_logs_storage[-days*50:]  # Rough estimate
    
    return {
        "total_calls": len(logs),
        "by_agent": group_by_agent(logs),
        "avg_duration": calculate_avg(logs, "duration_seconds"),
        "total_cost": sum(log.get("cost", 0) for log in logs),
        "success_rate": calculate_success_rate(logs)
    }
```

Access at: `http://localhost:8000/api/v1/vapi/analytics?days=30`

### Alerts Configuration

**Vapi Dashboard**:
1. Settings → Notifications
2. **Usage Alerts**:
   - Alert at $X per day
   - Alert at Y% of monthly minutes
3. **Quality Alerts**:
   - Failed call rate >5%
   - Average duration drops significantly

**Your Backend**:
- Slack webhooks for function failures
- Email alerts for escalations
- PagerDuty for critical errors

---

## Cost Optimization Tips

### Reduce Per-Call Costs

1. **Optimize System Prompts**:
   - Shorter prompts use fewer tokens
   - Be concise but maintain quality
   - Remove redundant instructions

2. **Reduce Max Tokens**:
   - Set to minimum needed for agent's responses
   - Hunter: 500 tokens → 400 tokens
   - Medic: 600 tokens → 450 tokens

3. **Use GPT-3.5 Turbo** (where appropriate):
   - For simple classification
   - For straightforward Q&A
   - Trade-off: Lower quality but 10x cheaper

4. **Reduce Max Duration**:
   - If calls average 5 minutes, set max to 10 minutes
   - Prevents accidentally long calls

5. **Optimize Voice Provider**:
   - ElevenLabs is premium (~$0.30/1K chars)
   - Deepgram's TTS cheaper (~$0.015/1K chars)
   - Trade-off: Quality vs cost

### Monitor Usage

```bash
# Weekly cost check
curl -H "Authorization: Bearer $VAPI_PRIVATE_KEY" \
  "https://api.vapi.ai/usage?startTime=2025-10-25T00:00:00Z&endTime=2025-11-01T00:00:00Z"
```

---

## Maintenance & Updates

### Regular Maintenance Tasks

**Weekly**:
- [ ] Review call logs for quality issues
- [ ] Check function success rates
- [ ] Monitor voice quality feedback
- [ ] Update system prompts if needed

**Monthly**:
- [ ] Analyze call volume trends
- [ ] Review and optimize costs
- [ ] Update voice models if new ones available
- [ ] Refresh training based on real calls

**Quarterly**:
- [ ] Major system prompt updates
- [ ] Re-evaluate voice selections
- [ ] Assess ROI vs human agents
- [ ] Plan new features or assistants

### Updating Assistant Configuration

**To update an existing assistant**:

1. Go to Dashboard → Assistants
2. Click on assistant to edit
3. Make changes to:
   - System prompt (most common update)
   - Functions (add/modify/remove)
   - Voice settings
   - Advanced settings
4. Click **"Save"**
5. Test immediately with phone call
6. Monitor first 10-20 calls for issues

**Version Control**: Keep your JSON configs in git and update them when you make dashboard changes.

---

## Function Implementation Guide

### Backend Function Handler Template

When adding new functions to your webhook handler:

```python
async def handle_your_new_function(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle your custom function.
    
    Args:
        params: Function parameters from Vapi
        
    Returns:
        Dict with result data
    """
    try:
        # Extract parameters
        required_param = params.get("required_param")
        optional_param = params.get("optional_param", "default")
        
        # Validate inputs
        if not required_param:
            return {
                "error": "Missing required parameter",
                "success": False
            }
        
        # Execute business logic
        result = await your_business_logic(required_param)
        
        # Return structured response
        return {
            "success": True,
            "data": result,
            "message": "Operation completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Function failed: {e}")
        return {
            "error": str(e),
            "success": False,
            "message": "I encountered an issue. Let me escalate to my team."
        }
```

### Function Response Format

Vapi expects this structure:

```json
{
  "result": {
    // Your function's return data
    "success": true,
    "data": {...}
  },
  "metadata": {
    "timestamp": "2025-11-01T03:53:38Z",
    "execution_time_ms": 145,
    "function_name": "search_crm_contact"
  }
}
```

---

## Integration with Existing Systems

### CRM Integration (HubSpot/Salesforce)

**Mapping Vapi Functions to CRM**:

```python
# In apps/adapter/src/api/vapi.py

async def handle_search_crm_contact(params):
    """Route to existing CRM provider."""
    from src.providers.crm.hubspot import HubSpotProvider
    
    provider = HubSpotProvider()
    result = await provider.search_contacts(
        query=params.get("email"),
        limit=1
    )
    return result

async def handle_create_crm_contact(params):
    """Create contact with BANT scores."""
    from src.providers.crm.hubspot import HubSpotProvider
    
    provider = HubSpotProvider()
    
    # Build contact data with BANT custom fields
    contact_data = {
        "email": params["email"],
        "firstname": params["first_name"],
        "lastname": params["last_name"],
        "company": params["company"],
        # Custom fields for BANT
        "bant_budget_score": params.get("budget_score"),
        "bant_authority_score": params.get("authority_score"),
        "bant_need_score": params.get("need_score"),
        "bant_timeline_score": params.get("timeline_score"),
        "bant_total_score": params["total_score"],
        "hs_lead_status": "qualified" if params["total_score"] >= 70 else "unqualified",
        "lifecyclestage": "lead"
    }
    
    result = await provider.create_contact(contact_data)
    return result
```

### Helpdesk Integration (Zendesk)

```python
async def handle_create_support_ticket(params):
    """Create Zendesk ticket from voice call."""
    from src.providers.helpdesk.zendesk import ZendeskProvider
    
    provider = ZendeskProvider()
    
    # Map priority to Zendesk values
    priority_map = {
        "low": "low",
        "normal": "normal",
        "high": "high",
        "urgent": "urgent"
    }
    
    ticket_data = {
        "subject": params["subject"],
        "description": params["description"],
        "priority": priority_map.get(params.get("priority", "normal")),
        "tags": params.get("tags", []) + ["voice_call", "vapi"],
        "requester": {
            "email": params["requester_email"],
            "name": params.get("requester_name")
        }
    }
    
    result = await provider.create_ticket(ticket_data)
    return result
```

---

## Scaling Considerations

### Concurrent Call Limits

**Vapi Plan Limits**:
- Hobby: 5 concurrent calls
- Growth: 25 concurrent calls  
- Business: 100 concurrent calls

**Your Backend**:
- Ensure webhook can handle concurrent requests
- Use async/await properly
- Consider connection pooling for databases

### High-Volume Scenarios

**If expecting >100 calls/day**:

1. **Implement Caching**:
   ```python
   # Cache CRM lookups for 5 minutes
   from functools import lru_cache
   
   @lru_cache(maxsize=1000)
   async def cached_crm_lookup(email: str):
       return await crm_provider.search(email)
   ```

2. **Queue Function Calls**:
   - For non-critical functions, use background tasks
   - Respond quickly to Vapi, process async

3. **Scale Backend**:
   - Multiple adapter instances behind load balancer
   - Redis for shared caching
   - Database connection pooling

---

## Security Best Practices

### Webhook Security

1. **Always Verify Signatures**:
   ```python
   # Never skip signature verification in production
   if not verify_vapi_signature(body, signature, secret):
       raise HTTPException(401, "Unauthorized")
   ```

2. **Use HTTPS Only**:
   - Never HTTP for production webhooks
   - Valid SSL certificate required

3. **Rate Limiting**:
   ```python
   # Limit webhook requests
   from slowapi import Limiter
   
   limiter = Limiter(key_func=get_remote_address)
   
   @app.post("/api/v1/vapi/webhook")
   @limiter.limit("100/minute")
   async def vapi_webhook(...):
       ...
   ```

4. **Input Validation**:
   ```python
   # Validate all function parameters
   from pydantic import BaseModel, validator
   
   class ContactParams(BaseModel):
       email: EmailStr
       first_name: str
       
       @validator('email')
       def email_must_be_valid(cls, v):
           # Additional validation
           return v
   ```

### Data Privacy

1. **PII Handling**:
   - Mask sensitive data in logs
   - Encrypt call recordings
   - Honor deletion requests (GDPR)

2. **Retention Policies**:
   ```python
   # Auto-delete old call logs
   DELETE_AFTER_DAYS = 90
   
   async def cleanup_old_calls():
       cutoff = datetime.now() - timedelta(days=DELETE_AFTER_DAYS)
       await db.delete_calls_before(cutoff)
   ```

3. **Consent Management**:
   - First message should mention recording: "This call may be recorded for quality assurance"
   - Provide opt-out mechanism

---

## Support Resources

### Vapi.ai Resources

- **Documentation**: [https://docs.vapi.ai](https://docs.vapi.ai)
- **API Reference**: [https://docs.vapi.ai/api-reference](https://docs.vapi.ai/api-reference)
- **Discord Community**: [https://discord.gg/vapi](https://discord.gg/vapi)
- **Status Page**: [https://status.vapi.ai](https://status.vapi.ai)
- **Support Email**: support@vapi.ai

### ElevenLabs Resources

- **Documentation**: [https://docs.elevenlabs.io](https://docs.elevenlabs.io)
- **Voice Library**: [https://elevenlabs.io/voice-library](https://elevenlabs.io/voice-library)
- **API Docs**: [https://docs.elevenlabs.io/api-reference](https://docs.elevenlabs.io/api-reference)

### Transform Army AI Resources

- **Adapter Documentation**: [`docs/adapter-contract.md`](docs/adapter-contract.md:1)
- **Agent Roles**: [`packages/agents/roles/`](packages/agents/roles/:1)
- **Agent Policies**: [`packages/agents/policies/`](packages/agents/policies/:1)
- **Architecture**: [`ARCHITECTURE.md`](ARCHITECTURE.md:1)

---

## Quick Reference

### Configuration File Locations

```
vapi-config/
├── assistants/
│   ├── hunter-bdr.json         # ALPHA-1: Sales qualification
│   ├── medic-support.json      # ALPHA-2: Customer support
│   ├── scout-research.json     # BRAVO-1: Competitive intel
│   ├── engineer-ops.json       # BRAVO-2: Operations monitoring
│   ├── intel-knowledge.json    # CHARLIE-1: KB management
│   └── guardian-qa.json        # CHARLIE-2: Quality assurance
└── VAPI_DEPLOYMENT_GUIDE.md    # This file
```

### Agent Quick Reference

| Agent | Call Sign | Rank | Primary Use | Phone Type | Voice Type |
|-------|-----------|------|-------------|------------|------------|
| **Hunter** | ALPHA-1 | SSG (E-6) | Sales inquiry calls | Public | Professional male, confident |
| **Medic** | ALPHA-2 | SGT (E-5) | Customer support | Public | Empathetic female, calm |
| **Scout** | BRAVO-1 | SSG (E-6) | Research briefings | Internal | Analytical male, methodical |
| **Engineer** | BRAVO-2 | SFC (E-7) | Ops status calls | Internal | Authoritative male, direct |
| **Intel** | CHARLIE-1 | SPC (E-4) | Doc consultations | Internal | Clear female, educational |
| **Guardian** | CHARLIE-2 | MSG (E-8) | QA reviews | Internal | Precise male, professional |

### Temperature Settings Explained

| Agent | Temperature | Why |
|-------|-------------|-----|
| Hunter | 0.3 | Consistent BANT scoring, professional but conversational |
| Medic | 0.2 | Very consistent for support, accurate solutions |
| Scout | 0.3 | Analytical but creative for insights |
| Engineer | 0.1 | Deterministic for operational data |
| Intel | 0.3 | Structured but helpful in explanations |
| Guardian | 0.1 | Highly consistent for fair QA scoring |

### Webhook Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/vapi/webhook` | POST | Main webhook for all events |
| `/api/v1/vapi/calls/log` | POST | Log completed calls |
| `/api/v1/vapi/calls/logs` | GET | Retrieve call history |

---

## Deployment Sequence

### Recommended Deployment Order

**Phase 1: Customer-Facing Agents** (Week 1)
1. **Hunter** (BDR) - Sales inquiry line
2. **Medic** (Support) - Customer support line

**Phase 2: Internal Operations** (Week 2)
3. **Scout** (Research) - For sales team intelligence
4. **Engineer** (Ops) - For operations monitoring

**Phase 3: Specialized Functions** (Week 3)
5. **Intel** (Knowledge) - For doc team
6. **Guardian** (QA) - For quality monitoring

**Rationale**: Deploy customer-facing assistants first to start generating value immediately. Internal assistants can be refined based on learnings from customer interactions.

---

## Success Metrics

### Track These KPIs

**For Hunter (BDR)**:
- Calls answered: Target 100% of inbound
- Qualification completion rate: ≥80%
- Meeting booking rate: ≥60% of qualified
- CRM data quality: ≥95% complete

**For Medic (Support)**:
- First response time: <2 minutes
- Deflection rate: ≥40%
- Customer satisfaction: ≥4.5/5
- Escalation context quality: ≥90% rated helpful

**For All Agents**:
- Call completion rate: ≥95%
- Function success rate: ≥98%
- Voice quality rating: ≥4.0/5
- Cost per call: <$1.00

---

## Emergency Procedures

### If Vapi.ai is Down

1. **Check Status**: [https://status.vapi.ai](https://status.vapi.ai)
2. **Fallback Plan**:
   - Display "Voice unavailable" message on website
   - Offer text chat or email form
   - Post status update for customers
3. **Communication**:
   - Update status page
   - Email affected users
   - Slack alert to team

### If Webhook Fails

1. **Check Backend**:
   ```bash
   # Test if adapter is running
   curl http://localhost:8000/health
   ```

2. **Check Logs**:
   ```bash
   # Review recent errors
   tail -f apps/adapter/logs/error.log
   ```

3. **Restart Services**:
   ```bash
   # Restart adapter
   cd apps/adapter
   python src/main_simple.py
   ```

4. **Verify Connectivity**:
   ```bash
   # Test webhook from external
   curl -X POST https://YOUR_URL/api/v1/vapi/webhook \
     -H "Content-Type: application/json" \
     -d '{"message":{"type":"test"}}'
   ```

### If Voice Quality Degrades

1. **Test Current Voice**:
   - Make test call
   - Record and review
   - Rate quality 1-5

2. **Adjust Settings** in Vapi dashboard:
   - Increase Stability: 0.7 → 0.85
   - Increase Similarity Boost: 0.8 → 0.9
   - Try different voice if needed

3. **Check ElevenLabs Status** (if using):
   - May be temporary service degradation
   - Switch to Deepgram fallback if critical

---

## FAQ

### Q: Can I use multiple phone numbers for one assistant?

**A**: Yes! In Vapi dashboard, you can assign multiple numbers to the same assistant. Useful for:
- Different regions (e.g., US vs UK number)
- Different campaigns tracking sources
- A/B testing

### Q: How do I prevent spam or abuse?

**A**: Several options:

1. **Implement Rate Limiting** in webhook:
   ```python
   # Block excessive calls from same number
   @limiter.limit("10/hour")
   async def vapi_webhook(...):
   ```

2. **Use Vapi's Built-in Protections**:
   - Max concurrent calls (prevents flooding)
   - Max duration (prevents long abusive calls)

3. **Blacklist Numbers**:
   - In Vapi dashboard, block specific phone numbers
   - Implement backend blacklist checking

### Q: Can assistants transfer to human agents?

**A**: Yes! Configure transfer:

```json
{
  "endCallFunctionEnabled": true,
  "endCallFunction": {
    "name": "transfer_to_human_agent",
    "parameters": {
      "destination": "+15551234567",
      "reason": "Customer requested human agent"
    }
  }
}
```

Then implement the transfer function in your webhook handler.

### Q: How do I handle multiple languages?

**A**: Create separate assistants per language:

1. Duplicate assistant config
2. Change transcriber language: `"language": "es"`
3. Translate system prompt and messages
4. Deploy and assign language-specific phone number

### Q: What if a function takes >10 seconds?

**A**: Vapi has ~10 second timeout for functions. Solutions:

1. **Optimize Function**: Make it faster
2. **Return Immediately, Process Async**:
   ```python
   async def handle_long_function(params):
       # Queue for background processing
       task_id = queue_task(params)
       
       # Return immediately
       return {
           "status": "processing",
           "task_id": task_id,
           "message": "I'm working on that. I'll have results shortly."
       }
   ```
3. **Break Into Smaller Functions**: Split one long function into multiple quick ones

### Q: Can I record calls for compliance/training?

**A**: Yes, recording is enabled by default in all configs:

```json
"recordingEnabled": true
```

**Access Recordings**:
1. Vapi Dashboard → Calls → Select call → Download recording
2. Via API:
   ```bash
   curl -H "Authorization: Bearer $VAPI_PRIVATE_KEY" \
     "https://api.vapi.ai/call/CALL_ID/recording"
   ```

**Compliance**: Ensure first message mentions recording (already included in all configs).

---

## Next Steps After Deployment

1. **Collect User Feedback**:
   - Send CSAT surveys after calls
   - Track positive vs negative sentiment
   - Identify improvement areas

2. **Analyze Call Transcripts**:
   - Review for common questions
   - Identify edge cases
   - Update system prompts based on learnings

3. **Optimize Performance**:
   - Monitor function execution times
   - Optimize slow functions
   - Adjust timeout settings

4. **Expand Capabilities**:
   - Add new functions as needs arise
   - Create additional specialized assistants
   - Integrate with more backend systems

5. **Scale Infrastructure**:
   - Upgrade Vapi plan as volume grows
   - Scale backend to handle load
   - Add redundancy and failover

---

## Appendix A: Complete Example Import (Hunter)

**Step-by-Step for First Assistant**:

1. **Login to Vapi.ai** dashboard

2. **Click "Assistants"** → **"Create Assistant"**

3. **Basic Information**:
   ```
   Name: Hunter - BDR Concierge (ALPHA-1)
   ```

4. **Model** tab:
   ```
   Provider: OpenAI
   Model: gpt-4
   Temperature: 0.3
   Max Tokens: 500
   ```

5. **System Prompt** (copy this entire block):
   ```
   You are Hunter, call sign ALPHA-1, a Business Development Representative AI agent with the rank of Staff Sergeant in the Transform Army AI cyber warfare unit. Your MOS is 18F (Special Forces Intelligence Sergeant).

   MISSION: Qualify inbound sales leads using the BANT framework and coordinate discovery meetings for qualified prospects.

   [... rest of system prompt from hunter-bdr.json ...]
   ```

6. **Voice** tab:
   ```
   Provider: 11labs
   Voice ID: [Your ElevenLabs voice ID]
   Stability: 0.7
   Similarity Boost: 0.8
   Style: 0.5
   Speaker Boost: ON
   ```

7. **Messages** tab:
   ```
   First Message: This is Hunter from Transform Army AI, call sign Alpha-One. Thanks for reaching out! I'm here to learn about your business needs and see how our cyber operations platform can help. To start, could you tell me a bit about what brought you to us today?

   End Call Message: Thanks for your time today! You'll receive a confirmation email shortly with all the details and next steps. Looking forward to our discovery meeting. Stay operational!

   Voicemail: This is Hunter from Transform Army AI. I'm here to discuss your inquiry about our platform. Please call back or visit our website to schedule a time to connect. Thanks for reaching out!
   ```

8. **Functions** tab - Add Function 1:
   ```
   Name: search_crm_contact
   Description: Search for existing contact in CRM by email or company to prevent duplicates and retrieve contact history
   
   Parameters:
   - Name: email
     Type: string
     Description: Email address to search for in CRM
     Required: YES
     
   - Name: query
     Type: string
     Description: Optional additional search query (company name, etc.)
     Required: NO
   ```

9. **Repeat** for functions 2, 3, 4

10. **Server** tab:
    ```
    Server URL: https://YOUR_WEBHOOK_URL/api/v1/vapi/webhook
    Server URL Secret: [Your webhook secret]
    ```

11. **Advanced** tab:
    ```
    Recording Enabled: ON
    Silence Timeout: 30 seconds
    Max Duration: 900 seconds
    Background Sound: OFF
    Backchanneling: OFF
    
    End Call Phrases:
    - goodbye
    - that's all for now
    - thank you hunter
    - end call
    ```

12. **Click "Create"**

13. **Save Assistant ID**: `asst_hunter_abc123...`

14. **Test immediately** by calling the phone number

---

## Appendix B: Webhook Payload Examples

### Function Call Payload

What Vapi sends when assistant calls a function:

```json
{
  "message": {
    "type": "function-call",
    "functionCall": {
      "name": "search_crm_contact",
      "parameters": {
        "email": "john@example.com",
        "query": "Acme Corp"
      }
    },
    "call": {
      "id": "call_abc123",
      "assistant": {
        "id": "asst_hunter_abc123",
        "name": "Hunter - BDR Concierge (ALPHA-1)"
      }
    }
  }
}
```

### Expected Response Format

What your webhook should return:

```json
{
  "result": {
    "contacts": [
      {
        "id": "contact_001",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "company": "Acme Corp"
      }
    ],
    "total_found": 1
  },
  "metadata": {
    "timestamp": "2025-11-01T03:53:38Z",
    "execution_time_ms": 145,
    "success": true
  }
}
```

### Call Ended Payload

```json
{
  "message": {
    "type": "call-ended",
    "call": {
      "id": "call_abc123",
      "assistant": {
        "id": "asst_hunter_abc123"
      },
      "duration": 247,
      "endedReason": "assistant-ended-call",
      "cost": 0.45,
      "transcript": "Full conversation transcript here..."
    }
  }
}
```

---

## Appendix C: Voice Testing Scripts

Test each voice personality with these scripts:

**Hunter Test Script**:
```
"Hi there! Thanks for calling Transform Army AI. I'm Hunter, and I'd love to learn about your business needs. Let's start with what brought you to us today. What challenges are you looking to solve?"
```

**Medic Test Script**:
```
"I understand that's frustrating. Let me search our knowledge base for the solution. This should only take a moment... Okay, I found it! Here's what you need to do. First, go to your account settings..."
```

**Scout Test Script**:
```
"Acknowledged. I'll conduct a comprehensive competitive analysis on that company. I'll be gathering intelligence from multiple sources including their website, recent news, technology stack, and customer reviews. Expect a detailed briefing within four hours."
```

**Engineer Test Script**:
```
"Operations status report: SLA compliance at 96.8%. Three tickets approaching breach threshold. Data quality score 94.2%, within acceptable range. Two anomalies detected in the past hour. Detailed metrics will be emailed. Any immediate concerns?"
```

**Intel Test Script**:
```
"I've identified three high-priority documentation gaps based on recent support tickets. First, we need an article on API authentication flows - requested by 12 users this month. Second, the mobile app installation guide needs updating. And third, we're missing integration documentation for PowerBI. Would you like me to create these?"
```

**Guardian Test Script**:
```
"Quality assessment complete. The agent output scores 8.2 out of 10. Accuracy: 9. Completeness: 8. Format: 8. Tone: 8. Compliance: 8. No blocking issues detected. Recommendation: Minor improvements to formatting structure. Otherwise approved for deployment."
```

---

## Support & Troubleshooting Contacts

**Vapi.ai Support**:
- Email: support@vapi.ai
- Discord: [https://discord.gg/vapi](https://discord.gg/vapi)
- Response time: <24 hours

**Transform Army AI Internal**:
- Engineering: Your engineering team lead
- Operations: Your ops manager  
- Questions about agent logic: Refer to agent role docs

---

**END OF DEPLOYMENT GUIDE**

🎖️ **Mission Brief**: Deploy all 6 voice assistants for operational readiness.  
🎯 **Success Criteria**: All assistants functional, tested, and available via phone.  
📞 **Support**: Refer to this guide and official Vapi.ai documentation.

**Ready for deployment! Signal completion when all 6 assistants are operational.**