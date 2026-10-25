import json, os, sqlite3, unittest, uuid
from pathlib import Path
os.environ['DATABASE_URL']=''
os.environ['DB_PATH']=str(Path(__file__).parent/'instance'/('test-'+uuid.uuid4().hex+'.sqlite3'))
os.environ['SECRET_KEY']='test-secret'
import app as game

class GameTest(unittest.TestCase):
    def setUp(self):
        self.client=game.app.test_client()
        self.token=self.client.get('/api/state').json['csrf']
    def post(self,path,data,method='POST'):
        return self.client.open(path,method=method,json=data,headers={'X-CSRF-Token':self.token})
    def start(self,team=1,name='Club de prueba'):
        return self.post('/api/start',{'team':team,'club_name':name})
    def login(self):
        return self.post('/api/admin/login',{'password':'wobukeneng'})
    def finish(self,answers):
        response=None
        for stage,value in enumerate(answers):
            if stage==1:self.post('/api/mission/begin-timed',{})
            response=self.post('/api/answer',{'stage':stage,'answer':value})
            self.assertEqual(response.status_code,200)
            self.assertTrue(response.json['accepted'])
            self.assertNotIn('correct',response.json)
            self.assertEqual(response.json['mission']['stage'],stage+1)
        return response
    def test_five_teams_accept_wrong_and_score_individually(self):
        for team in range(1,6):
            with self.subTest(team=team):
                self.setUp()
                name=f'Gremio QA {team}'
                self.assertEqual(self.start(team,name).json['mission']['club_name'],name)
                expected=game.expected(team)
                answers=[a or 'pendiente' for a in expected]
                answers[0]=game.normalize(answers[0])+'.'
                answers[9]=game.normalize(answers[9])
                answers[2]='9';answers[8]='000'
                result=self.finish(answers)
                self.assertTrue(result.json['mission']['finished'])
                self.assertEqual(self.post('/api/answer',{'stage':9,'answer':'otra'}).status_code,409)
                self.assertEqual(self.client.get('/api/results').status_code,401)
                self.login()
                entry=next(r for r in self.client.get('/api/results').json['leaderboard'] if r['club']==name)
                self.assertEqual(entry['team'],team)
                self.assertEqual(entry['score'],7)
                self.assertEqual(entry['answers'],answers)
                self.assertFalse(entry['comparison'][2]['correct'])
                self.assertFalse(entry['comparison'][8]['correct'])
                self.assertIsNone(entry['comparison'][4]['correct'])
                self.assertEqual(entry['comparison'][3]['expected'],game.CIRCUITS[team-1])
                self.assertEqual(entry['comparison'][8]['expected'],game.CODES[team-1])
    def test_no_empty_answers_or_skipped_stages(self):
        self.assertEqual(self.client.post('/api/start',json={'team':1,'club_name':'QA'}).status_code,403)
        self.start()
        for value in ['', '   ',None,123,[]]:
            self.assertEqual(self.post('/api/answer',{'stage':0,'answer':value}).status_code,400)
            self.assertEqual(self.client.get('/api/state').json['mission']['stage'],0)
        self.assertEqual(self.post('/api/answer',{'stage':8,'answer':'251'}).status_code,409)
        self.assertEqual(self.post('/api/answer',{'stage':True,'answer':'1'}).status_code,409)
        self.assertFalse(self.post('/api/answer',{'stage':0,'answer':'incorrecta'}).json['accepted'])
        self.assertEqual(self.client.get('/api/state').json['mission']['stage'],0)
        self.post('/api/answer',{'stage':0,'answer':game.LOCATIONS[0]})
        self.assertEqual(self.post('/api/answer',{'stage':0,'answer':'otro clic'}).status_code,409)
    def test_names_and_assigned_teams(self):
        for team in [None,True,0,6,'1']:
            self.assertEqual(self.start(team).status_code,400)
        for name in [None,'','a',' '*6,'x'*61,'club\nno']:
            self.assertEqual(self.start(1,name).status_code,400)
        result=self.start(2,'  Club Ñandú  ')
        self.assertEqual(result.json['mission']['club_name'],'Club Ñandú')
        self.assertEqual(self.client.get('/api/state').json['mission']['club_name'],'Club Ñandú')
    def test_change_name_preserves_progress_and_team(self):
        self.start(5,'Nombre inicial')
        self.post('/api/answer',{'stage':0,'answer':game.LOCATIONS[4]})
        renamed=self.post('/api/mission/name',{'club_name':'Club con nombre nuevo'}).json['mission']
        self.assertEqual(renamed['club_name'],'Club con nombre nuevo')
        self.assertEqual(renamed['stage'],1)
        self.assertEqual(renamed['team'],5)
        self.assertEqual(renamed['answers'],[game.LOCATIONS[4]])
        self.post('/api/mission/begin-timed',{})
        for stage in range(1,10):self.post('/api/answer',{'stage':stage,'answer':'LA INGENIERIA ES EQUIPO' if stage==9 else 'pendiente' if stage==4 else '000' if stage==8 else '9'})
        self.assertEqual(self.post('/api/mission/name',{'club_name':'otro nombre'}).status_code,409)
    def test_configured_photo_and_expected_snapshot(self):
        original=game.photo
        game.photo=lambda team: {'url':'/static/challenges/aula.jpg','answer':'A001','destination':'aula A001'}
        try:
            self.start(3,'Foto con clave')
            self.finish(game.expected(3))
            game.photo=lambda team: {'url':'/otro.jpg','answer':'A002','destination':'otra aula'}
            self.login()
            entry=next(r for r in self.client.get('/api/results').json['leaderboard'] if r['club']=='Foto con clave')
            self.assertEqual(entry['score'],10)
            self.assertEqual(entry['comparison'][4]['expected'],'A001')
            self.assertTrue(entry['comparison'][4]['correct'])
        finally:game.photo=original
    def test_password_each_entry_and_deletion(self):
        self.start(1,'Registro descartable de pruebas')
        self.finish([game.LOCATIONS[0],'9','9','9','pendiente','9','9','9','000','LA INGENIERIA ES EQUIPO'])
        self.assertEqual(self.login().status_code,200)
        entry=next(r for r in self.client.get('/api/results').json['leaderboard'] if r['club']=='Registro descartable de pruebas')
        self.assertEqual(entry['score'],2)
        self.assertEqual(self.post('/api/results/'+entry['id'],{},'DELETE').status_code,403)
        self.assertEqual(self.post('/api/results/'+entry['id'],{'password':'incorrecta'},'DELETE').status_code,403)
        page=self.client.get('/leaderboard')
        self.assertIn('no-store',page.headers['Cache-Control'])
        self.assertEqual(self.client.get('/api/results').status_code,401)
        self.assertEqual(self.post('/api/admin/login',{'password':'incorrecta'}).status_code,401)
        self.login()
        self.assertEqual(self.post('/api/results/'+entry['id'],{'password':'wobukeneng'},'DELETE').status_code,200)
        self.client.get('/')
        self.assertEqual(self.client.get('/api/results').status_code,401)
    def test_migration_keeps_existing_rows(self):
        original_path=game.DB_PATH
        old_path=str(Path(original_path).with_name('old-'+uuid.uuid4().hex+'.sqlite3'))
        db=sqlite3.connect(old_path)
        db.execute("CREATE TABLE missions(id TEXT PRIMARY KEY,team INTEGER,started REAL,stage INTEGER,answers TEXT,attempts TEXT,finished INTEGER)")
        db.execute("CREATE TABLE submissions(id TEXT PRIMARY KEY,club TEXT,score INTEGER,time_ms INTEGER,answers TEXT)")
        db.execute('INSERT INTO missions VALUES (?,?,?,?,?,?,?)',('old-id',4,1.0,10,json.dumps(['x']*10),'[]',1))
        db.execute('INSERT INTO submissions VALUES (?,?,?,?,?)',('old-id','Nombre antiguo',3,12345,json.dumps(['x']*10)))
        db.commit();db.close()
        try:
            game.DB_PATH=old_path;game.init_db();game.init_db()
            with game.connection() as db:
                row=game.sql(db,'SELECT * FROM submissions WHERE id=?',('old-id',)).fetchone()
                self.assertEqual(row['club'],'Nombre antiguo');self.assertEqual(row['score'],3);self.assertEqual(row['time_ms'],12345)
            self.login()
            row=next(r for r in self.client.get('/api/results').json['leaderboard'] if r['id']=='old-id')
            self.assertEqual(row['team'],4)
            self.assertEqual(row['comparison'][3]['expected'],'5')
        finally:game.DB_PATH=original_path
    def test_first_gate_accepts_case_accents_and_punctuation(self):
        for team in range(1,6):
            with self.subTest(team=team):
                self.setUp();self.start(team,f'Primer reto {team}')
                result=self.post('/api/answer',{'stage':0,'answer':'respuesta incorrecta'})
                self.assertFalse(result.json['accepted'])
                self.assertEqual(self.client.get('/api/state').json['mission']['stage'],0)
                variant='... '+', '.join(game.LOCATIONS[team-1].upper().split())+'!!!'
                result=self.post('/api/answer',{'stage':0,'answer':variant})
                self.assertTrue(result.json['accepted'])
                self.assertEqual(result.json['mission']['stage'],1)
                self.post('/api/mission/begin-timed',{})
                for value in ['12','e','-1','２','']:
                    self.assertEqual(self.post('/api/answer',{'stage':1,'answer':value}).status_code,400)
                self.assertTrue(self.post('/api/answer',{'stage':1,'answer':'9'}).json['accepted'])
    def test_final_gate_requires_correct_message(self):
        self.start(1,'Mensaje final con validacion')
        answers=game.expected(1)
        for stage,target in enumerate(answers[:9]):
            if stage==1:self.post('/api/mission/begin-timed',{})
            response=self.post('/api/answer',{'stage':stage,'answer':target or 'PENDIENTE'})
            self.assertTrue(response.json['accepted'])
        wrong=self.post('/api/answer',{'stage':9,'answer':'UN MENSAJE INCORRECTO'})
        self.assertFalse(wrong.json['accepted'])
        self.assertEqual(self.client.get('/api/state').json['mission']['stage'],9)
        correct=self.post('/api/answer',{'stage':9,'answer':'la ingenieria es EQUIPO!'})
        self.assertTrue(correct.json['mission']['finished'])
    def test_previous_progress_survives_first_answer_correction(self):
        self.start(2,'Mision ya empezada')
        with self.client.session_transaction() as sess:mission_id=sess['mission']
        with game.connection() as db:
            game.sql(db,'UPDATE missions SET timed_started=started,stage=2,answers=? WHERE id=?',(json.dumps(['respuesta vieja incorrecta','9']),mission_id))
        self.assertEqual(self.client.get('/api/state').json['mission']['stage'],0)
        result=self.post('/api/answer',{'stage':0,'answer':game.LOCATIONS[1]})
        self.assertEqual(result.json['mission']['stage'],2)
        self.assertEqual(result.json['mission']['answers'],[game.LOCATIONS[1],'9'])
    def test_timer_waits_for_acknowledgement_and_cannot_restart(self):
        from unittest.mock import patch
        baseline=game.time.time()
        with patch.object(game.time,'time',return_value=baseline):
            self.assertIsNone(self.start().json['mission']['started'])
        self.assertEqual(self.post('/api/mission/begin-timed',{}).status_code,409)
        with patch.object(game.time,'time',return_value=baseline+1000):
            mission=self.post('/api/answer',{'stage':0,'answer':game.LOCATIONS[0]}).json['mission']
            self.assertTrue(mission['awaiting_start'])
            self.assertIsNone(mission['started'])
            self.assertEqual(mission['first_destination'],game.LOCATIONS[0])
            self.assertTrue(self.client.get('/api/state').json['mission']['awaiting_start'])
            self.assertEqual(self.post('/api/answer',{'stage':1,'answer':'4'}).status_code,409)
        with patch.object(game.time,'time',return_value=baseline+2000):
            self.assertEqual(self.post('/api/mission/begin-timed',{}).json['mission']['started'],baseline+2000)
        with patch.object(game.time,'time',return_value=baseline+3000):
            self.assertEqual(self.post('/api/mission/begin-timed',{}).json['mission']['started'],baseline+2000)
            for stage,target in enumerate(game.expected(1)[1:],1):
                result=self.post('/api/answer',{'stage':stage,'answer':target or 'PENDIENTE'})
                self.assertEqual(result.status_code,200)
            self.login()
            entry=next(r for r in self.client.get('/api/results').json['leaderboard'] if r['id']==self._mission_id())
            self.assertEqual(entry['time_ms'],1000000)
    def _mission_id(self):
        with self.client.session_transaction() as sess:return sess['mission']
    def test_classrooms_unique_stable_and_recalled_after_photo(self):
        rooms=[game.classroom(team) for team in range(1,6)]
        self.assertEqual(len(set(rooms)),5)
        game.init_db()
        self.assertEqual(rooms,[game.classroom(team) for team in range(1,6)])
        self.start(2)
        for stage,target in enumerate(game.expected(2)[:5]):
            if stage==1:self.post('/api/mission/begin-timed',{})
            result=self.post('/api/answer',{'stage':stage,'answer':target or 'PENDIENTE'})
        self.assertIn(rooms[1],result.json['message'])
        self.assertEqual(result.json['mission']['classroom'],rooms[1])
        self.assertEqual(self.client.get('/api/state').json['mission']['classroom'],rooms[1])
        self.assertEqual(self.post('/api/answer',{'stage':4,'answer':'PENDIENTE'}).status_code,409)
    def test_word_banks_and_circuits(self):
        for team in range(1,6):
            self.assertEqual(str((((2|3)&(~(2&3)&15))^team)),game.CIRCUITS[team-1])
            phrase=' '.join(game.BANKS[team-1][int(n)-1] for n in game.CODES[team-1]+'4')
            self.assertEqual(game.normalize(phrase),'la ingenieria es equipo')

if __name__=='__main__':unittest.main()
