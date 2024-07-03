import os
from flask import Flask, request, render_template, redirect, url_for, flash
import requests
from bs4 import BeautifulSoup
from groq import Groq

# Load environment variables from .env file

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

# Initialize Groq client
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("wiki_url")
        if not url:
            flash("Please provide a valid Wikipedia URL.", "error")
            return redirect(url_for("index"))

        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            flash(f"Error fetching URL: {e}", "error")
            return redirect(url_for("index"))

        soup = BeautifulSoup(response.text, "html.parser")
        article = soup.find_all("div", {"class": "mw-parser-output"})
        text = ""

        for articles in article:
            content = articles.find_all("p")
            for p in content:
                text += p.text

        prompt = f"Summarise the text below in no more than 3 paragraphs: {text}"

        try:
            summary_response = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="llama3-8b-8192",
            )
            summary = summary_response.choices[0].message.content
        except Exception as e:
            flash(f"Error summarizing text: {e}", "error")
            return redirect(url_for("index"))

        refs = soup.find_all("ol", {"class": "references"})
        references = ""
        for ref in refs:
            references += ref.text.replace("^ ", "")

        return render_template("index.html", summary=summary, references=references, url=url)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
