import asyncpraw
import urllib
import os

import util

reddit = asyncpraw.Reddit(
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET'),
    user_agent="pallone:v0.0.0 (by u/square264)",
    username=os.getenv('REDDIT_USERNAME'),
    password=os.getenv('PASSWORD'),
)


async def get_submissions(subreddit: str, number: int, trace=False):
    os.makedirs(f'submissions/{subreddit}', exist_ok=True)
    subreddit = await reddit.subreddit(subreddit)
    async for submission in subreddit.hot(limit=number):
        if submission.id + '.png' in os.listdir(f'submissions/{subreddit}') or submission.id + '.jpg' in os.listdir(f'submissions/{subreddit}'):
            break
        try:
            url = submission.url
            request = urllib.request.Request(
                url, headers={'User-Agent': 'Mozilla/5.0'})
            contents = urllib.request.urlopen(request).read()
            if url.endswith('.png'):
                with open(f"submissions/{subreddit}/{submission.id}.png", "wb") as f:
                    f.write(contents)
                if trace:
                    print('Read meme',
                          f"submissions/{subreddit}/{submission.id}.png")
            elif url.endswith('.jpg'):
                with open(f"submissions/{subreddit}/{submission.id}.jpg", "wb") as f:
                    f.write(contents)
                if trace:
                    print('Read meme',
                          f"submissions/{subreddit}/{submission.id}.jpg")
        except Exception as e:
            if trace:
                print(e)
    if trace:
        print('Done reading memes')


async def get_info(meme_id: str):
    submission = await reddit.submission(meme_id)
    return submission.title, submission.permalink, submission.score, submission.num_comments

if __name__ == '__main__':
    get_submissions('pallone', 15)
