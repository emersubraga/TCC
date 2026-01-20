import qrcode
from django.core.files import File
from io import BytesIO

def gerar_qr_code(animal):
    url = f"http://192.168.3.113:8000/animal/{animal.id}/"

    qr = qrcode.make(url)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')

    animal.qr_code.save(
        f"animal_{animal.id}.png",
        File(buffer),
        save=True
    )
