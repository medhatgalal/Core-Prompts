-- Supplied design context; do not execute or modify. PostgreSQL.
CREATE TABLE authors (author_id BIGINT PRIMARY KEY, display_name TEXT NOT NULL);
CREATE TABLE books (
  book_id BIGINT PRIMARY KEY,
  author_id BIGINT NOT NULL REFERENCES authors(author_id),
  title TEXT NOT NULL,
  published_on DATE NOT NULL
);
CREATE INDEX books_published ON books (published_on DESC, book_id DESC);
