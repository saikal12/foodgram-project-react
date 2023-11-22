from django.http import HttpResponse
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

FILE_NAME = 'shopping-list.txt'


def to_pdf(self, ingredients):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename={FILE_NAME}'
    pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
    c = canvas.Canvas(response)
    c.setFont('DejaVu', 17)
    WIDTH = 60
    HEIGHT = 770
    c.drawString(WIDTH, HEIGHT, "  Ингредиенты: ")
    for new_string in ingredients:
        HEIGHT -= 30
        name = new_string['ingredient__name']
        measurement_unit = new_string['ingredient__measurement_unit']
        amount = new_string['sum']
        string = f'{name}  -  {amount}({measurement_unit})'
        c.drawString(WIDTH, HEIGHT, string)
    c.showPage()
    c.save()
    return response
