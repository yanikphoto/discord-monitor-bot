import discord
import smtplib
import asyncio
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiscordMonitor(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        
        # Configuration
        self.CHANNEL_ID = 1190457613394137178
        self.EMAIL_TO = "bo_zyeux@hotmail.com"
        self.EMAIL_FROM = os.getenv('EMAIL_FROM')  # Your email
        self.EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')  # Your app password
        self.SMTP_SERVER = "smtp.gmail.com"  # Change if not using Gmail
        self.SMTP_PORT = 587
        self.last_message_id = None
    
    async def on_ready(self):
        logger.info(f'Bot connected as {self.user}')
        logger.info(f'Monitoring channel ID: {self.CHANNEL_ID}')
        
        # Get the channel and set last message ID
        channel = self.get_channel(self.CHANNEL_ID)
        if channel:
            try:
                async for message in channel.history(limit=1):
                    self.last_message_id = message.id
                    logger.info(f'Started monitoring from message ID: {self.last_message_id}')
                    break
            except Exception as e:
                logger.error(f'Error getting channel history: {e}')
        else:
            logger.error(f'Could not find channel with ID: {self.CHANNEL_ID}')
    
    async def on_message(self, message):
        # Only process messages from the target channel
        if message.channel.id != self.CHANNEL_ID:
            return
        
        # Skip messages older than our last processed message
        if self.last_message_id and message.id <= self.last_message_id:
            return
        
        # Skip bot messages
        if message.author.bot:
            return
        
        # Update last message ID
        self.last_message_id = message.id
        
        # Send email notification
        await self.send_email_notification(message)
    
    async def send_email_notification(self, message):
        try:
            # Format the email content
            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            author = f"{message.author.display_name} (@{message.author.name})"
            content = message.content if message.content else "[No text content]"
            
            # Handle embeds
            embed_content = ""
            if message.embeds:
                for embed in message.embeds:
                    if embed.title:
                        embed_content += f"\n\nEmbed Title: {embed.title}"
                    if embed.description:
                        embed_content += f"\nEmbed Description: {embed.description}"
            
            # Handle attachments
            attachment_info = ""
            if message.attachments:
                attachment_info = f"\n\nAttachments: {len(message.attachments)} file(s)"
                for att in message.attachments:
                    attachment_info += f"\n- {att.filename} ({att.url})"
            
            # Create email body
            email_body = f"""New message in Discord channel!

Time: {timestamp}
Author: {author}
Channel: #{message.channel.name}

Message:
{content}{embed_content}{attachment_info}

---
Discord Channel Monitor Bot
"""
            
            # Create email
            msg = MIMEMultipart()
            msg['From'] = self.EMAIL_FROM
            msg['To'] = self.EMAIL_TO
            msg['Subject'] = "Meta Signals Alert"
            
            msg.attach(MIMEText(email_body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT)
            server.starttls()
            server.login(self.EMAIL_FROM, self.EMAIL_PASSWORD)
            text = msg.as_string()
            server.sendmail(self.EMAIL_FROM, self.EMAIL_TO, text)
            server.quit()
            
            logger.info(f'Email sent for message from {author}')
            
        except Exception as e:
            logger.error(f'Error sending email: {e}')

# Main execution
if __name__ == "__main__":
    # Get Discord token from environment variable
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN environment variable not set!")
        exit(1)
    
    if not os.getenv('EMAIL_FROM') or not os.getenv('EMAIL_PASSWORD'):
        logger.error("Email credentials not set!")
        exit(1)
    
    # Create and run the bot
    bot = DiscordMonitor()
    bot.run(DISCORD_TOKEN)