DROP TABLE submission cascade;
DROP TABLE finished;
DROP TABLE alert;
DROP TABLE review;
DROP TABLE review_review;


CREATE TABLE reviewer (
	--ID SERIAL PRIMARY KEY,
	login TEXT PRIMARY KEY, -- login name for the system (no password)
	name TEXT,		-- The name that appears in system emails etc.
	email TEXT,
	year INTEGER, -- year in the program
	milestone TEXT, -- None, 1st Paper, 2nd Paper, or Proposal
	expertise TEXT, -- statistics, economics, IS, etc. Comma delimited.
	submitted INTEGER, -- num papers submitted
	reviewed INTEGER, -- num papers reviewed
	useful INTEGER, -- number of reviews considered useful
	passes INTEGER, -- current number of 'pass' actions. Too many you're out.
	dropped INTEGER, -- num reviews accepted and not done.
	started TIMESTAMP, -- profile creation date
	enabled INTEGER, -- 1/0 for are they 1) a student, and 2) haven't dropped 
					-- a review recently
	active_requests INTEGER, -- number of requests you're currently fielding
	active_submissions INTEGER, -- number of submissions you have out
	last_review TIMESTAMP
);

CREATE TABLE submission (
	ID SERIAL PRIMARY KEY,
	login TEXT,
	title TEXT,
	abstract TEXT,
	assigned_reviewer_1 TEXT,
	assigned_reviewer_2 TEXT,
	reviewer_1 TEXT, -- actual reviewer, if assigned_1 turned it down
	reviewer_2 TEXT,
	requested_expertise TEXT,
	notes TEXT,
	timeline INTEGER, -- number of days requested for turnaround
	active INTEGER, -- i.e. reviewed yet, or not. Could also be a boolean.
	jr_list TEXT, -- a comma-separated string of jr reviewers in order
	sr_list TEXT, -- of priority, should the current request be refused.
	date TIMESTAMP -- date of submission
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


