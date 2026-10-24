"""Código Secreto: progreso, tiempo y validación en el servidor."""
import hashlib, hmac, json, os, secrets, sqlite3, time, unicodedata
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / '.env')
from contextlib import contextmanager
from flask import Flask, jsonify, render_template, request, session
from werkzeug.security import check_password_hash
ROOT = Path(__file__).resolve().parent
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=os.environ.get('RENDER')=='true', MAX_CONTENT_LENGTH=16384)
DB_PATH = os.environ.get('DB_PATH', str(ROOT/'instance'/'game.sqlite3'))
DATABASE_URL = os.environ.get('DATABASE_URL')
LOCATIONS = ['Los sobres están bajo el escritorio central','Busquen los sobres detrás de la laptop','Revisen siempre bajo la mesa del proyector','Busquen todos los sobres bajo las sillas','Los sobres están junto a la puerta']
CIRCUITS = ['0','3','2','5','4']
CODES = ['251','372','583','916','635']
BANKS = [['ES','LA','CAFE','EQUIPO','INGENIERÍA','CODIGO','SECRETO','NEXO','TIEMPO'],['CAFE','ES','LA','EQUIPO','CODIGO','SECRETO','INGENIERÍA','NEXO','TIEMPO'],['CAFE','CODIGO','ES','EQUIPO','LA','SECRETO','NEXO','INGENIERÍA','TIEMPO'],['INGENIERÍA','CAFE','CODIGO','EQUIPO','SECRETO','ES','NEXO','TIEMPO','LA'],['CAFE','CODIGO','INGENIERÍA','EQUIPO','ES','LA','SECRETO','NEXO','TIEMPO']]
TITLES = ['Cuenta bien, lee mejor','La contraseña imposible','El algoritmo corrompido','Compuertas en serie','Haz zoom','Encuentra las diferencias','La transmisión interceptada','Transmisión de doble cifrado','Señales intermitentes','Mensaje final']
QUESTIONS = ['¿Cuál es tu enunciado correcto?','¿Cuál es el dígito central de la contraseña de tres cifras?','¿Qué número de un solo dígito se obtiene al ejecutar correctamente el programa?','¿Cuál es el resultado decimal de la salida del circuito lógico?','¿Cuál es el código de aula de la puerta marcada?','¿Cuántas diferencias hay entre la Imagen A y la Imagen B?','¿Cuál es la clave recuperada de la transmisión NEXO?','¿Cuál es el último dígito de la suma obtenida después de descifrar el mensaje?','¿Qué código de tres cifras se obtiene al interpretar las señales luminosas?','¿Cuál es el mensaje final formado con las palabras de las posiciones recuperadas?']

def normalize(value):
    text=unicodedata.normalize('NFD',value.strip().casefold())
    return ' '.join(''.join(c for c in text if unicodedata.category(c)!='Mn' and (c.isalnum() or c.isspace())).split())

@contextmanager
def connection():
    if DATABASE_URL:
        import psycopg
        from psycopg.rows import dict_row
        db=psycopg.connect(DATABASE_URL,row_factory=dict_row)
    else:
        Path(DB_PATH).parent.mkdir(parents=True,exist_ok=True)
        db=sqlite3.connect(DB_PATH,timeout=20)
        db.row_factory=sqlite3.Row
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def sql(db,query,args=()):
    return db.execute(query.replace('?', '%s') if DATABASE_URL else query,args)

