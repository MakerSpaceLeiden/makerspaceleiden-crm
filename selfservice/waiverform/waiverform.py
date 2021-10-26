import io
import os
import datetime
from collections import namedtuple
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm, inch
import PyPDF2
import qrcode


MM_2_UNITS = mm / inch * 72
pt = inch / 27

DOCUMENT_SIZE = (210 * MM_2_UNITS, 297 * MM_2_UNITS)

FONT_SIZE = 11  # Implicitly "pt"

LEADING = FONT_SIZE * 1.2

MARGIN_LEFT = 1 * inch
MARGIN_LEFT_DATE = 140 * mm
MARGIN_TOP = 100 * mm

NAME_COORDINATES = (89 * mm, 228 * mm)

QR_CODE_COORDS = (20 * mm, 200 * mm, 40 * mm, 40 * mm)


WAIVER_TEXT = """
Leiden, {data.date}

Ref: waiver: waiver-2019-01-v1.01/{data.user_id}

{data.user_name} verklaart op {data.date} bekend te zijn met het risico van het gebruik van 
apparatuur die ernstig blijvend letsel kan veroorzaken met eventueel de dood tot gevolg.

{data.user_name} verklaart zich te houden aan de veiligheidsinstructies en richtlijnen.

{data.user_name} vrijwaart het bestuur en de deelnemers van MakerSpace Leiden van
aansprakelijkheid door hem/haar zelf, dan wel door derden.
"""

FormData = namedtuple("FormData", "date user_id user_name")

template_filepath = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "waiverform template.pdf"
)


def generate_waiverform_fd(user_id, user_name, confirmation_url):
    form_data = FormData(
        date=datetime.datetime.now().strftime("%d/%m/%Y"),
        user_id=user_id,
        user_name=user_name,
    )

    # Read template page from PDF
    reader = PyPDF2.PdfFileReader(template_filepath, strict=False)
    template_page = reader.getPage(0)

    # Generate overlay text with reportlab
    fd = _generate_overlay(form_data, confirmation_url)
    overlay_page = PyPDF2.PdfFileReader(fd, strict=False).getPage(0)

    # Merge the pages
    writer = PyPDF2.PdfFileWriter()
    new_page = writer.addBlankPage(*DOCUMENT_SIZE)
    new_page.mergePage(template_page)
    new_page.mergePage(overlay_page)

    # Write the result to an in-memory file
    fd = io.BytesIO()
    writer.write(fd)
    fd.seek(0)
    return fd


def _generate_overlay(form_data, confirmation_url):
    fd = io.BytesIO()
    c = canvas.Canvas(fd, pagesize=DOCUMENT_SIZE, bottomup=0)

    # Waiver text
    c.setFont("Helvetica", FONT_SIZE)
    y = MARGIN_TOP
    for idx, line in enumerate(WAIVER_TEXT.strip().split("\n")):
        if line.strip():
            c.drawString(
                MARGIN_LEFT if idx > 0 else MARGIN_LEFT_DATE,
                y,
                line.format(data=form_data),
            )
        y += LEADING

    # Date
    c.drawString(*NAME_COORDINATES, form_data.user_name)

    # QR code
    qrcode_img = qrcode.make(confirmation_url)
    c.drawInlineImage(qrcode_img, *QR_CODE_COORDS)

    c.showPage()
    c.save()
    fd.seek(0)
    return fd
