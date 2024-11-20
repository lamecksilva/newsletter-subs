import os

import boto3
import mysql.connector
from dotenv import load_dotenv
from flask import Flask, jsonify, request

# loading variables from .env file
load_dotenv()

app = Flask(__name__)

# Configurações de banco de dados
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

# Configurar SES Client
SES_REGION = os.getenv("SES_REGION")  # Altere para sua região do SES
SES_SENDER_EMAIL = os.getenv("SES_SENDER_EMAIL")  # E-mail verificado no SES
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

ses_client = boto3.client(
    "ses",
    region_name=SES_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)


def get_db_connection():
    return mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
    )


@app.route("/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    try:
        # Salvar no banco de dados
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO newsletter_emails (email) VALUES (%s)", (email,))
        conn.commit()
        cursor.close()
        conn.close()

        # Enviar e-mail de confirmação pelo SES
        subject = "Confirmação de Inscrição - Newsletter"
        body = f"""
        <html>
            <body>
                <h1>Obrigado por se inscrever!</h1>
                <p>Seu email ({email}) foi cadastrado com sucesso na nossa newsletter.</p>
            </body>
        </html>
        """

        ses_client.send_email(
            Source=SES_SENDER_EMAIL,
            Destination={"ToAddresses": [email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": body, "Charset": "UTF-8"},
                },
            },
        )

        return jsonify({"message": "Email cadastrado com sucesso!"}), 201
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def hello():
    return jsonify({"message": "Newsletter Subs"})


@app.route("/emails", methods=["GET"])
def get_emails():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM newsletter_emails")
        emails = [row for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        print(emails)
        return jsonify({"emails": emails}), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8500)
