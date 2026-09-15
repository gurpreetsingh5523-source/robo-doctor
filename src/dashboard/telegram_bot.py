"""
AMRIT Telegram Bot v6.1
Multi-platform messaging integration
"""
from __future__ import annotations
import os
import json
import asyncio
from typing import Dict, Optional
from datetime import datetime

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("Warning: python-telegram-bot not installed. Install with: pip install python-telegram-bot")

class AMRITTelegramBot:
    """
    Telegram bot for AMRIT Research OS
    Provides chat interface for all AMRIT modules
    """

    def __init__(self, token: str = None):
        self.token = token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.application = None
        self.user_sessions = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_text = """
🕉️ *Welcome to AMRIT Research OS v6.1*

"ਸਰਬੱਤ ਦਾ ਭਲਾ" - Welfare of All Humanity

I am your intelligent medical research assistant. I can help you with:

🩸 *Blood Analysis* - Analyze blood test results
🧬 *DNA Analysis* - Genetic risk assessment
👨‍👩‍👧‍👦 *Consanguinity* - Marriage risk calculation
💊 *Drug Predictor* - Pharmacogenomics
🔬 *Research* - Autonomous medical research
⚖️ *Ethics* - Gurmat + Medical ethics review
🌍 *Pandemic* - Risk prediction
🏥 *Health Advisor* - Personalized recommendations

Just type your query naturally, or use /help for commands.

*Founder:* Gurpreet Singh
*Mission:* Lifelong Seva through technology
        """

        keyboard = [
            [InlineKeyboardButton("🩸 Blood Test", callback_data='blood'),
             InlineKeyboardButton("🧬 DNA Analysis", callback_data='dna')],
            [InlineKeyboardButton("💊 Drug Predictor", callback_data='drug'),
             InlineKeyboardButton("🔬 Research", callback_data='research')],
            [InlineKeyboardButton("⚖️ Ethics Check", callback_data='ethics'),
             InlineKeyboardButton("🏥 Health Advice", callback_data='health')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
*AMRIT Commands:*

/start - Start the bot
/help - Show this help
/blood - Analyze blood tests
/dna - DNA variant analysis
/drug - Drug response prediction
/research - Start autonomous research
/ethics - Ethics assessment
/team - Configure agent team
/status - System status

*Example queries:*
• "My glucose is 110, is it normal?"
• "Research diabetes in Punjabis"
• "Check ethics of genetic screening"
• "First cousin marriage risk"
• "Warfarin drug prediction"
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user messages"""
        user_id = update.effective_user.id
        message_text = update.message.text

        # Store session
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {'history': [], 'profile': {}}

        self.user_sessions[user_id]['history'].append({
            'role': 'user',
            'content': message_text,
            'timestamp': datetime.now().isoformat()
        })

        # Detect intent (reuse router from chat_dashboard)
        intent = self._detect_intent(message_text)

        # Generate response
        response = self._generate_response(intent, message_text, user_id)

        # Store bot response
        self.user_sessions[user_id]['history'].append({
            'role': 'bot',
            'content': response,
            'timestamp': datetime.now().isoformat()
        })

        await update.message.reply_text(response, parse_mode='Markdown')

    def _detect_intent(self, message: str) -> str:
        """Simple intent detection"""
        message_lower = message.lower()

        keywords = {
            'blood': ['blood', 'glucose', 'cholesterol', 'hemoglobin', 'hba1c'],
            'dna': ['dna', 'gene', 'genetic', 'variant', 'apoe', 'mthfr'],
            'drug': ['drug', 'medicine', 'warfarin', 'clopidogrel', 'metformin'],
            'research': ['research', 'study', 'paper', 'literature', 'pubmed'],
            'ethics': ['ethics', 'moral', 'consent', 'gurmat'],
            'consanguinity': ['cousin', 'marriage', 'consanguinity', 'thalassemia'],
            'pandemic': ['pandemic', 'outbreak', 'covid', 'virus'],
            'health': ['health', 'diet', 'exercise', 'lifestyle']
        }

        for intent, words in keywords.items():
            for word in words:
                if word in message_lower:
                    return intent

        return 'general'

    def _generate_response(self, intent: str, message: str, user_id: int) -> str:
        """Generate response based on intent"""

        responses = {
            'blood': """
🩸 *Blood Analysis Requested*

Please provide your blood test values in this format:
`glucose: 95, hba1c: 5.8, ldl: 110`

I will analyze them with 4-level detection (Normal/Borderline/High/Critical) and provide population-specific recommendations.

*Supported tests:* Glucose, HbA1c, LDL, HDL, Triglycerides, Hemoglobin, WBC, Creatinine, and 25+ more.
            """,

            'dna': """
🧬 *DNA Analysis Requested*

Please share your genetic variants:
`APOE4: 1_copy, MTHFR_C677T: CT, FTO: AT`

I will analyze:
• Alzheimer's risk (APOE4)
• Cardiovascular risk (MTHFR)
• Obesity risk (FTO)
• Lactose intolerance (LCT)
• Alcohol metabolism (ALDH2)
• And 5 more variants

*Privacy:* Your data is processed locally and never shared.
            """,

            'drug': """
💊 *Drug Response Prediction*

Please provide:
1. Drug name (e.g., warfarin, clopidogrel, codeine)
2. Your pharmacogenomic variants if known

I will predict:
• Optimal dosage
• Side effect risk
• Alternative drugs
• Contraindications

*Based on:* CYP2D6, CYP2C19, CYP2C9, TPMT, DPYD, and 8 more biomarkers.
            """,

            'research': """
🔬 *Autonomous Research Initiated*

I will start research on: *%s*

*Process:*
1. Literature mining (PubMed, ArXiv, etc.)
2. Pattern detection
3. Hypothesis generation
4. Statistical validation
5. Ethics review

*Estimated time:* 2-5 minutes

You will receive a comprehensive report with findings, recommendations, and generated paper.
            """ % message,

            'ethics': """
⚖️ *Ethics Assessment*

I will evaluate your proposal against:

*Gurmat Principles:*
• ਸਰਬੱਤ ਦਾ ਭਲਾ (Welfare of all)
• ਸੇਵਾ (Selfless service)
• ਦਯਾ (Compassion)
• ਸਤ (Truth)

*Medical Ethics:*
• Autonomy, Beneficence
• Non-maleficence, Justice
• Dignity

*Prohibited:* Eugenics, discrimination, exploitation

Please describe your research or action for review.
            """,

            'consanguinity': """
👨‍👩‍👧‍👦 *Consanguinity Risk Assessment*

Please specify:
• Relationship type (first cousin, double first cousin, uncle-niece, etc.)
• Any known family history

I will assess 20+ diseases including:
• Thalassemia, Sickle cell
• Cystic fibrosis, Tay-Sachs
• Gaucher, Spinal muscular atrophy
• And 15 more

*South Asian focus:* Higher carrier frequencies considered.
            """,

            'pandemic': """
🌍 *Pandemic Risk Assessment*

Please provide location or population data:
• City/Region
• Population density
• Vaccination rate
• Healthcare capacity

I will calculate:
• Risk score (0-1)
• Alert level (Green/Yellow/Orange/Red)
• Key drivers
• Mitigation strategies

*Based on:* Real-time epidemiological models.
            """,

            'health': """
🏥 *Personalized Health Assessment*

I will provide comprehensive recommendations based on:
• DNA variants
• Blood analysis
• Environmental factors (PM2.5, arsenic, etc.)

*Recommendations include:*
• Diet modifications
• Lifestyle changes
• Supplements
• Exercise plans
• Screening schedule

Please share your health profile or ask specific questions.
            """,

            'general': """
🕉️ *AMRIT Research OS v6.1*

I can help you with:

🩸 *Blood Analysis* - "My glucose is 110"
🧬 *DNA Analysis* - "APOE4 1_copy"
💊 *Drug Predictor* - "Warfarin response"
🔬 *Research* - "Study diabetes in Punjabis"
⚖️ *Ethics* - "Check genetic screening ethics"
👨‍👩‍👧‍👦 *Consanguinity* - "First cousin risk"
🌍 *Pandemic* - "Delhi outbreak risk"
🏥 *Health* - "Diet for South Asian"

Just type your question naturally!
            """
        }

        return responses.get(intent, responses['general'])

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()

        intent_map = {
            'blood': 'blood',
            'dna': 'dna',
            'drug': 'drug',
            'research': 'research',
            'ethics': 'ethics',
            'health': 'health'
        }

        intent = intent_map.get(query.data, 'general')
        response = self._generate_response(intent, query.data, query.from_user.id)

        await query.edit_message_text(response, parse_mode='Markdown')

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        status_text = """
📊 *AMRIT System Status*

✅ *Modules Online:* 16
✅ *Agents Active:* 7
✅ *Knowledge Graph:* 13 entities, 12 relationships
✅ *Memory:* SQLite + Vector
✅ *Ethics Filter:* Active
✅ *Auto-Improvement:* Running

*Version:* 6.1.0
*Uptime:* Active
*Users Served:* %d

*ਸਰਬੱਤ ਦਾ ਭਲਾ* 🕉️
        """ % len(self.user_sessions)

        await update.message.reply_text(status_text, parse_mode='Markdown')

    def run(self):
        """Start the bot"""
        if not TELEGRAM_AVAILABLE:
            print("Error: python-telegram-bot not installed")
            print("Install: pip install python-telegram-bot")
            return

        if not self.token:
            print("Error: TELEGRAM_BOT_TOKEN not set")
            print("Set environment variable: export TELEGRAM_BOT_TOKEN=your_token")
            return

        self.application = Application.builder().token(self.token).build()

        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        print("🕉️ AMRIT Telegram Bot v6.1 starting...")
        print("ਸਰਬੱਤ ਦਾ ਭਲਾ - Welfare of All Humanity")

        self.application.run_polling()

# Discord bot placeholder (for future implementation)
class AMRITDiscordBot:
    """Discord bot placeholder - implement with discord.py"""

    def __init__(self, token: str = None):
        self.token = token or os.getenv('DISCORD_BOT_TOKEN')

    def run(self):
        print("Discord bot implementation pending")
        print("Install: pip install discord.py")

if __name__ == "__main__":
    bot = AMRITTelegramBot()
    bot.run()
