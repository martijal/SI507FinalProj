### SI507 final project ###
import csv
import json
import sys
import sqlite3
import requests
import requests.auth
import praw
import plotly.graph_objs as go
from secret import *


"""this version uses PRAW instead of the base reddit API. It also works, unlike the other version"""

### Part 1: Read and process the media bias cvs ###
### Import the csv file ###
NEWS_TSV = 'newsArticlesWithLabels.tsv'
NEWS_CSV_CLEAN = 'cleanedNewsArticles.csv'
NEWS_OUTLETS = 'NewsOutlets.csv'
CACHE_FNAME = 'reddit_cache.json'
AUTH_CACHE_FNAME = 'reddit_auth_cache.json'
DBNAME = 'news.db'


def clean_csv_data():
    """This function will be called in init_db
    The fuction does two things:
    1. Opens newsArticlesWithLabels.tsv, and re-writes it as a .csv with the colums in full_data. 
        This file will be saved to the local directory and imported into the db
    2. returns a list of news outlets from the newsArticlesWithLabels file with their aggregated 'bias score'"""
    
    url = []
    PrimaryTopic = []
    SecondaryTopic = []
    DemVote_T = []
    RepVote_T = []
    DemVote = []
    RepVote = []
    pub_name = []
    full_data = zip(url, pub_name, PrimaryTopic, SecondaryTopic, DemVote_T, RepVote_T, DemVote, RepVote)
    
    with open('newsArticlesWithLabels.tsv') as tsvDataFile:
        csvReader = csv.reader(tsvDataFile, delimiter = '\t')
        for row in csvReader:
            if row[0] != 'url':
                url.append(row[0])
                PrimaryTopic.append(row[3])
                SecondaryTopic.append(row[4])
                DemVote_T.append(row[5])
                RepVote_T.append(row[6])
                
    for i in url:
        if i.split(".")[1] != "blogs" and i.split(".")[1] != "money" and i.split(".")[1] != "fortune" and i.split(".")[1] != "news": 
            publisher = i.split(".")[1]
        else:
            publisher = i.split(".")[2]
        pub_name.append(publisher)
    
    for vote in range(0, len(DemVote_T)):
        if DemVote_T[vote] == "Negative":
            DemVote.append(2)
        elif DemVote_T[vote] == "SomewhatNegative":
            DemVote.append(1)
        elif DemVote_T[vote] == "Neutral":
            DemVote.append(0)
        elif DemVote_T[vote] == "SomewhatPositive":
            DemVote.append(-1)
        elif DemVote_T[vote] == "Positive":
            DemVote.append(-2)

    for vote in range(0, len(RepVote_T)):
        if RepVote_T[vote] == "Negative":
            RepVote.append(-2)
        elif RepVote_T[vote] == "SomewhatNegative":
            RepVote.append(-1)
        elif RepVote_T[vote] == "Neutral":
            RepVote.append(0)
        elif RepVote_T[vote] == "SomewhatPositive":
            RepVote.append(1)
        elif RepVote_T[vote] == "Positive":
            RepVote.append(2)
    
    
    full_data = zip(url, pub_name, PrimaryTopic, SecondaryTopic, DemVote_T, RepVote_T, DemVote, RepVote)
    with open(NEWS_CSV_CLEAN, "w", newline="") as f:
        writer = csv.writer(f)
        for row in full_data:
            writer.writerow(row)
    
    pub_name_unique = {}
    for i in range(0, len(pub_name)):
        score = DemVote[i] + RepVote[i]
        if pub_name[i] not in pub_name_unique.keys():
            pub_name_unique[pub_name[i]] = score
        else:
            pub_name_unique[pub_name[i]] += score
            
    with open(NEWS_OUTLETS, 'w', newline="") as csv_file:  
        writer = csv.writer(csv_file)
        for key, value in pub_name_unique.items():
           writer.writerow([key, value])



