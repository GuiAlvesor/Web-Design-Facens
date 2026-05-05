import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)

def enviar_email_boas_vindas(nome: str, email_destino: str):
    mensagem = Mail(
        from_email=os.environ.get("DEFAULT_FROM_EMAIL"),
        to_emails=email_destino,
        subject="Bem-vindo à Lume 3D!",
        html_content=f"""
            <h2>Olá, {nome}!</h2>
            <p>Seu cadastro foi realizado com sucesso.</p>
            <p>Obrigado por se registrar na nossa loja de produtos 3D.</p>
        """
    )

    try:
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        response = sg.send(mensagem)
        logger.info(f"Email enviado para {email_destino} - status {response.status_code}")
        return response.status_code
    except Exception as e:
        logger.error(f"Falha ao enviar email para {email_destino}: {e}")
        return None