import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
from g4f.client import Client

TOKEN = "" #input your own token
intents = discord.Intents.default()
intents.message_content = True  
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("Bot is ready!")
    await bot.tree.sync()

@bot.tree.command(name="ping", description="Responds with Pong!")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@bot.tree.command(name="about", description="Explains what this bot is about")
async def about(interaction: discord.Interaction):
    about_embed = discord.Embed(
        title="About Mr. Bee",
        description="Mr. Bee is a project for the EHS hackathon.",
        color=discord.Color.blue()
    )
    
    await interaction.response.send_message(embed=about_embed)  

@bot.tree.command(name="help", description="Tells all bot commands.")
async def help_command(interaction: discord.Interaction):
    help_embed = discord.Embed(
        title="Mr. Bee Commands",
        color=discord.Color.green()  
    )
    help_embed.add_field(name="/about", value="-Tells about project", inline=False),
    help_embed.add_field(name="/help", value="-Tells project commands", inline=False),
    help_embed.add_field(name="/view_flashcard", value="-Adds a flashcard", inline=False),
    help_embed.add_field(name="/trivia", value="-Trivia question", inline=False), 
    help_embed.add_field(name="/test", value="- Test your knowledge on flashcards", inline=False)

    
    
    await interaction.response.send_message(embed=help_embed)

@bot.tree.command(name="ai", description="Use AI to help enhance your learning and cure you doubts!")
@app_commands.describe(prompt="Enter your prompt")
async def ai(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer()

    try:
        client = Client()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
        )

        ai_response = response.choices[0].message.content

        await interaction.followup.send(f"{ai_response}")

    except Exception as e:
        await interaction.followup.send(f"Something went wrong: {str(e)}")


user_notes = {}

@bot.tree.command(name='add_note', description="Add a flashcard note")
@app_commands.describe(question="Enter the question", answer="Enter the answer")
async def add_note(interaction: discord.Interaction, question: str, answer: str,):
    user_id = interaction.user.id 

    if user_id not in user_notes:
        user_notes[user_id] = []

    user_notes[user_id].append({"question": question, "answer": answer, "id": id})

    await interaction.response.send_message(
        f"Flashcard added!\n**Question:** {question}\n**Answer:** {answer}"
    )


@bot.tree.command(name='test', description="Test your knowledge on your flashcards")
async def test(interaction: discord.Interaction):
    user_id = interaction.user.id  

    if user_id not in user_notes or not user_notes[user_id]:
        await interaction.response.send_message("You don't have any flashcards yet. Add some with `/add_note`.")
        return

    await interaction.response.defer(thinking=True)

    flashcards = user_notes[user_id]
    for idx, card in enumerate(flashcards):
        await interaction.followup.send(f"Flashcard {idx + 1}:\n**Q:** {card['question']}")
        
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            user_response = await bot.wait_for('message', check=check, timeout=30.0)
            
            if user_response.content.strip().lower() == card['answer'].strip().lower():
                await interaction.followup.send("✅ Correct answer!")
            else:
                await interaction.followup.send(f"❌ Incorrect answer! The correct answer is: **{card['answer']}**")
        
        except asyncio.TimeoutError:
            await interaction.followup.send("⏳ Time's up for this flashcard!")


user_trivia = {}


@bot.tree.command(name="triva", description="AI will generate five random trivia questions realated to the topic you chose!")
@app_commands.describe(theme="Enter your theme", questions="Choose how many questions you want.")
async def trivia(interaction: discord.Interaction, theme: str, questions: int):
    await interaction.response.defer()

    try:
        client = Client()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Create {questions} random trivia about {theme} uestions with answers. Format as 'Q: question' and 'A: answer'."}]
        )

        ai_response = response.choices[0].message.content

        trivia_data = extract_trivia(ai_response)

        if not trivia_data:
            await interaction.followup.send("I couldn't generate trivia questions. Please try again.")
            return

        await interaction.followup.send("Let's start the trivia! Answer each question as they appear.")

        for idx, trivia in enumerate(trivia_data):
            question = trivia['question']
            answer = trivia['answer']

            await interaction.followup.send(f"**{question}**")

            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel

            try:
                user_response = await bot.wait_for('message', check=check, timeout=30.0)

                if user_response.content.strip().lower() == answer.strip().lower().replace("a:", ""):
                    await interaction.followup.send("✅ Correct!")
                else:
                    await interaction.followup.send(f"❌ Incorrect! The correct answer is: **{answer.replace('A:', '').strip()}**")

            except asyncio.TimeoutError:
                await interaction.followup.send(f"⏳ Time's up! The correct answer was: **{answer.replace('A:', '').strip()}**")

    except Exception as e:
        await interaction.followup.send(f"Something went wrong: {str(e)}")


def extract_trivia(ai_response):
    lines = ai_response.split("\n")
    questions_and_answers= []
    
    current_question = ""
    current_answer = ""
    
    for line in lines:
        if "Q:" in line:
            current_question = line.strip()
        elif "A:" in line:
            current_answer = line.strip()
            questions_and_answers.append({"question": current_question, "answer": current_answer})
            current_question = ""
            current_answer = ""
    
    return questions_and_answers

bot.run(TOKEN)
