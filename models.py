from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

DATABASE = 'database.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            tentativas INTEGER NOT NULL DEFAULT 0,
            bloqueado INTEGER NOT NULL DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chamados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Aberto',
            usuario_id INTEGER NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    
    cursor.execute("SELECT * FROM usuarios WHERE username = 'admin'")
    if not cursor.fetchone():
        senha_hash = generate_password_hash('cavasblindado')
        cursor.execute("INSERT INTO usuarios (username, password, role) VALUES (?, ?, ?)", ('admin', senha_hash, 'admin'))
        
    conn.commit()
    conn.close()

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    
    if commit:
        conn.commit()
        conn.close()
        return True
        
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def cadastrar_usuario(username, password):
    senha_criptografada = generate_password_hash(password)
    return query_db('INSERT INTO usuarios (username, password, role) VALUES (?, ?, ?)', 
                    [username, senha_criptografada, 'user'], commit=True)

def verificar_login(username, password):
    user = query_db('SELECT * FROM usuarios WHERE username = ?', [username], one=True)
    
    if not user:
        return None, "inexistente"
        
    if user['bloqueado'] == 1:
        return None, "bloqueado"
        
    if check_password_hash(user['password'], password):
        query_db('UPDATE usuarios SET tentativas = 0 WHERE id = ?', [user['id']], commit=True)
        return user, "sucesso"
    else:
        novas_tentativas = user['tentativas'] + 1
        if novas_tentativas >= 3:
            query_db('UPDATE usuarios SET tentativas = ?, bloqueado = 1 WHERE id = ?', [novas_tentativas, user['id']], commit=True)
            return None, "bloqueado_agora"
        else:
            query_db('UPDATE usuarios SET tentativas = ? WHERE id = ?', [novas_tentativas, user['id']], commit=True)
            return None, "erro_senha"

def atualizar_status_chamado(id_chamado, novo_status):
    return query_db('UPDATE chamados SET status = ? WHERE id = ?', [novo_status, id_chamado], commit=True)

def excluir_chamado_db(id_chamado):
    return query_db('DELETE FROM chamados WHERE id = ?', [id_chamado], commit=True)