This project is a news checker. It allows a user to make calls to the Reddit API in the /r/news subreddit 
These calls are based on topic, number of items to see, period the posts are from, and how to sort the response

Responses from calls to the /r/news subreddit are matched against a news 'bias' database available through UM. 
(see data_description.txt)

The current repo does not include all the pieces needed for the code to run successfully, as it is missing the database 
and cleaned csv files. I uploaded the bare minimum to make the code run to allow the teaching team to see it work fully.
When you first fun the code, then, you must add --init to the end of the command line (e.g. Python3 FinalProj_V4.py --init)
This will create two other csv files and a database in your working dir.

The code begins by cleaning a .tsv file I captured from the online database. This file is processed to clean it up as a csv and
create 'bias' scores from the DemVote and RepVote columns. Then, I create another csv that is the aggregation of the bias 
scores merged by news source. I then create a db with those files.

The other data collection function is get_reddit_data, which authenticates the user (based on secret.py -- YOU WILL NEED THIS)
and allows for searches to the /r/news subreddit. 

The help.txt document will be a good resource for running the program. Broadly, you can ask to search the subreddit or graph 
results from your search. Searches also always have console output that (I hope) is nicely formatted

