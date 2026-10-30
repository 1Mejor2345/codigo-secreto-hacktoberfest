"""Código Secreto: progreso, tiempo y validación en el servidor."""
import hashlib, hmac, json, os, secrets, sqlite3, time, unicodedata
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / '.env')
from contextlib import contextmanager
from flask import Flask, jsonify, render_template, request, session, make_response, redirect, url_for
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
PROVERBS = ['A caballo regalado no se le mira el diente','Cuando el río suena, piedras lleva','Al que madruga, Dios lo ayuda','Más vale pájaro en mano que ciento volando','Perro que ladra no muerde']
EMOJIS = ['🐴 🎁 🚫 👀 🦷','🏞️ 🔊 🪨','🐓 🌅 🙏 🤝','🐦 ✋ ⚖️ 💯 🐦 ☁️','🐕 📢 🚫 🦷']
PROVERB_VARIANTS = [
    ['A caballo regalado no se le miran los dientes','A caballo regalado no se le mira los dientes','A caballo regalado no le mires el diente','A caballo regalado no le mires los dientes'],
    ['Cuando el río suena es porque piedras lleva','Si el río suena piedras lleva'],
    ['Al que madruga Dios le ayuda','A quien madruga Dios lo ayuda','A quien madruga Dios le ayuda','Al que madruga Dios ayuda','A quien madruga Dios ayuda'],
    ['Más vale un pájaro en mano que ciento volando','Más vale pájaro en mano que cien volando','Más vale un pájaro en mano que cien volando'],
    []]

BANKS = [['ES','LA','CAFE','EQUIPO','INGENIERÍA','CODIGO','SECRETO','NEXO','TIEMPO'],['CAFE','ES','LA','EQUIPO','CODIGO','SECRETO','INGENIERÍA','NEXO','TIEMPO'],['CAFE','CODIGO','ES','EQUIPO','LA','SECRETO','NEXO','INGENIERÍA','TIEMPO'],['INGENIERÍA','CAFE','CODIGO','EQUIPO','SECRETO','ES','NEXO','TIEMPO','LA'],['CAFE','CODIGO','INGENIERÍA','EQUIPO','ES','LA','SECRETO','NEXO','TIEMPO']]
TITLES = ['Cuenta bien, lee mejor','La contraseña imposible','El algoritmo corrompido','Compuertas en serie','Dilo con emojis','Encuentra las diferencias','La transmisión interceptada','Transmisión de doble cifrado','Señales intermitentes','Mensaje final']
QUESTIONS = [
    'El primer reto puede parecer confuso, pero si lees bien tu ficha de normas lo entenderás.\n¿Cuál es tu enunciado correcto?',
    '¿Cuál es el dígito central de la contraseña de tres cifras?',
    '¿Qué número de un solo dígito se obtiene al ejecutar correctamente el programa?',
    '¿Cuál es el resultado decimal de la salida del circuito lógico?',
    '¿Qué refrán representan estos emojis? Escribe el refrán completo.',
    '¿Cuántas diferencias hay entre la Imagen A y la Imagen B?',
    '¿Cuál es la clave recuperada de la transmisión NEXO?',
    '¿Cuál es el último dígito de la suma obtenida después de descifrar el mensaje?',
    '¿Qué código de tres cifras se obtiene al interpretar las señales luminosas?',
    '¿Cuál es el mensaje final formado al combinar las palabras correspondientes a los números obtenidos en los retos anteriores?']
CONFIRMATIONS = [
    '¿Confirmas que «{respuesta}» es tu enunciado correcto?',
    '¿Confirmas que «{respuesta}» es el dígito central de la contraseña?',
    '¿Confirmas que el programa reconstruido produce «{respuesta}»?',
    '¿Confirmas que la salida del circuito es «{respuesta}»?',
    '¿Confirmas que «{respuesta}» es el refrán completo?',
    '¿Confirmas que encontraste «{respuesta}» diferencias?',
    '¿Confirmas que la clave recuperada es «{respuesta}»?',
    '¿Confirmas que el último dígito es «{respuesta}»?',
    '¿Confirmas que el código descifrado es «{respuesta}»?',
    '¿Confirmas que el código descifrado es «{respuesta}»?']
NUMERIC_LENGTHS = {1:1, 2:1, 3:1, 5:1, 6:1, 7:1, 8:3}


def normalize(value):
    text=unicodedata.normalize('NFD',value.strip().casefold())
    return ' '.join(''.join(c if c.isalnum() or c.isspace() else ' ' for c in text if unicodedata.category(c)!='Mn').split())

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

