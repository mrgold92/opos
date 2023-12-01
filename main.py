import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
from supabase import Client


load_dotenv()



def obtener_datos(url):
    # Enviar solicitud HTTP
    req = requests.get(url)
    # Parsear el contenido HTML
    soup = BeautifulSoup(req.text, "html.parser")
    # Buscando el 'ul' con la clase 'listado-menu'
    ul_element = soup.find('ul', class_='listado-menu')

    # Encontrando todos los 'li' dentro de este 'ul'
    specific_li_texts = []
    if ul_element:  # Verificando si el elemento 'ul' existe
        specific_li_elements = ul_element.find_all('li')
        specific_li_texts = [li.get_text(strip=True)
                             for li in specific_li_elements]

    return specific_li_texts


def conexion():
    # Conexión a la base de datos
    url: str = os.getenv("DATABASE_URL")
    key: str = os.getenv("DATABASE_KEY")
    supabase: Client = Client(url, key)
    
    return supabase

def insertar_datos(conn, total, texto):
    # Insertar los datos en la base de datos
    response = conn.table('datos').insert(
        {'total': total, 'texto': texto}).execute()
    print(response)



def mostrar_datos(conn):
     response = conn.table('datos').select('*').execute()
     print(response)


def comprobar_numero(conn, numero):
    # comprobar si el número ya existe en la base de datos 
    response = conn.table('datos').select('total').eq('total', numero).execute()
    return response



def enviar_correo(texto):
    
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    destinatarios = os.getenv("DESTINATARIOS").split(',')
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email_user, email_password)

    # Crear el mensaje
    mensaje = MIMEMultipart()
    mensaje['From'] = email_user
    mensaje['To'] = ",".join(destinatarios)
    mensaje['Subject'] = 'Cambio en la página web de las opos'

    # Cuerpo del mensaje
    html = """
    <html>
    <head></head>
    <body>
    <p>Ha habido un cambio en la página web de las opciones de la Seguridad Social.<br>
    El nuevo elemento es: <b>{}</b><br>
    Puedes verlo en <a href='https://www.seg-social.es/wps/portal/wss/internet/InformacionUtil/9950/cd623d58-d5fb-4d8a-a68f-79f1d65fa61c/73a17349-a805-4d22-aa3b-6dce34da715a/2bcddc79-8452-475b-aad0-96f72201c268#180423GT'>este enlace</a>.</p>
    </body>
    </html>
    """.format(texto)
    mensaje.attach(MIMEText(html, 'html', 'utf-8'))

    # Enviar el correo
    server.sendmail(email_user,
                    destinatarios, mensaje.as_string())
    server.quit()


url = "https://www.seg-social.es/wps/portal/wss/internet/InformacionUtil/9950/cd623d58-d5fb-4d8a-a68f-79f1d65fa61c/73a17349-a805-4d22-aa3b-6dce34da715a/2bcddc79-8452-475b-aad0-96f72201c268#180423GT"

# Nos conectamos a la base de datos
conn = conexion()

# Llamada a la función y mostrar resultados
datos = obtener_datos(url)
total = len(datos)
ultimoTexto = datos[-1]


# Comprobamos si el número de datos ya existe en la base de datos
existe = comprobar_numero(conn, total)


#Si no hay datos en la base de datos
if existe.data == []:
    # Insertamos los datos en la base de datos
    insertar_datos(conn, total, ultimoTexto)
    print("El dato ha sido insertado por primera vez")
    enviar_correo(ultimoTexto)
else:
    # Obtenemos el primer dato
    dato = existe.data[0]['total']
    # Es igual?
    if total == dato:
        # no hacemos nada
        print("El dato no ha cambiado")
        pass
    else:
        # Actualizamos el dato
        response = conn.table('datos').update({'total': total, 'texto': ultimoTexto}).eq('total', dato).execute()
        print("El dato ha sido actualizado")
        mostrar_datos(conn)
        # Enviar correo electrónico
        enviar_correo(ultimoTexto)
 