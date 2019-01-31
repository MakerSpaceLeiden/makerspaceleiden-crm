import io
import datetime
from collections import namedtuple
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm, inch


MM_2_UNITS = mm/inch*72
pt = inch/27

DOCUMENT_SIZE = (210*MM_2_UNITS, 297*MM_2_UNITS)

FONT_SIZE = 10  # Implicitly "pt"

LEADING = FONT_SIZE * 2

MARGIN_LEFT = 30 * mm

MARGIN_TOP = 50 * mm


WAIVER_TEXT = '''
Ondergetekende verklaart bekend te zijn met het risico van het gebruik van 
apparatuur die ernstig blijvend letsel kan veroorzaken met
eventueel de dood tot gevolg.

Ondergetekende verklaart zich te houden aan de veiligheidsinstructies en richtlijnen.

Ondergetekende vrijwaart het bestuur en de deelnemers van MakerSpace Leiden 
van aansprakelijkheid door hem/haar zelf, dan wel door derden.

Ondertekend:

Leiden, datum:   {data.date}


Deelnemer:       {data.user_name}



Handtekening:     ______________________________
'''

FormData = namedtuple('FormData', 'date user_name')


def generate_waiverform_fd(user_name):
    form_data = FormData(
        date = datetime.datetime.now().strftime('%d/%m/%Y'),
        user_name = user_name,
    )

    fd = io.BytesIO()
    c = canvas.Canvas(fd, pagesize=DOCUMENT_SIZE, bottomup=0)
    c.setFont("Helvetica", FONT_SIZE)
    y = MARGIN_TOP
    for idx, line in enumerate(WAIVER_TEXT.strip().split('\n')):
        if line.strip():
            c.drawString(MARGIN_LEFT, y, line.format(data=form_data))
        y += LEADING

    c.showPage()
    c.save()
    fd.seek(0)
    return fd
