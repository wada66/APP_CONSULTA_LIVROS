import re
from flask import Flask, render_template, request, jsonify
from config import Config
from models import LivroEditor, LivroExecutor, db, Livro, Setor, Local, Assunto, Executor, Autor, Editor, AreaGeografica, LivroAutor
from datetime import datetime
from sqlalchemy import or_, extract

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.route('/')
def index():
    """Página inicial"""
    try:
        total_livros = Livro.query.count()
        total_autores = Autor.query.count()
    except Exception:
        total_livros = 0
        total_autores = 0
    
    return render_template('index.html', 
                          total_livros=total_livros,
                          total_autores=total_autores)

@app.route('/livros', methods=['GET'])
def listar_livros():
    """Lista livros com filtros - não carrega nada inicialmente"""
    
    # Carregar dados para os selects (sempre necessários)
    locais = Local.query.order_by(Local.nome_local).all()
    setores = Setor.query.order_by(Setor.nome_setor).all()
    assuntos = Assunto.query.order_by(Assunto.nome_assunto).all()
    executores = Executor.query.order_by(Executor.nome_executor).all()
    autores = Autor.query.order_by(Autor.nome_autor).all()
    editores = Editor.query.order_by(Editor.nome_editor).all()
    areas = AreaGeografica.query.order_by(AreaGeografica.nome_area_geografica).all()
    
    # Conteúdos distintos (para sugestão)
    conteudos = db.session.query(Livro.conteudo_livro).distinct().filter(Livro.conteudo_livro.isnot(None)).all()
    conteudos = [c[0] for c in conteudos if c[0]]
    
    # Inicializar lista vazia de livros
    livros = []
    filtros = {}
    
    # Verificar se há parâmetros de busca na URL
    has_filters = any([
        request.args.get('id_livro'),
        request.args.get('n_chamada'),
        request.args.get('titulo'),
        request.args.get('autor'),
        request.args.get('local_id'),
        request.args.get('setor_id'),
        request.args.get('assunto'),
        request.args.get('mes'),
        request.args.get('ano'),
        request.args.get('conteudo'),
        request.args.get('executor'),
        request.args.get('editor'),
        request.args.get('area_id')
    ])
    
    # Se houver filtros ou se for uma busca explícita (submit do formulário)
    if has_filters or request.args.get('buscar'):
        query = Livro.query
        
        # Filtro por ID
        if 'id_livro' in request.args and request.args['id_livro']:
            try:
                id_val = int(request.args['id_livro'])
                query = query.filter(Livro.id_livro == id_val)
                filtros['id_livro'] = request.args['id_livro']
            except ValueError:
                pass
        
        # Filtro por Número de Chamada
        if 'n_chamada' in request.args and request.args['n_chamada']:
            query = query.filter(Livro.n_chamada_livro.like(f"%{request.args['n_chamada']}%"))
            filtros['n_chamada'] = request.args['n_chamada']
        
        # Filtro por Título
        if 'titulo' in request.args and request.args['titulo']:
            titulo_busca = request.args['titulo'].strip()
            if titulo_busca:
                def criar_padrao_regex(palavra):
                    padrao = ''
                    for letra in palavra.lower():
                        if letra == 'a': padrao += '[aáàãâä]'
                        elif letra == 'e': padrao += '[eéèêë]'
                        elif letra == 'i': padrao += '[iíìîï]'
                        elif letra == 'o': padrao += '[oóòõôö]'
                        elif letra == 'u': padrao += '[uúùûü]'
                        elif letra == 'c': padrao += '[cç]'
                        else: padrao += re.escape(letra)
                    return padrao

                palavras = titulo_busca.split()
                condicoes = []
                for palavra in palavras:
                    if len(palavra) >= 2:
                        padrao = criar_padrao_regex(palavra)
                        try:
                            condicoes.append(Livro.titulo_livro.op('~*')(padrao))
                        except:
                            condicoes.append(Livro.titulo_livro.ilike(f"%{palavra}%"))
                if condicoes:
                    query = query.filter(*condicoes)
                filtros['titulo'] = titulo_busca
        
        # Filtro por Autor (busca textual inteligente)
        if 'autor' in request.args and request.args['autor']:
            termo = request.args['autor'].strip()
            if termo:
                def criar_padrao_regex(palavra):
                    padrao = ''
                    for letra in palavra.lower():
                        if letra == 'a': padrao += '[aáàãâä]'
                        elif letra == 'e': padrao += '[eéèêë]'
                        elif letra == 'i': padrao += '[iíìîï]'
                        elif letra == 'o': padrao += '[oóòõôö]'
                        elif letra == 'u': padrao += '[uúùûü]'
                        elif letra == 'c': padrao += '[cç]'
                        else: padrao += re.escape(letra)
                    return padrao

                palavras = termo.split()
                condicoes_autor = []

                for palavra in palavras:
                    if len(palavra) >= 2:
                        padrao = criar_padrao_regex(palavra)
                        try:
                            # Tenta usar regex do PostgreSQL
                            condicoes_autor.append(Autor.nome_autor.op('~*')(padrao))
                        except Exception:
                            # Fallback: ILIKE
                            condicoes_autor.append(Autor.nome_autor.ilike(f"%{palavra}%"))
                    else:
                        condicoes_autor.append(Autor.nome_autor.ilike(f"%{palavra}%"))

                if condicoes_autor:
                    # JOIN com a tabela Autor via livro_autor
                    subquery = db.session.query(LivroAutor.id_livro).join(
                        Autor, LivroAutor.id_autor == Autor.id_autor
                    ).filter(*condicoes_autor)
                    
                    query = query.filter(Livro.id_livro.in_(subquery))

                filtros['autor'] = termo
        
        # Filtro por Local
        if 'local_id' in request.args and request.args['local_id']:
            try:
                query = query.filter(Livro.id_local == int(request.args['local_id']))
                filtros['local_id'] = request.args['local_id']
            except ValueError:
                pass
        
        # Filtro por Setor
        if 'setor_id' in request.args and request.args['setor_id']:
            try:
                query = query.filter(Livro.id_setor == int(request.args['setor_id']))
                filtros['setor_id'] = request.args['setor_id']
            except ValueError:
                pass
        
        # Filtro por Assunto (busca textual)
        if 'assunto' in request.args and request.args['assunto']:
            termo = request.args['assunto'].strip()
            if termo:
                def criar_padrao_regex(palavra):
                    padrao = ''
                    for letra in palavra.lower():
                        if letra == 'a': padrao += '[aáàãâä]'
                        elif letra == 'e': padrao += '[eéèêë]'
                        elif letra == 'i': padrao += '[iíìîï]'
                        elif letra == 'o': padrao += '[oóòõôö]'
                        elif letra == 'u': padrao += '[uúùûü]'
                        elif letra == 'c': padrao += '[cç]'
                        else: padrao += re.escape(letra)
                    return padrao
                
                palavras = termo.split()
                condicoes_assunto = []
                
                for palavra in palavras:
                    if len(palavra) >= 2:
                        padrao = criar_padrao_regex(palavra)
                        try:
                            condicoes_assunto.append(Assunto.nome_assunto.op('~*')(padrao))
                        except Exception:
                            condicoes_assunto.append(Assunto.nome_assunto.ilike(f"%{palavra}%"))
                    else:
                        condicoes_assunto.append(Assunto.nome_assunto.ilike(f"%{palavra}%"))
                
                if condicoes_assunto:
                    query = query.join(Assunto, Livro.id_assunto == Assunto.id_assunto).filter(*condicoes_assunto)
                
                filtros['assunto'] = termo
        
        # Filtro por Data
        if 'mes' in request.args and request.args['mes']:
            mes = request.args['mes']
            ano = request.args.get('ano', '')
            if mes.isdigit():
                mes_int = int(mes)
                if ano.isdigit():
                    ano_int = int(ano)
                    query = query.filter(
                        extract('month', Livro.data_livro) == mes_int,
                        extract('year', Livro.data_livro) == ano_int
                    )
                    filtros['mes'] = mes
                    filtros['ano'] = ano
                else:
                    query = query.filter(extract('month', Livro.data_livro) == mes_int)
                    filtros['mes'] = mes
        
        # Filtro por Conteúdo (busca textual inteligente)
        if 'conteudo' in request.args and request.args['conteudo']:
            termo = request.args['conteudo'].strip()
            if termo:
                def criar_padrao_regex(palavra):
                    padrao = ''
                    for letra in palavra.lower():
                        if letra == 'a': padrao += '[aáàãâä]'
                        elif letra == 'e': padrao += '[eéèêë]'
                        elif letra == 'i': padrao += '[iíìîï]'
                        elif letra == 'o': padrao += '[oóòõôö]'
                        elif letra == 'u': padrao += '[uúùûü]'
                        elif letra == 'c': padrao += '[cç]'
                        else: padrao += re.escape(letra)
                    return padrao

                palavras = termo.split()
                condicoes = []

                for palavra in palavras:
                    if len(palavra) >= 2:
                        padrao = criar_padrao_regex(palavra)
                        try:
                            condicoes.append(Livro.conteudo_livro.op('~*')(padrao))
                        except Exception:
                            condicoes.append(Livro.conteudo_livro.ilike(f"%{palavra}%"))
                    else:
                        condicoes.append(Livro.conteudo_livro.ilike(f"%{palavra}%"))

                if condicoes:
                    query = query.filter(*condicoes)

                filtros['conteudo'] = termo
        
        # Filtro por Executor (busca textual inteligente)
        if 'executor' in request.args and request.args['executor']:
            termo = request.args['executor'].strip()
            if termo:
                def criar_padrao_regex(palavra):
                    padrao = ''
                    for letra in palavra.lower():
                        if letra == 'a': padrao += '[aáàãâä]'
                        elif letra == 'e': padrao += '[eéèêë]'
                        elif letra == 'i': padrao += '[iíìîï]'
                        elif letra == 'o': padrao += '[oóòõôö]'
                        elif letra == 'u': padrao += '[uúùûü]'
                        elif letra == 'c': padrao += '[cç]'
                        else: padrao += re.escape(letra)
                    return padrao

                palavras = termo.split()
                condicoes_executor = []

                for palavra in palavras:
                    if len(palavra) >= 2:
                        padrao = criar_padrao_regex(palavra)
                        try:
                            condicoes_executor.append(Executor.nome_executor.op('~*')(padrao))
                        except Exception:
                            condicoes_executor.append(Executor.nome_executor.ilike(f"%{palavra}%"))
                    else:
                        condicoes_executor.append(Executor.nome_executor.ilike(f"%{palavra}%"))

                if condicoes_executor:
                    # JOIN com a tabela Executor via livro_executor
                    subquery = db.session.query(LivroExecutor.id_livro).join(
                        Executor, LivroExecutor.id_executor == Executor.id_executor
                    ).filter(*condicoes_executor)
                    
                    query = query.filter(Livro.id_livro.in_(subquery))

                filtros['executor'] = termo
        
        # Filtro por Editor (busca textual inteligente)
        if 'editor' in request.args and request.args['editor']:
            termo = request.args['editor'].strip()
            if termo:
                def criar_padrao_regex(palavra):
                    padrao = ''
                    for letra in palavra.lower():
                        if letra == 'a': padrao += '[aáàãâä]'
                        elif letra == 'e': padrao += '[eéèêë]'
                        elif letra == 'i': padrao += '[iíìîï]'
                        elif letra == 'o': padrao += '[oóòõôö]'
                        elif letra == 'u': padrao += '[uúùûü]'
                        elif letra == 'c': padrao += '[cç]'
                        else: padrao += re.escape(letra)
                    return padrao

                palavras = termo.split()
                condicoes_editor = []

                for palavra in palavras:
                    if len(palavra) >= 2:
                        padrao = criar_padrao_regex(palavra)
                        try:
                            condicoes_editor.append(Editor.nome_editor.op('~*')(padrao))
                        except Exception:
                            condicoes_editor.append(Editor.nome_editor.ilike(f"%{palavra}%"))
                    else:
                        condicoes_editor.append(Editor.nome_editor.ilike(f"%{palavra}%"))

                if condicoes_editor:
                    # JOIN com a tabela Editor via livro_editor
                    subquery = db.session.query(LivroEditor.id_livro).join(
                        Editor, LivroEditor.id_editor == Editor.id_editor
                    ).filter(*condicoes_editor)
                    
                    query = query.filter(Livro.id_livro.in_(subquery))

                filtros['editor'] = termo
        
        # Filtro por Área Geográfica
        if 'area_id' in request.args and request.args['area_id']:
            try:
                area_id = int(request.args['area_id'])
                query = query.join(Livro.areas_geograficas).filter(AreaGeografica.id_area_geografica == area_id)
                filtros['area_id'] = request.args['area_id']
            except ValueError:
                pass
        
        # Ordenar e executar a query
        livros = query.order_by(Livro.id_livro.desc()).all()
    
    return render_template('livros.html',
                           livros=livros,
                           locais=locais,
                           setores=setores,
                           assuntos=assuntos,
                           executores=executores,
                           autores=autores,
                           editores=editores,
                           areas=areas,
                           conteudos=conteudos,
                           filtros=filtros,
                           datetime=datetime,
                           has_filters=has_filters)

@app.route('/api/autores')
def get_autores():
    autores = Autor.query.order_by(Autor.nome_autor).all()
    return jsonify([{
        'id': a.id_autor,
        'nome': a.nome_autor,
        'tipo': a.tipo_autor
    } for a in autores])

@app.route('/api/conteudos')
def get_conteudos():
    conteudos = db.session.query(Livro.conteudo_livro).distinct().filter(Livro.conteudo_livro.isnot(None)).all()
    return jsonify([c[0] for c in conteudos if c[0]])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)