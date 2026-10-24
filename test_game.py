import importlib.util, json, os, tempfile, unittest
from pathlib import Path
os.environ.pop('DATABASE_URL',None)
import uuid
os.environ['DB_PATH']=str(Path(__file__).parent/'instance'/('test-'+uuid.uuid4().hex+'.sqlite3'))
os.environ['SECRET_KEY']='test-secret'
import app as game
class GameTest(unittest.TestCase):
    def setUp(self):
        self.client=game.app.test_client()
        self.token=self.client.get('/api/state').json['csrf']
    def post(self,path,data,method='POST'):
        return self.client.open(path,method=method,json=data,headers={'X-CSRF-Token':self.token})
    def test_five_teams(self):
        for team in range(1,6):
            with self.subTest(team=team):
                self.client=game.app.test_client();self.token=self.client.get('/api/state').json['csrf']
                r=self.post('/api/start',{'team':team});self.assertEqual(r.status_code,200)
                self.assertNotIn('correct_answers',r.json)
                for stage,target in enumerate(game.expected(team)):
                    if stage==4:
                        self.assertTrue(r.json['mission']['photo']['pending'])
                        self.assertEqual(self.post('/api/answer',{'stage':4,'answer':'inventado'}).status_code,409)
                        self.assertEqual(self.post('/api/monitor/advance-photo',{'password':'wrong'}).status_code,403)
                        r=self.post('/api/monitor/advance-photo',{'password':'wobukeneng'})
                    else:
                        wrong=self.post('/api/answer',{'stage':stage,'answer':'incorrecto'})
                        self.assertFalse(wrong.json['correct'])
                        self.assertEqual(self.client.get('/api/state').json['mission']['stage'],stage)
                        if stage in (0,9):target=game.normalize(target)+'.'
                        r=self.post('/api/answer',{'stage':stage,'answer':target})
                        self.assertTrue(r.json['correct'])
                    self.assertEqual(r.json['mission']['stage'],stage+1)
                self.assertTrue(r.json['mission']['finished'])
                self.assertEqual(self.post('/api/answer',{'stage':9,'answer':'LA INGENIERIA ES EQUIPO'}).status_code,409)
                self.assertEqual(self.client.get('/api/results').status_code,401)
                self.assertEqual(self.post('/api/admin/login',{'password':'wobukeneng'}).status_code,200)
                rows=self.client.get('/api/results').json['leaderboard']
                entry=next(e for e in rows if e['club']==f'Equipo {team}')
                self.assertEqual(entry['score'],9)
                self.assertGreaterEqual(entry['time_ms'],0)
                self.assertEqual(self.post('/api/results/'+entry['id'],{},'DELETE').status_code,403)
                self.assertEqual(self.post('/api/results/'+entry['id'],{'password':'wrong'},'DELETE').status_code,403)
                self.assertEqual(self.post('/api/results/'+entry['id'],{'password':'wobukeneng'},'DELETE').status_code,200)
    def test_csrf_and_validation(self):
        self.assertEqual(self.client.post('/api/start',json={'team':1}).status_code,403)
        for team in [None,True,0,6,'1']:
            self.assertEqual(self.post('/api/start',{'team':team}).status_code,400)
        self.post('/api/start',{'team':1})
        self.assertEqual(self.post('/api/answer',{'stage':8,'answer':'251'}).status_code,409)
        self.assertEqual(self.post('/api/answer',{'stage':0,'answer':123}).status_code,400)
    def test_word_banks_and_circuits(self):
        for team in range(1,6):
            self.assertEqual(str((((2|3)&(~(2&3)&15))^team)),game.CIRCUITS[team-1])
            phrase=' '.join(game.BANKS[team-1][int(n)-1] for n in game.CODES[team-1]+'4')
            self.assertEqual(game.normalize(phrase),'la ingenieria es equipo')
if __name__=='__main__':unittest.main()
