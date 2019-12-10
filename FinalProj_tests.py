import unittest
from FinalProj_V4 import *

class TestDatabase(unittest.TestCase):

    def test_bar_table(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        url = "http://www.foxnews.com/politics/2013/04/03/obamacare-in-trouble-exchange-provision-delayed-as-lawmakers-push-to-repeal/"
        sql = 'SELECT URL FROM AllNewsSet'
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn((url,), result_list)
        self.assertEqual(len(result_list), 21004)

        sql = '''
            SELECT OutletId, DemVote
            FROM AllNewsSet
            WHERE OutletId = 1
            ORDER BY DemVote
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertEqual(len(result_list), 1450)
        self.assertEqual(result_list[0][1], "Negative")

        conn.close()
        
    
    def test_joins(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = '''
            SELECT BiasScore, COUNT(*)
            FROM NewsOutlets
                JOIN AllNewsSet
                ON NewsOutlets.Id = AllNewsSet.OutletId
            WHERE NewsOutlets.Outlet="bbc"
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0][1], 1252)
        self.assertEqual(result_list[0][0], '-67')
        conn.close()    
        
class TestRedditClass(unittest.TestCase):
    
    def testReddit(self):
        r1 = RedditPost(title="Test title for class", score = 100001, post_id="aLpHAnUm3rik", body = "Test Body")
        r2 = RedditPost()
        
        self.assertEqual(r1.__str__(), "Post Title: Test title for class\nPost Score: 100001\nNews Outlet: None\n")
        self.assertEqual(r2.score, 0)
        
        
class TestRedditAPI(unittest.TestCase):
    
    def test_search(self):
        reddit1 = get_reddit_data(query="hong kong", limit=10, sort='hot', time_filter='year')
        reddit2 = get_reddit_data(query="trump", limit=50, sort='top', time_filter='all')
        
        self.assertLessEqual(len(reddit1), 10)
        self.assertLessEqual(len(reddit2), 50)
        self.assertIsInstance(reddit1[1], RedditPost)
        
        
        
class TestMapping(unittest.TestCase):

    # we can't test to see if the maps are correct, but we can test that
    # the functions don't return an error!
    
    
    def test_show_scores(self):
        reddit1 = get_reddit_data(query="hong kong", limit=10, sort='hot', time_filter='year')
        reddit2 = get_reddit_data(query="trump", limit=50, sort='top', time_filter='all')
        try:
            plot_scores(reddit2)
            plot_scores(reddit1)
        except:
            self.fail()

    def test_show_comments(self):
        reddit1 = get_reddit_data(query="hong kong", limit=10, sort='hot', time_filter='year')
        reddit2 = get_reddit_data(query="trump", limit=50, sort='top', time_filter='all')
        try:
            plot_comments(reddit2)
            plot_comments(reddit1)
        except:
            self.fail()
            
    def test_show_outlets(self):
        reddit1 = get_reddit_data(query="hong kong", limit=10, sort='hot', time_filter='year')
        reddit2 = get_reddit_data(query="trump", limit=50, sort='top', time_filter='all')
        try:
            plot_outlets(reddit2)
            plot_outlets(reddit1)
        except:
            self.fail()
            
    def test_bias_ratings(self):
        reddit1 = get_reddit_data(query="hong kong", limit=10, sort='hot', time_filter='year')
        reddit2 = get_reddit_data(query="trump", limit=50, sort='top', time_filter='all')
        try:
            plot_bias_data()
        except:
            self.fail()

if __name__ == '__main__':
    unittest.main(verbosity=2)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        