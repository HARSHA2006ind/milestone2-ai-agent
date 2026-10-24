
import json
import urllib.request
import urllib.error
import re

# Ollama local model settings
MODEL = "qwen2.5:3b"
OLLAMA_URL = "http://localhost:11434/api/chat"

FALLBACK = (
    "The provided context does not contain enough information "
    "to answer this question."
)

# Tool 1: Read the supplied context
def get_context():
    with open("context.json", "r", encoding="utf-8") as file:
        return json.load(file)


# Tool 2: Search the context for relevant information
def search_context(question, context):
    context_text = json.dumps(context, ensure_ascii=False).lower()

    stop_words = {
        "what", "who", "when", "where", "why", "how",
        "is", "are", "was", "were", "the", "a", "an",
        "of", "in", "on", "to", "for", "does", "do",
        "this", "that", "it", "and", "or", "my", "me",
        "about", "tell", "please", "can", "you"
    }

    aliases = {
        "requirements": "requirement",
        "require": "requirement",
        "requires": "requirement",
        "required": "requirement",
        "created": "creator",
        "creator": "creator",
        "author": "creator",
        "testing": "repeatability",
        "tests": "test"
    }

    def normalize(word):
        word = aliases.get(word, word)
        if word.endswith("s") and len(word) > 4:
            word = word[:-1]
        return word

    question_words = [
        normalize(word)
        for word in re.findall(r"[a-zA-Z]+", question.lower())
        if word not in stop_words
    ]

    context_words = {
        normalize(word)
        for word in re.findall(r"[a-zA-Z]+", context_text)
    }

    matched_words = [
        word for word in question_words
        if word in context_words
    ]

    # Do not answer questions about an unknown creator.
    creator_question = any(
        word in question.lower()
        for word in ["who created", "who is the creator",
                     "who is the author", "who developed"]
    )

    creator_information_exists = any(
        word in context_text
        for word in ["creator", "created_by", "author", "developer"]
    )

    if creator_question and not creator_information_exists:
        return {"supported": False, "evidence": None}

    # Require relevant matches rather than guessing.
    if len(set(matched_words)) < 2:
        return {"supported": False, "evidence": None}

    return {"supported": True, "evidence": context}


# Ask Ollama to answer using the retrieved evidence
def ask_model(question, evidence):
    prompt = f"""
Answer the question using ONLY the supplied context.
Do not add facts from your own knowledge.
If the context does not answer the question, reply exactly:
{FALLBACK}

Keep the answer short and clear.

Context:
{json.dumps(evidence, ensure_ascii=False)}

Question: {question}

Answer:
"""

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0
        }
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["message"]["content"].strip()


# Run the agent and record which tools it uses
def answer_question(question):
    context = get_context()
    search_result = search_context(question, context)

    tools_used = ["get_context", "search_context"]

    if not search_result["supported"]:
        return FALLBACK, tools_used

    answer = ask_model(question, search_result["evidence"])
    return answer, tools_used


# Compare repeated answers
def check_repeatability(question):
    answer1, _ = answer_question(question)
    answer2, _ = answer_question(question)

    normalized1 = " ".join(answer1.lower().split())
    normalized2 = " ".join(answer2.lower().split())

    print("\nFirst answer: ", answer1)
    print("Second answer:", answer2)

    if normalized1 == normalized2:
        print("Repeatability check: PASS")
    else:
        print("Repeatability check: FAIL")


# Main program
def main():
    print("AI Agent - Milestone 2")
    print("Ask a question, type 'repeat' to test repeatability,")
    print("or type 'exit' to quit.")

    while True:
        question = input("\nYou: ").strip()

        if question.lower() == "exit":
            print("Agent: Goodbye!")
            break

        if not question:
            continue

        if question.lower() == "repeat":
            test_question = input("Enter the question to repeat: ").strip()
            if test_question:
                check_repeatability(test_question)
            continue

        try:
            answer, tools_used = answer_question(question)
            print("Agent:", answer)
            print("Tools used:", tools_used)

        except FileNotFoundError:
            print("Error: context.json was not found.")
            print("Keep context.json and agent.py in the same folder.")

        except urllib.error.URLError:
            print("Error: Ollama is not running.")
            print("Start Ollama and try again.")

        except Exception as error:
            print("Error:", error)


if __name__ == "__main__":
    main()
