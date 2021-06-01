import asyncpraw
import urllib
import os

reddit = asyncpraw.Reddit(
    client_id=os.environ['CLIENT_ID'],
    client_secret=os.environ['CLIENT_SECRET'],
    user_agent="pallone:v0.0.0 (by u/square264)",
    username=os.environ['USERNAME'],
    password=os.environ['PASSWORD'],
)

already_done = []

async def get_submissions(subreddit : str, number : int):
    os.makedirs(f'submissions/{subreddit}', exist_ok=True)
    subreddit = await reddit.subreddit(subreddit)
    async for submission in subreddit.hot(limit=number):
        if submission.id not in already_done:
            try:
                url = submission.url
                request = urllib.request.Request(
                    url, headers={'User-Agent': 'Mozilla/5.0'})
                contents = urllib.request.urlopen(request).read()
                if url.endswith('.png'):
                    with open(f"submissions/{subreddit}/{submission.id}.png", "wb") as f:
                        f.write(contents)
                elif url.endswith('.jpg'):
                    with open(f"submissions/{subreddit}/{submission.id}.jpg", "wb") as f:
                        f.write(contents)
                already_done.append(submission.id)
            except Exception as e:
                print(e)

async def get_info(meme_id : str):
    submission = await reddit.submission(meme_id)
    return submission.title, submission.permalink, submission.score, submission.num_comments

if __name__ == '__main__':
    get_submissions('pallone', 15)