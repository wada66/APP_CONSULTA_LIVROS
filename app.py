import re
from flask import Flask, render_template, request, jsonify
from config import Config
from models import db, Livro, Setor, Local, Assunto, Executor, Autor, Editor, AreaGeografica, LivroAutor
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
        request.args.get('autor_id'),
        request.args.get('local_id'),
        request.args.get('setor_id'),
        request.args.get('assunto'),
        request.args.get('mes'),
        request.args.get('ano'),
        request.args.get('conteudo'),
        request.args.get('executor_id'),
        request.args.get('editor_id'),
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
        
        # Filtro por Autor
        if 'autor_id' in request.args and request.args['autor_id']:
            try:
                autor_id = int(request.args['autor_id'])
                autor_tipo = request.args.get('autor_tipo', 'todos')
                
                subquery = db.session.query(LivroAutor.id_livro).filter(
                    LivroAutor.id_autor == autor_id
                )
                if autor_tipo != 'todos':
                    subquery = subquery.join(Autor, LivroAutor.id_autor == Autor.id_autor)\
                                       .filter(Autor.tipo_autor == autor_tipo)
                
                query = query.filter(Livro.id_livro.in_(subquery))
                filtros['autor_id'] = request.args['autor_id']
                if autor_tipo != 'todos':
                    filtros['autor_tipo'] = autor_tipo
            except ValueError:
                pass
        
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
        
        # Filtro por Conteúdo
        if 'conteudo' in request.args and request.args['conteudo']:
            query = query.filter(Livro.conteudo_livro.ilike(f"%{request.args['conteudo']}%"))
            filtros['conteudo'] = request.args['conteudo']
        
        # Filtro por Executor
        if 'executor_id' in request.args and request.args['executor_id']:
            try:
                executor_id = int(request.args['executor_id'])
                query = query.join(Livro.executores).filter(Executor.id_executor == executor_id)
                filtros['executor_id'] = request.args['executor_id']
            except ValueError:
                pass
        
        # Filtro por Editor
        if 'editor_id' in request.args and request.args['editor_id']:
            try:
                editor_id = int(request.args['editor_id'])
                query = query.join(Livro.editores).filter(Editor.id_editor == editor_id)
                filtros['editor_id'] = request.args['editor_id']
            except ValueError:
                pass
        
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