def init_db():
    """This function will create the database that houses our """
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    # Drop tables
    statement = '''
        DROP TABLE IF EXISTS 'NewsOutlets';
    '''
    cur.execute(statement)
    
    statement = '''
        DROP TABLE IF EXISTS 'AllNewsSet';
    '''
    cur.execute(statement)
    
    conn.commit()


    statement = '''
        CREATE TABLE 'NewsOutlets' (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                'Outlet' TEXT,
                'BiasScore' TEXT
        );
    '''
    cur.execute(statement)
    

    statement = '''
        CREATE TABLE 'AllNewsSet' (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                'URL' TEXT,
                'DemVote' INTEGER,
                'RepVote' INTEGER,
                'OutletName' TEXT,
                'OutletId' INTEGER
        );
    '''
    cur.execute(statement)
    
    conn.commit()
    
    
    ### Now that the database is created, populate the data ###
    ### Start by checking if the correct files are available. Create them with clean_csv_data() if not###
    try:
        all_news = open(NEWS_CSV_CLEAN)
        news_outlets = open(NEWS_OUTLETS)
        all_news.close()
        news_outlets.close()
        print("No need to update csv data")
    except:
        print("Updating csv data...")
        clean_csv_data()

        
    
    ### Create temp AllNews file. Including news_outlet names now. Will remove later after matching to the NewsOutlet foriegn key
    with open(NEWS_CSV_CLEAN) as all_news:
        news = csv.reader(all_news)
        for row in news:
            insertion = (None, row[0], row[4], row[5], row[1], None)
            statement = 'INSERT INTO "AllNewsSet" '
            statement += 'VALUES (?, ?, ?, ?, ?, ?)'
            cur.execute(statement, insertion)

            conn.commit()
    
    with open(NEWS_OUTLETS) as csvData:
        news_outlets = csv.reader(csvData)
        for row in news_outlets:
            insertion = (None, row[0], row[1])
            statement = 'INSERT INTO "NewsOutlets" '
            statement += 'VALUES (?, ?, ?)'
            cur.execute(statement, insertion)

            conn.commit()
    
    
    ### Update foriegn key info in AllNewsSet
    statement = '''UPDATE AllNewsSet
                    SET
                        (OutletId) = (SELECT NewsOutlets.Id
                                FROM NewsOutlets
                                WHERE NewsOutlets.Outlet = AllNewsSet.OutletName)
                    WHERE
                        EXISTS (
                            SELECT *
                            FROM NewsOutlets
                            WHERE NewsOutlets.Outlet = AllNewsSet.OutletName)
    '''
    cur.execute(statement)
    conn.commit()
    
    conn.close()

if len(sys.argv) > 1 and sys.argv[1] == '--init':
    print('Deleting db and starting over from scratch.')
    init_db()
else:
    print('Leaving the DB alone.')



### Pull data from reddit/figure out the API
### Cache response data
## uniq_url_combo
## try/except with cache file
def params_unique_combo(baseurl, params):
    alphabetized_keys = sorted(params.keys())
    res = []
    for k in alphabetized_keys:
        res.append("{}-{}".format(k, params[k]))
    return baseurl + "_".join(res)
    
    
def reddit_cache(baseurl, pd):   
    ### open cache file ###
    try:
        with open(CACHE_FNAME) as my_data:
            CACHE_DICTION = json.load(my_data)
        my_data.close()
    except:
        CACHE_DICTION = {}
    
    uniq_url = params_unique_combo(baseurl, pd)
    
    if uniq_url in CACHE_DICTION.keys():
        pass
    else:
        new_request = requests.get(baseurl, pd)
        try:
            CACHE_DICTION[uniq_url] = new_request.json()
            with open(CACHE_FNAME, 'w') as outfile:
                outfile.write(json.dumps(CACHE_DICTION, indent=2))
            outfile.close()
        except:
            print("Request failed. Following was returned: {}".format(new_request))
            return {}

    return CACHE_DICTION[uniq_url]


class RedditPost():
    def __init__(self, title=None, score=0, post_id=None, url=None, comms_num=0, body=None, json=None):
        try:
            self.title = json['title']
            self.score = json['score']
            self.post_id = json['post_id']
            self.url = json['url']
            self.comms_num = json['comms_num']
            self.body = json['body']

        
            for i in self.url.split(":"):
                pass
            url_temp = self.url.split(":")
            if url_temp[1][2:5] != "www":
                url_temp = url_temp[1]
                self.outlet = url_temp.split(".")[0][2:]
            elif self.url.split(".")[1] != "blogs" and i.split(".")[1] != "money" and i.split(".")[1] != "fortune" and i.split(".")[1] != "news": 
                self.outlet = self.url.split(".")[1]
            else:
                self.outlet = self.url.split(".")[2]
                
        except:
            if json != None:
                print("unable to parse json file. It may not have the information requested")
            self.title = title
            self.score = score
            self.post_id = post_id
            self.url = url
            self.comms_num = comms_num
            self.body = body
            self.outlet = None
        
    def __str__(self):
        return "Post Title: {}\nPost Score: {}\nNews Outlet: {}\n".format(self.title, self.score, self.outlet)
        
        


