from flask import Flask, render_template, request, redirect, url_for, session, flash
import models
import sqlite3
import re

app = Flask(__name__)
app.secret_key = 'chave_secreta_super_segura_para_sessoes'

models.init_db()

def validar_senha_forte(password):
    if len(password) < 8:
        return False
    if not re.search("[a-z]", password):
        return False
    if not re.search("[A-Z]", password):
        return False
    if not re.search("[0-9]", password):
        return False
    if not re.search("[_@$!%*?&]", password):
        return False
    return True

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username'].strip()
    password = request.form['password'].strip()
    
    user, status = models.verificar_login(username, password)
    
    if status == "sucesso":
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        return redirect(url_for('dashboard'))
    elif status == "bloqueado" or status == "bloqueado_agora":
        flash("Errou a senha 3 vezes? Parabéns, você conseguiu bloquear a conta! Vá tomar um café e implore para a TI te desbloquear agora... 🔒☕", "danger")
    else:
        flash("Errou o usuário ou a senha. Será que o Caps Lock está ligado ou você só esqueceu como digita mesmo? 🤔", "danger")
        
    return redirect(url_for('index'))

@app.route('/cadastro', methods=['POST'])
def cadastro():
    username = request.form['username'].strip()
    password = request.form['password'].strip()
    
    if not username:
        flash("Enviar usuário em branco? O sistema é seguro, mas não lê mentes ainda.", "danger")
        return redirect(url_for('index'))
        
    if not validar_senha_forte(password):
        flash("Que senha horrorosa! O grupo rival vai adivinhar isso em dois segundos. Coloque pelo menos 8 caracteres, uma maiúscula, uma minúscula, um número e um caractere especial! Se vira. 🛡️🤡", "danger")
        return redirect(url_for('index'))
        
    try:
        models.cadastrar_usuario(username, password)
        flash("Milagre! Cadastro realizado. Agora tente acertar as credenciais para logar.", "success")
    except sqlite3.IntegrityError:
        flash("Esse usuário já existe. Seja um pouco mais criativo e tente outro nome! 🙄", "warning")
        
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
        
    if session['role'] == 'admin':
        chamados = models.query_db('SELECT chamados.*, usuarios.username FROM chamados JOIN usuarios ON chamados.usuario_id = usuarios.id')
    else:
        chamados = models.query_db('SELECT * FROM chamados WHERE usuario_id = ?', [session['user_id']])
        
    return render_template('dashboard.html', chamados=chamados)

@app.route('/detalhe', methods=['GET', 'POST'])
@app.route('/detalhe/<int:id_chamado>', methods=['GET'])
def detalhe(id_chamado=None):
    if 'user_id' not in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        titulo = request.form['titulo'].strip()
        descricao = request.form['descricao'].strip()
        
        if not titulo or not descricao:
            flash("Preencha todos os campos! A TI não trabalha com telepatia.", "danger")
            return redirect(url_for('dashboard'))
            
        models.query_db('INSERT INTO chamados (titulo, descricao, usuario_id) VALUES (?, ?, ?)', 
                        [titulo, descricao, session['user_id']], commit=True)
        flash("Chamado enviado. Sente-se e espere (bastante), porque a TI está ocupada jogando ludo. 🛠️⏳", "success")
        return redirect(url_for('dashboard'))
        
    if id_chamado:
        chamado_dados = models.query_db('SELECT * FROM chamados WHERE id = ?', [id_chamado], one=True)
        
        if not chamado_dados:
            flash("Chamado sumiu no limbo do servidor.", "danger")
            return redirect(url_for('dashboard'))
            
        if session['role'] != 'admin' and chamado_dados['usuario_id'] != session['user_id']:
            flash("Alto lá, bisbilheteiro! Tentando espiar o chamado dos outros mudando o ID na URL? Bloqueado com sucesso! 🛑🕵️‍♂️", "danger")
            return redirect(url_for('dashboard'))
            
        return render_template('detalhe.html', chamado=chamado_dados)
        
    return render_template('detalhe.html', chamado=None)

@app.route('/chamado/atender/<int:id_chamado>')
def atender_chamado(id_chamado):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    if session['role'] != 'admin':
        flash("Você não tem roupa de técnico para fazer isso. Tentativa de invasão detectada e ignorada com deboche! 🛑", "danger")
        return redirect(url_for('dashboard'))
        
    models.atualizar_status_chamado(id_chamado, 'Atendido ✅')
    flash(f"Chamado #{id_chamado} foi marcado como Atendido. Milagres acontecem!", "success")
    return redirect(url_for('dashboard'))

@app.route('/chamado/excluir/<int:id_chamado>')
def excluir_chamado(id_chamado):
    if 'user_id' not in session:
        return redirect(url_for('index'))
        
    chamado_dados = models.query_db('SELECT * FROM chamados WHERE id = ?', [id_chamado], one=True)
    
    if not chamado_dados:
        flash("Esse chamado já deve ter sido apagado por outra pessoa... ou nunca existiu.", "danger")
        return redirect(url_for('dashboard'))
        
    if session['role'] != 'admin' and chamado_dados['usuario_id'] != session['user_id']:
        flash("Tentou apagar o chamado alheio na malandragem? Deu ruim, o sistema é blindado! 🕵️‍♂️❌", "danger")
        return redirect(url_for('dashboard'))
        
    models.excluir_chamado_db(id_chamado)
    flash(f"Chamado #{id_chamado} evaporou do sistema com sucesso.", "info")
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)