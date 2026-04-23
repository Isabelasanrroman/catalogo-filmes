import os
import hashlib
from flask import Flask, request, jsonify, render_template, redirect, url_for
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename
from database import get_connection

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def gerar_nome_unico(filename):
    ext = filename.rsplit(".", 1)[1].lower()
    hash_nome = hashlib.sha256((filename + str(os.urandom(16))).encode()).hexdigest()
    return f"{hash_nome}.{ext}"


# Listar todos os filmes
@app.route('/', methods=['GET'])
def listar_filmes():
    sql = "SELECT * FROM filmes"
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql)
        filmes = cursor.fetchall()
        conn.close()
        return render_template("index.html", filmes=filmes)
    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": "erro ao listar filmes"}), 500


@app.route("/novo", methods=["GET", "POST"])
def novo_filme():
    sql = "INSERT INTO filmes (titulo, genero, ano, url_capa) VALUES (%s, %s, %s, %s)"
    try:
        if request.method == "POST":
            titulo = request.form["titulo"]
            genero = request.form["genero"]
            ano = request.form["ano"]

            arquivo = request.files.get("capa")

            if not arquivo or arquivo.filename == "":
                return render_template("erro.html", erro="Nenhuma imagem foi enviada!")

            if not allowed_file(arquivo.filename):
                return render_template("erro.html", erro="Extensão inválida! Use apenas PNG, JPG ou JPEG.")

            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

            nome_seguro = secure_filename(arquivo.filename)
            nome_final = gerar_nome_unico(nome_seguro)

            caminho_completo = os.path.join(app.config["UPLOAD_FOLDER"], nome_final)
            arquivo.save(caminho_completo)

            caminho_banco = f"uploads/{nome_final}"

            params = [titulo, genero, ano, caminho_banco]

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            conn.close()

            return redirect(url_for("listar_filmes"))

        return render_template("novo_filme.html")

    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": "erro ao cadastrar filme"}), 500


@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar_filme(id):
    try:
        conn = get_connection()

        if request.method == "POST":
            titulo = request.form["titulo"]
            genero = request.form["genero"]
            ano = request.form["ano"]

            arquivo = request.files.get("capa")

            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM filmes WHERE id = %s", [id])
            filme_atual = cursor.fetchone()

            if filme_atual is None:
                conn.close()
                return redirect(url_for("listar_filmes"))

            caminho_banco = filme_atual["url_capa"]

            # Se enviou nova imagem, troca
            if arquivo and arquivo.filename != "":
                if not allowed_file(arquivo.filename):
                    conn.close()
                    return render_template("erro.html", erro="Extensão inválida! Use apenas PNG, JPG ou JPEG.")

                os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

                nome_seguro = secure_filename(arquivo.filename)
                nome_final = gerar_nome_unico(nome_seguro)

                caminho_completo = os.path.join(app.config["UPLOAD_FOLDER"], nome_final)
                arquivo.save(caminho_completo)

                caminho_banco = f"uploads/{nome_final}"

            sql_update = """
                UPDATE filmes 
                SET titulo = %s, genero = %s, ano = %s, url_capa = %s 
                WHERE id = %s
            """
            params = [titulo, genero, ano, caminho_banco, id]

            cursor2 = conn.cursor()
            cursor2.execute(sql_update, params)
            conn.commit()
            conn.close()

            return redirect(url_for("listar_filmes"))

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM filmes WHERE id = %s", [id])
        filme = cursor.fetchone()
        conn.close()

        if filme is None:
            return redirect(url_for("listar_filmes"))

        return render_template("editar_filme.html", filme=filme)

    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": "erro ao editar filme"}), 500


@app.route("/deletar/<int:id>", methods=["POST"])
def deletar_filme(id):
    try:
        conn = get_connection()

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT url_capa FROM filmes WHERE id = %s", [id])
        filme = cursor.fetchone()

        if filme and filme["url_capa"]:
            caminho_arquivo = os.path.join("static", filme["url_capa"])
            if os.path.exists(caminho_arquivo):
                os.remove(caminho_arquivo)

        cursor2 = conn.cursor()
        cursor2.execute("DELETE FROM filmes WHERE id = %s", [id])
        conn.commit()
        conn.close()

        return redirect(url_for("listar_filmes"))

    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": "erro ao deletar filme"}), 500


if __name__ == '__main__':
    app.run(debug=True)