def get_reddit_data(query=None, limit=25, sort='hot', time_filter='all'):
    """function to get reddit data. Allows for most search functions to be changed.
    q will come from user input
    Caching will be implemented within this fuction instead of as a separate function
    Function will always return a list. This list is either empty or contains reddit_post class objects"""
    ### Open cache file
    try:
        with open(CACHE_FNAME) as my_data:
            CACHE_DICTION = json.load(my_data)
        my_data.close()
    except:
        CACHE_DICTION = {}
    
    
    ### clean up and handle bad user input ###
    sort = sort.lower()
    time_filter = time_filter.lower()
    query = query.lower()
    limit = int(limit)

    if type(limit) != type(0):
        print("DIDNT RECOGNIZE LIMIT")
        limit = 25
    if limit < 0:
        limit = abs(limit)
    if limit > 100:
        limit = 100
    if sort not in ['hot', 'top', 'new']:
        sort = 'hot'
    if time_filter not in ['hour', 'year', 'day', 'all', 'month', 'week']:
        time_filter = 'all'
    
    ### build uniq url elements for cache
    baseurl = "https://www.reddit.com/r/news/search/"
    pd = {}
    pd['query'] = query
    pd['limit'] = limit
    pd['sort'] = sort # can be one of hot, new, or top
    pd['time_filter'] = time_filter
    
    uniq_url = params_unique_combo(baseurl, pd)
    
    if uniq_url in CACHE_DICTION.keys():
        print("retrieving cached result")
    else:
        ### create a reddit instance and build the request
        reddit = praw.Reddit(client_id = CLIENT_ID,
                            client_secret = REDDIT_SECRET,
                            username = USERNAME,
                            password = PASSWORD,
                            user_agent = USER_AGENT)
        subreddit = reddit.subreddit('news')
        
        submissions = subreddit.search(query=query, limit=limit, sort=sort, time_filter=time_filter)
        
        ### Create dictionary of posts based on submissions ###
        submission_list = []
        for submission in submissions:
            sub_info = dict(
                title = submission.title,
                score = submission.score,
                post_id = submission.id,
                url = submission.url,
                comms_num = submission.num_comments,
                body = submission.selftext
            )
            submission_list.append(sub_info)
            
        try:
            CACHE_DICTION[uniq_url] = submission_list
            with open(CACHE_FNAME, 'w') as outfile:
                outfile.write(json.dumps(CACHE_DICTION, indent=2))
            outfile.close()
        except:
            print("Request failed. Following was returned: {}".format(new_request))
            return {}
    
    
    reddit_posts = []
    for post in CACHE_DICTION[uniq_url]:
        reddit_posts.append(RedditPost(json=post))
    
    
    return reddit_posts
    # return subreddit.search(query="trump", limit=5, sort='top', time_filter='all')
            

    
# news1 = get_reddit_data(query="hong kong", limit=50, sort="hot", time_filter='all')
# print("length of response: {}".format(str(len(news1))))
# counter=1
# for i in news1:
#     print(counter)
#     print(i)
#     counter +=1


def plot_scores(reddit_obj_lst):
    """This function will plot number of upvotes on bias score for each reddit_obj with a matching outlet"""
    f=open('NewsOutlets.csv')
    csv_data = csv.reader(f)
    
    score_dict = {}
    for row in csv_data:
        score_dict[row[0]] = row[1]
    
    bias_vals = []
    text_vals = []
    score_vals = []
    
    for reddit_obj in reddit_obj_lst:
        if reddit_obj.outlet in score_dict.keys():
            score_vals.append(reddit_obj.score)
            text_vals.append("{} from {}".format(reddit_obj.title, reddit_obj.outlet))
            bias_vals.append(score_dict[reddit_obj.outlet])
    
    trace = go.Scatter(
        x = bias_vals,
        y = score_vals,
        text = text_vals,
        mode = 'markers'
    )
    data=[trace]
    fig = go.Figure(data=data)
    fig.update_layout(
        title = "Reddit submission scores plotted against news source 'bias' score<br>(Hover for scores and titles)"
    )
    fig.show()
    f.close()
    pass
    
    