def init_db():
    with connection() as db:
        sql(db,"CREATE TABLE IF NOT EXISTS missions (id TEXT PRIMARY KEY, team INTEGER NOT NULL, started DOUBLE PRECISION NOT NULL, stage INTEGER NOT NULL DEFAULT 0, answers TEXT NOT NULL DEFAULT '[]', attempts TEXT NOT NULL DEFAULT '[]', finished INTEGER NOT NULL DEFAULT 0)")
        sql(db,"CREATE TABLE IF NOT EXISTS submissions (id TEXT PRIMARY KEY, club TEXT NOT NULL, score INTEGER NOT NULL, time_ms BIGINT NOT NULL, answers TEXT NOT NULL)")
        sql(db,"CREATE TABLE IF NOT EXISTS app_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        legacy=ROOT/'legacy-results.json'
        if legacy.exists() and not sql(db,'SELECT value FROM app_metadata WHERE key=?',('legacy-imported',)).fetchone():
            for i,entry in enumerate(json.loads(legacy.read_text(encoding='utf-8')).get('submissions',[])):
                identifier='legacy-'+hashlib.sha256((str(i)+json.dumps(entry,sort_keys=True)).encode()).hexdigest()[:32]
                sql(db,'INSERT INTO submissions (id,club,score,time_ms,answers) VALUES (?,?,?,?,?) ON CONFLICT (id) DO NOTHING',(identifier,entry['club'],entry['score'],entry['time_ms'],json.dumps(entry['answers'])))
            sql(db,'INSERT INTO app_metadata (key,value) VALUES (?,?) ON CONFLICT (key) DO NOTHING',('legacy-imported','yes'))

def event_config():
    path=ROOT/'event_config.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'photos':{}}

def photo(team):
    return event_config().get('photos',{}).get(CIRCUITS[team-1],{})

def expected(team):
    return [LOCATIONS[team-1],'4','2',CIRCUITS[team-1],photo(team).get('answer',''),'5','5','8',CODES[team-1],'LA INGENIERÍA ES EQUIPO']

def password_valid(value):
    hashed=os.environ.get('ADMIN_PASSWORD_HASH')
    return check_password_hash(hashed,value) if hashed else hmac.compare_digest(value.encode(),os.environ.get('ADMIN_PASSWORD','wobukeneng').encode())

def is_admin():
    return time.time()<session.get('admin_until',0)

@app.before_request
def protect():
    session.setdefault('csrf',secrets.token_hex(24))
    if request.method in ('POST','DELETE','PUT') and not hmac.compare_digest(request.headers.get('X-CSRF-Token',''),session['csrf']):
        return jsonify(error='Sesión vencida. Recarga la página.'),403

@app.get('/')
def index():
    return render_template('index.html')

@app.get('/admin')
@app.get('/leaderboard')
def admin():
    return render_template('admin.html')

@app.get('/healthz')
def health():
    with connection() as db:
        sql(db,'SELECT 1')
    return jsonify(status='ok',storage='postgresql' if DATABASE_URL else 'sqlite')

def public(row):
    team,stage=row['team'],row['stage']
    value=dict(team=team,stage=stage,started=row['started'],finished=bool(row['finished']),answers=json.loads(row['answers']))
    if stage<10:
        value.update(title=TITLES[stage],question=QUESTIONS[stage])
    if stage==4:
        value['photo']=dict(url=photo(team).get('url') or '/static/event/aula-provisional.svg',number=CIRCUITS[team-1],pending=not all(photo(team).get(k) for k in ('url','answer','destination')))
    if stage==8:
        patterns=dict(zip('0123456789',['-----','.----','..---','...--','....-','.....','-....','--...','---..','----.']))
        value['signal']=[patterns[n] for n in CODES[team-1]]
    if stage==9:
        value['words']=BANKS[team-1]
    return value

@app.get('/api/state')
def state():
    with connection() as db:
        row=sql(db,'SELECT * FROM missions WHERE id=?',(session.get('mission',''),)).fetchone()
    return jsonify(csrf=session['csrf'],admin=is_admin(),mission=public(row) if row else None)

@app.post('/api/start')
def start():
    data=request.get_json(silent=True) or {}
    team=data.get('team')
    if type(team)!=int or team not in range(1,6):
        return jsonify(error='Selecciona un equipo del 1 al 5.'),400
    with connection() as db:
        existing=sql(db,'SELECT * FROM missions WHERE id=?',(session.get('mission',''),)).fetchone()
        if existing and not existing['finished']:
            return jsonify(mission=public(existing))
        mission=secrets.token_hex(24)
        sql(db,'INSERT INTO missions (id,team,started) VALUES (?,?,?)',(mission,team,time.time()))
        row=sql(db,'SELECT * FROM missions WHERE id=?',(mission,)).fetchone()
    session['mission']=mission
    return jsonify(mission=public(row))

@app.post('/api/answer')
def answer():
    data=request.get_json(silent=True) or {}
    value=data.get('answer')
    if not isinstance(value,str) or not value.strip() or len(value)>300:
        return jsonify(error='Escribe una respuesta válida.'),400
    with connection() as db:
        if not DATABASE_URL:
            sql(db,'BEGIN IMMEDIATE')
        row=sql(db,'SELECT * FROM missions WHERE id=?'+(' FOR UPDATE' if DATABASE_URL else ''),(session.get('mission',''),)).fetchone()
        if not row or row['finished']:
            return jsonify(error='No hay una misión activa.'),409
        stage,team=row['stage'],row['team']
        if data.get('stage')!=stage:
            return jsonify(error='La etapa cambió. Recarga para recuperar tu avance.'),409
        if stage==4 and not all(photo(team).get(k) for k in ('url','answer','destination')):
            return jsonify(error='Esta fotografía es provisional. Solicita al organizador que habilite el siguiente reto.'),409
        target=expected(team)[stage]
        if stage in (0,9):
            correct=normalize(value)==normalize(target)
        else:
            correct=value.strip().casefold()==target.strip().casefold()
        attempts=json.loads(row['attempts'])+[dict(stage=stage,correct=correct)]
        sql(db,'UPDATE missions SET attempts=? WHERE id=?',(json.dumps(attempts),row['id']))
        if not correct:
            return jsonify(correct=False,message='La señal no coincide. Revisa las pistas con tu equipo e inténtalo de nuevo.')
        answers=json.loads(row['answers'])+[value.strip()]
        finished=stage==9
        sql(db,'UPDATE missions SET stage=?,answers=?,finished=? WHERE id=?',(stage+1,json.dumps(answers),int(finished),row['id']))
        if finished:
            sql(db,'INSERT INTO submissions (id,club,score,time_ms,answers) VALUES (?,?,?,?,?)',(row['id'],f'Equipo {team}',sum(not a.startswith('PENDIENTE') for a in answers),int((time.time()-row['started'])*1000),json.dumps(answers)))
        updated=sql(db,'SELECT * FROM missions WHERE id=?',(row['id'],)).fetchone()
    return jsonify(correct=True,message='Dirígete a '+photo(team)['destination'] if stage==4 else '¡Respuesta confirmada!',mission=public(updated))

@app.post('/api/admin/login')
def login():
    if time.time()<session.get('retry_after',0):
        return jsonify(error='Espera un minuto antes de volver a intentar.'),429
    data=request.get_json(silent=True) or {}
    if not isinstance(data.get('password'),str) or not password_valid(data['password']):
        failures=session.get('failures',0)+1
        session['failures']=failures
        if failures>=5:
            session['retry_after']=time.time()+60
            session['failures']=0
        return jsonify(error='Contraseña incorrecta.'),401
    session['admin_until']=time.time()+3600
    session['failures']=0
    return jsonify(success=True)

@app.get('/api/results')
def results():
    if not is_admin():
        return jsonify(error='Ingresa la contraseña de organización.'),401
    with connection() as db:
        rows=sql(db,'SELECT * FROM submissions ORDER BY score DESC,time_ms ASC,id ASC').fetchall()
    return jsonify(leaderboard=[{**dict(r),'answers':json.loads(r['answers'])} for r in rows],correct_answers=expected(1),answers_by_team={f'Equipo {n}':expected(n) for n in range(1,6)})

@app.delete('/api/results/<submission_id>')
def delete(submission_id):
    if not is_admin():
        return jsonify(error='Inicia sesión como organizador.'),401
    data=request.get_json(silent=True) or {}
    if not isinstance(data.get('password'),str) or not password_valid(data['password']):
        return jsonify(error='Debes volver a introducir la contraseña para borrar este registro.'),403
    with connection() as db:
        result=sql(db,'DELETE FROM submissions WHERE id=?',(submission_id,))
        if not result.rowcount:
            return jsonify(error='El registro ya no existe.'),404
    return jsonify(success=True)

@app.get('/api/admin/readiness')
def readiness():
    if not is_admin():
        return jsonify(error='Acceso reservado.'),401
    return jsonify(teams=[dict(team=n,photo=CIRCUITS[n-1],ready=all(photo(n).get(k) for k in ('url','answer','destination'))) for n in range(1,6)])

@app.post('/api/monitor/advance-photo')
def monitor_advance():
    data=request.get_json(silent=True) or {}
    if not isinstance(data.get('password'),str) or not password_valid(data['password']):
        return jsonify(error='Contraseña incorrecta.'),403
    with connection() as db:
        if not DATABASE_URL:
            sql(db,'BEGIN IMMEDIATE')
        row=sql(db,'SELECT * FROM missions WHERE id=?'+(' FOR UPDATE' if DATABASE_URL else ''),(session.get('mission',''),)).fetchone()
        if not row or row['stage']!=4 or row['finished']:
            return jsonify(error='No hay una etapa de fotografía pendiente.'),409
        if all(photo(row['team']).get(k) for k in ('url','answer','destination')):
            return jsonify(error='Este equipo ya tiene una fotografía real configurada.'),409
        answers=json.loads(row['answers'])+['PENDIENTE · habilitado por monitor']
        sql(db,'UPDATE missions SET stage=5,answers=? WHERE id=?',(json.dumps(answers),row['id']))
        row=sql(db,'SELECT * FROM missions WHERE id=?',(row['id'],)).fetchone()
    return jsonify(correct=True,message='Etapa provisional habilitada por el organizador.',mission=public(row))

init_db()
if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5001)),debug=False)