def add_columns(db, table, columns):
    existing = set()
    if not DATABASE_URL:
        existing = {row['name'] for row in sql(db, 'PRAGMA table_info('+table+')').fetchall()}
    for name, definition in columns.items():
        if DATABASE_URL:
            sql(db, f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {name} {definition}')
        elif name not in existing:
            sql(db, f'ALTER TABLE {table} ADD COLUMN {name} {definition}')

def init_db():
    with connection() as db:
        sql(db,"CREATE TABLE IF NOT EXISTS missions (id TEXT PRIMARY KEY, team INTEGER NOT NULL, started DOUBLE PRECISION NOT NULL, stage INTEGER NOT NULL DEFAULT 0, answers TEXT NOT NULL DEFAULT '[]', attempts TEXT NOT NULL DEFAULT '[]', finished INTEGER NOT NULL DEFAULT 0)")
        sql(db,"CREATE TABLE IF NOT EXISTS submissions (id TEXT PRIMARY KEY, club TEXT NOT NULL, score INTEGER NOT NULL, time_ms BIGINT NOT NULL, answers TEXT NOT NULL)")
        sql(db,"CREATE TABLE IF NOT EXISTS app_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        # Backfill only on the first migration, preserving clocks already in progress.
        if DATABASE_URL:
            had_clock=sql(db,"SELECT 1 FROM information_schema.columns WHERE table_name='missions' AND column_name='timed_started'").fetchone()
        else:
            had_clock=any(r['name']=='timed_started' for r in sql(db,'PRAGMA table_info(missions)').fetchall())
        add_columns(db, 'missions', {'club_name': "TEXT NOT NULL DEFAULT ''", 'timed_started': 'DOUBLE PRECISION'})
        if not had_clock:
            sql(db,'UPDATE missions SET timed_started=started WHERE stage>0')
        add_columns(db, 'submissions', {'team': 'INTEGER', 'expected_answers': "TEXT NOT NULL DEFAULT '[]'", 'challenge_version': "TEXT NOT NULL DEFAULT 'photo'", 'manual_reviews': "TEXT NOT NULL DEFAULT '{}'"})
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
    return [LOCATIONS[team-1],'4','2',CIRCUITS[team-1],PROVERBS[team-1],'5','5','8',CODES[team-1],'LA INGENIERÍA ES EQUIPO']

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
    session.pop('admin_until', None)
    response = make_response(render_template('index.html'))
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.get('/admin')
def admin_alias():
    return redirect(url_for('admin'))

@app.get('/leaderboard')
def admin():
    session.pop('admin_until', None)
    response = make_response(render_template('admin.html'))
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.post('/api/admin/logout')
def logout():
    session.pop('admin_until', None)
    return jsonify(success=True)

@app.get('/healthz')
def health():
    with connection() as db:
        sql(db,'SELECT 1')
    return jsonify(status='ok',storage='postgresql' if DATABASE_URL else 'sqlite')

def needs_first_correction(row):
    answers=json.loads(row['answers'])
    return not row['finished'] and row['stage']>0 and bool(answers) and not answer_matches(answers[0],LOCATIONS[row['team']-1],0)

def public(row):
    team,stage=row['team'],0 if needs_first_correction(row) else row['stage']
    value=dict(team=team,club_name=row['club_name'] or f'Equipo {team}',stage=stage,started=row['timed_started'],awaiting_start=stage==1 and row['timed_started'] is None,finished=bool(row['finished']),answers=json.loads(row['answers']))
    if stage<10:
        value.update(title=f'Reto {stage+1} — {TITLES[stage]}',question=QUESTIONS[stage],confirmation=CONFIRMATIONS[stage])
    if stage==1 and row['timed_started'] is None:
        value['first_destination']=LOCATIONS[team-1]
    if 5<=stage<10:
        value['handoff']=dict(instruction='Acércate a Gabriel Vallejo y dile esta frase:',phrase=PROVERBS[team-1])
    if stage==4:
        value['emoji_screen']=dict(number=CIRCUITS[team-1],emojis=EMOJIS[team-1])
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
    club_name=data.get('club_name')
    if not isinstance(club_name,str) or not 2<=len(club_name.strip())<=60 or any(ord(c)<32 for c in club_name):
        return jsonify(error='Escribe el nombre de tu club o gremio (entre 2 y 60 caracteres).'),400
    club_name=club_name.strip()
    with connection() as db:
        existing=sql(db,'SELECT * FROM missions WHERE id=?',(session.get('mission',''),)).fetchone()
        if existing and not existing['finished']:
            return jsonify(mission=public(existing))
        mission=secrets.token_hex(24)
        sql(db,'INSERT INTO missions (id,team,started,club_name) VALUES (?,?,?,?)',(mission,team,time.time(),club_name))
        row=sql(db,'SELECT * FROM missions WHERE id=?',(mission,)).fetchone()
    session['mission']=mission
    return jsonify(mission=public(row))

@app.post('/api/mission/begin-timed')
def begin_timed():
    with connection() as db:
        if not DATABASE_URL:
            sql(db,'BEGIN IMMEDIATE')
        row=sql(db,'SELECT * FROM missions WHERE id=?'+(' FOR UPDATE' if DATABASE_URL else ''),(session.get('mission',''),)).fetchone()
        if not row or row['finished'] or row['stage']!=1 or needs_first_correction(row):
            return jsonify(error='El primer reto debe estar resuelto.'),409
        if row['timed_started'] is None:
            sql(db,'UPDATE missions SET timed_started=? WHERE id=?',(time.time(),row['id']))
        updated=sql(db,'SELECT * FROM missions WHERE id=?',(row['id'],)).fetchone()
    return jsonify(mission=public(updated))


@app.post('/api/mission/name')
def rename_mission():
    data=request.get_json(silent=True) or {}
    name=data.get('club_name')
    if not isinstance(name,str) or not 2<=len(name.strip())<=60 or any(ord(c)<32 for c in name):
        return jsonify(error='Escribe un nombre de 2 a 60 caracteres.'),400
    with connection() as db:
        updated=sql(db,'UPDATE missions SET club_name=? WHERE id=? AND finished=0',(name.strip(),session.get('mission','')))
        if not updated.rowcount:
            return jsonify(error='No hay una misión activa para cambiar el nombre.'),409
        row=sql(db,'SELECT * FROM missions WHERE id=?',(session['mission'],)).fetchone()
    return jsonify(mission=public(row))

def answer_matches(value, target, stage):
    if not target:
        return None
    if stage==4 and value.startswith('PENDIENTE · habilitado por monitor'):
        return None
    if stage==4 and target in PROVERBS:
        index=PROVERBS.index(target)
        return normalize(value) in {normalize(v) for v in [target]+PROVERB_VARIANTS[index]}
    return normalize(value)==normalize(target) if stage in (0,9) else value.strip().casefold()==target.strip().casefold()

@app.post('/api/answer')
def answer():
    data=request.get_json(silent=True) or {}
    value=data.get('answer')
    if not isinstance(value,str) or not value.strip() or len(value)>300:
        return jsonify(error='Debes escribir una respuesta antes de continuar.'),400
    with connection() as db:
        if not DATABASE_URL:
            sql(db,'BEGIN IMMEDIATE')
        row=sql(db,'SELECT * FROM missions WHERE id=?'+(' FOR UPDATE' if DATABASE_URL else ''),(session.get('mission',''),)).fetchone()
        if not row or row['finished']:
            return jsonify(error='No hay una misión activa.'),409
        if needs_first_correction(row):
            if type(data.get('stage')) is not int or data['stage']!=0:
                return jsonify(error='Recarga la página para continuar.'),409
            correct=answer_matches(value,LOCATIONS[row['team']-1],0)
            attempts=json.loads(row['attempts'])+[dict(stage=0,correct=correct)]
            sql(db,'UPDATE missions SET attempts=? WHERE id=?',(json.dumps(attempts),row['id']))
            if not correct:
                return jsonify(accepted=False,message='Respuesta incorrecta.'),200
            answers=json.loads(row['answers']);answers[0]=value.strip()
            sql(db,'UPDATE missions SET answers=? WHERE id=?',(json.dumps(answers),row['id']))
            updated=sql(db,'SELECT * FROM missions WHERE id=?',(row['id'],)).fetchone()
            return jsonify(accepted=True,message='',mission=public(updated))
        stage,team=row['stage'],row['team']
        if type(data.get('stage')) is not int or data['stage']!=stage:
            return jsonify(error='La etapa cambió. Recarga para recuperar tu avance.'),409
        if stage in NUMERIC_LENGTHS and (not value.isascii() or not value.isdigit() or len(value)!=NUMERIC_LENGTHS[stage]):
            return jsonify(error='Ingresa un dígito.' if NUMERIC_LENGTHS[stage]==1 else 'Ingresa tres dígitos.'),400
        if stage>0 and row['timed_started'] is None:
            return jsonify(error='Confirma el inicio del tiempo para continuar.'),409
        targets=expected(team)
        correct=answer_matches(value,targets[stage],stage)
        if stage in (0,9) and not correct:
            attempts=json.loads(row['attempts'])+[dict(stage=stage,correct=False)]
            sql(db,'UPDATE missions SET attempts=? WHERE id=?',(json.dumps(attempts),row['id']))
            return jsonify(accepted=False,message='Respuesta incorrecta.'),200
        attempts=json.loads(row['attempts'])+[dict(stage=stage,correct=correct)]
        answers=json.loads(row['answers'])+[value.strip()]
        finished=stage==9
        sql(db,'UPDATE missions SET stage=?,answers=?,attempts=?,finished=? WHERE id=?',(stage+1,json.dumps(answers),json.dumps(attempts),int(finished),row['id']))
        if finished:
            score=sum(answer_matches(a,targets[i],i) is True for i,a in enumerate(answers))
            sql(db,'INSERT INTO submissions (id,club,score,time_ms,answers,team,expected_answers,challenge_version) VALUES (?,?,?,?,?,?,?,?)',(row['id'],row['club_name'] or f'Equipo {team}',score,int((time.time()-row['timed_started'])*1000),json.dumps(answers),team,json.dumps(targets),'emoji'))
        updated=sql(db,'SELECT * FROM missions WHERE id=?',(row['id'],)).fetchone()
    return jsonify(accepted=True,message='',mission=public(updated))

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

LEGACY_ANSWERS=['I','8','F','P','0','X','3','Z','M','1']

def result_entry(row):
    entry=dict(row)
    team=entry.get('team') or entry.pop('mission_team',None)
    entry.pop('mission_team',None)
    answers=json.loads(entry['answers'])
    stored=json.loads(entry.get('expected_answers') or '[]')
    legacy=entry['id'].startswith('legacy-')
    targets=stored if len(stored)==10 else LEGACY_ANSWERS[:] if legacy else expected(team or 1)
    if len(stored)!=10 and not legacy and entry.get('challenge_version')=='photo':
        targets[4]=photo(team or 1).get('answer','')
    reviews=json.loads(entry.get('manual_reviews') or '{}')
    comparison=[]
    for i in range(10):
        automatic=answer_matches(answers[i],targets[i],i) if i<len(answers) else False
        approved=bool(reviews.get(str(i+1),{}).get('approved'))
        title=f'Reto {i+1} · versión anterior' if legacy else 'Haz zoom · versión anterior' if i==4 and entry.get('challenge_version')=='photo' else TITLES[i]
        comparison.append(dict(stage=i+1,title=title,submitted=answers[i] if i<len(answers) else '',expected=targets[i],correct=True if approved else automatic,automatic_correct=automatic,manual_approved=approved))
    entry.update(team=team,answers=answers,expected_answers=targets,legacy=legacy,manual_reviews=reviews,comparison=comparison)
    return entry


@app.get('/api/results')
def results():
    if not is_admin():
        return jsonify(error='Ingresa la contraseña de organización.'),401
    with connection() as db:
        rows=sql(db,'SELECT s.*, m.team AS mission_team FROM submissions s LEFT JOIN missions m ON m.id=s.id ORDER BY s.score DESC,s.time_ms ASC,s.id ASC').fetchall()
    response=jsonify(leaderboard=[result_entry(row) for row in rows])
    response.headers['Cache-Control']='no-store'
    return response


@app.post('/api/results/<submission_id>/review')
def review_answer(submission_id):
    if not is_admin():
        return jsonify(error='Inicia sesión como organizador.'),401
    data=request.get_json(silent=True) or {}
    stage=data.get('stage');approved=data.get('approved')
    if type(stage)!=int or not 1<=stage<=10 or type(approved)!=bool:
        return jsonify(error='Selecciona un reto válido.'),400
    with connection() as db:
        if not DATABASE_URL:
            sql(db,'BEGIN IMMEDIATE')
        row=sql(db,'SELECT * FROM submissions WHERE id=?'+(' FOR UPDATE' if DATABASE_URL else ''),(submission_id,)).fetchone()
        if not row:
            return jsonify(error='El registro ya no existe.'),404
        entry=result_entry(row);item=entry['comparison'][stage-1]
        if item['automatic_correct'] is not False:
            return jsonify(error='Solo se pueden validar respuestas marcadas como incorrectas.'),409
        previous=item['manual_approved']
        reviews=entry['manual_reviews']
        if previous!=approved:
            new_score=entry['score']+(1 if approved else -1)
            if not 0<=new_score<=10:
                return jsonify(error='El puntaje resultante debe estar entre 0 y 10.'),409
            reviews[str(stage)]=dict(approved=approved,reviewed_at=time.time())
            sql(db,'UPDATE submissions SET manual_reviews=?,score=? WHERE id=?',(json.dumps(reviews),new_score,submission_id))
        updated=sql(db,'SELECT * FROM submissions WHERE id=?',(submission_id,)).fetchone()
    return jsonify(success=True,result=result_entry(updated))


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
    return jsonify(teams=[dict(team=n,screen=CIRCUITS[n-1],ready=True) for n in range(1,6)])


@app.post('/api/monitor/advance-photo')
def monitor_advance():
    return jsonify(error='El reto de fotografía fue sustituido por Dilo con emojis.'),410

init_db()
if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5001)),debug=False)
