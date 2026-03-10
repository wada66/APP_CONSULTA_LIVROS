from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Tabelas principais
class Setor(db.Model):
    __tablename__ = 'setor'
    id_setor = db.Column(db.Integer, primary_key=True)
    nome_setor = db.Column(db.String(200))
    livros = db.relationship('Livro', backref='setor', lazy=True)

class Local(db.Model):
    __tablename__ = 'local'
    id_local = db.Column(db.Integer, primary_key=True)
    nome_local = db.Column(db.String(40))
    livros = db.relationship('Livro', backref='local', lazy=True)

class Assunto(db.Model):
    __tablename__ = 'assunto'
    id_assunto = db.Column(db.Integer, primary_key=True)
    nome_assunto = db.Column(db.String(300))
    livros = db.relationship('Livro', backref='assunto', lazy=True)

class Livro(db.Model):
    __tablename__ = 'livro'
    id_livro = db.Column(db.Integer, primary_key=True)
    tipo_livro = db.Column(db.String(1))
    idioma_livro = db.Column(db.String(10))
    titulo_livro = db.Column(db.String(500))
    edicao_livro = db.Column(db.String(13))
    n_chamada_livro = db.Column(db.String(40))
    data_livro = db.Column(db.Date)
    colacao_paginas_livro = db.Column(db.String(20))
    colacao_volume_tomo_livro = db.Column(db.String(30))
    serie_livro = db.Column(db.String(100))
    conteudo_livro = db.Column(db.String(1000))
    notas_gerais_livro = db.Column(db.String(1000))
    outros_formatos_disponiveis_livro = db.Column(db.String(40))
    aquisicao_livro = db.Column(db.String(60))
    fonte_livro = db.Column(db.String(300))
    id_setor = db.Column(db.Integer, db.ForeignKey('setor.id_setor'))
    id_local = db.Column(db.Integer, db.ForeignKey('local.id_local'))
    id_assunto = db.Column(db.Integer, db.ForeignKey('assunto.id_assunto'))

    # Relacionamentos muitos-para-muitos
    autores = db.relationship('Autor', secondary='livro_autor', backref='livros')
    executores = db.relationship('Executor', secondary='livro_executor', backref='livros')
    editores = db.relationship('Editor', secondary='livro_editor', backref='livros')
    areas_geograficas = db.relationship('AreaGeografica', secondary='livro_area_geografica', backref='livros')

# Tabelas auxiliares
class Autor(db.Model):
    __tablename__ = 'autor'
    id_autor = db.Column(db.Integer, primary_key=True)
    nome_autor = db.Column(db.String(200))
    tipo_autor = db.Column(db.String(40))

class Executor(db.Model):
    __tablename__ = 'executor'
    id_executor = db.Column(db.Integer, primary_key=True)
    nome_executor = db.Column(db.String(200))

class Editor(db.Model):
    __tablename__ = 'editor'
    id_editor = db.Column(db.Integer, primary_key=True)
    nome_editor = db.Column(db.String(200))

class AreaGeografica(db.Model):
    __tablename__ = 'area_geografica'
    id_area_geografica = db.Column(db.Integer, primary_key=True)
    nome_area_geografica = db.Column(db.String(40))

# Tabelas de junção
class LivroAutor(db.Model):
    __tablename__ = 'livro_autor'
    id_livro_autor = db.Column(db.Integer, primary_key=True)
    id_livro = db.Column(db.Integer, db.ForeignKey('livro.id_livro'))
    id_autor = db.Column(db.Integer, db.ForeignKey('autor.id_autor'))

class LivroExecutor(db.Model):
    __tablename__ = 'livro_executor'
    id_livro_executor = db.Column(db.Integer, primary_key=True)
    id_livro = db.Column(db.Integer, db.ForeignKey('livro.id_livro'))
    id_executor = db.Column(db.Integer, db.ForeignKey('executor.id_executor'))

class LivroEditor(db.Model):
    __tablename__ = 'livro_editor'
    id_livro_editor = db.Column(db.Integer, primary_key=True)
    id_livro = db.Column(db.Integer, db.ForeignKey('livro.id_livro'))
    id_editor = db.Column(db.Integer, db.ForeignKey('editor.id_editor'))

class LivroAreaGeografica(db.Model):
    __tablename__ = 'livro_area_geografica'
    id_livro_area_geografica = db.Column(db.Integer, primary_key=True)
    id_livro = db.Column(db.Integer, db.ForeignKey('livro.id_livro'))
    id_area_geografica = db.Column(db.Integer, db.ForeignKey('area_geografica.id_area_geografica'))