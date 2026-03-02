PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS posts (
  post_id TEXT PRIMARY KEY,
  created_utc INTEGER NOT NULL,
  subreddit TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  url TEXT NOT NULL,
  score INTEGER NOT NULL DEFAULT 0,
  num_comments INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_posts_created_utc ON posts(created_utc DESC);
CREATE INDEX IF NOT EXISTS idx_posts_subreddit ON posts(subreddit);
CREATE INDEX IF NOT EXISTS idx_posts_title ON posts(title);

CREATE TABLE IF NOT EXISTS comments (
  comment_id TEXT PRIMARY KEY,
  post_id TEXT NOT NULL,
  created_utc INTEGER NOT NULL,
  parent_id TEXT,
  body TEXT NOT NULL,
  score INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_created_utc ON comments(created_utc DESC);