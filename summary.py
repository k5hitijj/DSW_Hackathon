from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_summary_prompt(chat_history):
    summary_lines = []
    for idx, chat in enumerate(chat_history, 1):
        summary_lines.append(f"{idx}. User: {chat['user_input']}")
        summary_lines.append(f"   Agent: {chat['agent_response']}")
    return "\n".join(summary_lines)


def create_pdf(summary_text, filename="chat_summary.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    text = c.beginText(40, height - 50)
    text.setFont("Helvetica", 12)
    text.textLine("Conversation Summary")

    for line in summary_text.split("\n"):
        text.textLine(line)

    c.drawText(text)
    c.showPage()
    c.save()