def plot_comments(reddit_obj_lst):
    """This function will plot number of comments on bias score for each reddit_obj with a matching outlet"""
    f=open('NewsOutlets.csv')
    csv_data = csv.reader(f)
    
    score_dict = {}
    for row in csv_data:
        score_dict[row[0]] = row[1]
    
    bias_vals = []
    text_vals = []
    comm_vals = []
    
    for reddit_obj in reddit_obj_lst:
        if reddit_obj.outlet in score_dict.keys():
            comm_vals.append(reddit_obj.comms_num)
            text_vals.append("{} from {}".format(reddit_obj.title, reddit_obj.outlet))
            bias_vals.append(score_dict[reddit_obj.outlet])
    
    trace = go.Scatter(
        x = bias_vals,
        y = comm_vals,
        text = text_vals,
        mode = 'markers'
    )
    data=[trace]
    fig = go.Figure(data=data)
    fig.update_layout(
        title = "Reddit submission comment numbers plotted against news source 'bias' score<br>(Hover for scores and titles)"
    )
    fig.show()
    f.close()
    pass
    
    
def plot_outlets(reddit_obj_lst):
    """This function will plot all outlets in a reddit_obj_lst and how many times they're included in the list"""
    outlet_dict = {}
    for reddit_obj in reddit_obj_lst:
        if reddit_obj.outlet not in outlet_dict.keys():
            outlet_dict[reddit_obj.outlet] = 1
        else:
            outlet_dict[reddit_obj.outlet] += 1
            
    outlet = tuple(outlet_dict.keys())
    outlet_vals = tuple(outlet_dict.values())
    
    fig = go.Figure(data=go.Bar(y=outlet_vals, x=outlet))
    fig.update_layout(
        title = "All news outlets from your search and the number of time they were cited"
    )
    fig.show()
    pass

# plot_outlets(news1)

def plot_bias_data():
    """Static plot of each of the 15 outlets and their 'bias' scores"""
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    sql = '''
        SELECT Outlet, BiasScore FROM NewsOutlets
    '''
    results = cur.execute(sql)
    result_list = results.fetchall()
    
    outlets = []
    outlet_bias = []
    
    for i in result_list:
        outlets.append(i[0])
        outlet_bias.append(i[1])
        
    outlets = tuple(outlets)
    outlet_bias = tuple(outlet_bias)
    
    fig = go.Figure(data=go.Bar(y=outlet_bias, x=outlets))
    fig.update_layout(
        title = "Surveyed news outlets and their composit 'bias' scores"
    )
    fig.show()
    
    
    conn.close()
    return result_list


def load_help_text():
    with open('help.txt') as f:
        return f.read()


def interactive_prompt():
    help_text = load_help_text()
    response = input('Enter a command (or "help" for options): ')
    while response != 'exit':
        response = response.lower()
        if response == 'exit':
            print("Bye!")
            break
            
        elif response == 'help':
            print(help_text)
            response = input('Enter a command (or "help" for options): ')
            
        elif response == 'search':
            query = input("what topic do you want to search for? ")
            limit = input("How many results do you want to see (1-100)? ")
            sort = input("How should we sort the results (hot, top, or new)? ")
            time_filter = input("Over what period of time (hour, day, week, month, year, or all)? ")
            
            reddit_q = get_reddit_data(query=query, limit=limit, sort=sort, time_filter=time_filter)
            counter = 1
            for i in reddit_q:
                print(counter)
                print(i)
                counter += 1
                
            response = input('Enter a command (or "help" for options): ')
            response = response.lower()
            
            if response != 'graph':
                pass
            else:
                while response == 'graph':
                    graph = input('What would you like to graph? ')
                    graph = graph.lower()
                    
                    if graph == 'bias_data':
                        plot_bias_data()
                    elif graph == 'scores':
                        plot_scores(reddit_q)
                    elif graph == 'comments':
                        plot_comments(reddit_q)
                    elif graph == 'outlets':
                        plot_outlets(reddit_q)
                    elif graph == 'break':
                        break
                    elif graph == 'help':
                        print(help_text)
                    else:
                        print("Note a valid graphing input")
                        
                    response = input('Type "graph" if you would like to make another graph with this data\n Otherwise, enter a command: ')
                    
        elif response == 'graph':
            print("you can only graph the bias_data right now")
            graph = input('Would you like to graph the bias data (yes/no)? ')
            graph = graph.lower()
            
            if graph == 'yes':
                plot_bias_data()
                
            response = input('Enter a command (or "help" for options): ')
        else:
            response = input('Not a valid command. Enter a new command (or "help" for options): ')
            
#
# if __name__=="__main__":
#     interactive_prompt()
