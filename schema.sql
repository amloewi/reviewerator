DROP TABLE reviewer;
DROP TABLE submission cascade;
DROP TABLE finished;
DROP TABLE alert;
DROP TABLE review;
DROP TABLE review_review;


CREATE TABLE person (
	--ID SERIAL PRIMARY KEY,
	id char(30) PRIMARY KEY, -- login name for the system (no password)
	name char(50),		-- The name that appears in system emails etc.
	email char(50),
	year INTEGER, -- year in the program
	milestone char(20), -- None, 1st Paper, 2nd Paper, or Proposal
	expertise TEXT, -- statistics, economics, IS, etc. Comma delimited.
	
	submitted INTEGER, -- num papers submitted
	reviewed INTEGER, -- num papers reviewed
	passes INTEGER, -- current number of 'pass' actions. Too many you're out.
	dropped INTEGER, -- num reviews accepted and not done.
	
	active_requests INTEGER, -- number of requests you're currently fielding
	active_submissions INTEGER, -- number of submissions you have out
	
	started TIMESTAMP, -- profile creation date
	last_review TIMESTAMP
	
	enabled BOOLEAN, -- 1/0 for are they 1) a student, and 2) haven't dropped 
					-- a review recently
);

CREATE TABLE paper (
	id SERIAL PRIMARY KEY,
	author char(30), -- author's id
	title TEXT,
	abstract TEXT,
	requested_expertise TEXT,
	notes TEXT,
	timeline INTEGER, -- number of days requested for turnaround
	date TIMESTAMP -- date of submission
);

CREATE TABLE assignment (
	submission INT, -- The id of the related submission
	assigned_reviewer char(30),
	reviewer char(30),
	candidates TEXT, -- list of next possibilities
	kind CHAR(10), -- jr/sr
	active BOOLEAN,
	accepted BOOLEAN,
	completed BOOLEAN
);


CREATE TABLE active_submission (
	-- anything?
) INHERITS (submission);

-- Sits around in the box of an active reviewer. 
-- They signal the review is finished by clicking it.
CREATE TABLE finished (
	reviewer TEXT,
	requester TEXT
);

CREATE TABLE alert (
	recipient TEXT, -- the intended recipient
	message TEXT, -- either 'you have a reviewer' or 'you have a review due'
	reveal_if_after DATE -- when it should be sent to the inbox
);

CREATE TABLE review (
	ID SERIAL PRIMARY KEY,
	reviewer TEXT,
	author TEXT,
	title TEXT,
	returned TIMESTAMP,
	on_time INTEGER -- 1 for yes, 0 for no .. they must have booleans though
	--tf BOOLEAN
	-- CONTENT, NOTES, UPLOAD IT, ETC.
	
	-- FEATURES OF THE REVIEWERS. As well. Their -- expertise, timing, and ...
	-- milestone, I think.
);

CREATE TABLE review_review (
	ID SERIAL PRIMARY KEY,
	submission INTEGER, -- the ID for the submission
	review INTEGER, -- the ID for the review
	satisfaction INTEGER -- 1-7 satisfaction Likert.
);


-- CREATE TABLE reviewer_submission (
-- 	reviewer TEXT,
-- 	submission INTEGER,
-- );
-- 
-- 
-- -- necessary to 
-- CREATE TABLE reviewer_review (
-- 	reviewer TEXT,
-- 	submission INTEGER,
-- );

-- reviewer_review?


