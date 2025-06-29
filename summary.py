from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas

def create_summary_prompt(chat_history):
    summary_lines = []
    for idx, chat in enumerate(chat_history, 1):
        summary_lines.append(f"<b>{idx}. You:</b> {chat['user_input']}")
        summary_lines.append(f"<b>Agent:</b> {chat['agent_response']}")
        summary_lines.append("")  # blank line between exchanges
    return "\n".join(summary_lines)

def add_footer(canvas, doc):
    # Header
    header_text = "DSW Hackathon Project by Kshitij Varma"
    canvas.saveState()
    canvas.setFont('Helvetica-Bold', 14)
    canvas.setFillColor(colors.darkblue)
    width, height = letter
    canvas.drawString(72, height - 40, header_text)

    footer_text = "LinkedIn: https://www.linkedin.com/in/k5hitij-varma   |   GitHub: https://github.com/k5hitijj/DSW_Hackathon"
    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    width, height = letter
    canvas.setFillColor(colors.grey)
    canvas.drawString(72, 30, footer_text)
    canvas.restoreState()

def create_pdf(summary_text, filename="chat_summary.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=72, leftMargin=72,
        topMargin=72, bottomMargin=72
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Chat',
        fontSize=11,
        leading=15,
        spaceAfter=10,
    ))

    flowables = []

    flowables.append(Paragraph("<b>📄 Conversation Summary</b>", styles['Title']))
    flowables.append(Spacer(1, 0.3 * inch))

    for line in summary_text.strip().split("\n"):
        flowables.append(Paragraph(line, styles['Chat']))

    doc.build(flowables, onFirstPage=add_footer, onLaterPages=add_footer)