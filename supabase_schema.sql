-- Colleges Table
CREATE TABLE colleges (
    college_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    address TEXT NOT NULL,
    password TEXT NOT NULL
);

-- Students Table
CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    roll_no TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    year TEXT NOT NULL,
    branch TEXT NOT NULL,
    college_id INTEGER REFERENCES colleges(college_id) ON DELETE CASCADE
);

-- Judges Table
CREATE TABLE judges (
    judge_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    password TEXT NOT NULL,
    college_id INTEGER REFERENCES colleges(college_id) ON DELETE CASCADE
);

-- Hackathons Table
CREATE TABLE hackathons (
    hackathon_id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    post_date DATE NOT NULL,
    deadline DATE NOT NULL,
    prizes TEXT,
    poster_url TEXT,
    college_id INTEGER REFERENCES colleges(college_id) ON DELETE CASCADE
);

-- Ideas Table
CREATE TABLE ideas (
    idea_id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(student_id) ON DELETE CASCADE,
    hackathon_id INTEGER REFERENCES hackathons(hackathon_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    prototype TEXT
);

-- Scores Table
CREATE TABLE scores (
    score_id SERIAL PRIMARY KEY,
    idea_id INTEGER REFERENCES ideas(idea_id) ON DELETE CASCADE,
    judge_id TEXT REFERENCES judges(judge_id) ON DELETE CASCADE,
    score INTEGER CHECK (score >= 1 AND score <= 10)
);

-- Disable RLS on all tables
ALTER TABLE colleges DISABLE ROW LEVEL SECURITY;
ALTER TABLE students DISABLE ROW LEVEL SECURITY;
ALTER TABLE judges DISABLE ROW LEVEL SECURITY;
ALTER TABLE hackathons DISABLE ROW LEVEL SECURITY;
ALTER TABLE ideas DISABLE ROW LEVEL SECURITY;
ALTER TABLE scores DISABLE ROW LEVEL SECURITY;

-- Create bucket for hackathon posters (do this in Supabase Storage UI):
-- Bucket name: hackathon_posters 