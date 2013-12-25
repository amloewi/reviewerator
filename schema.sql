DROP TABLE reviewer;
DROP TABLE submission cascade;
DROP TABLE finished;
DROP TABLE alert;
DROP TABLE review;
DROP TABLE review_review;


CREATE TABLE person (
	--ID SERIAL PRIMARY KEY,
	id CHAR(30) PRIMARY KEY, -- login name for the system (no password)
	name CHAR(50),		-- The name that appears in system emails etc.
	email CHAR(50),
	year INTEGER, -- year in the program
	milestone CHAR(20), -- None, 1st Paper, 2nd Paper, or Proposal
	expertise TEXT, -- statistics, economics, IS, etc. Comma delimited.
	
	submitted INTEGER, -- num papers submitted
	reviewed INTEGER, -- num papers reviewed
	passes INTEGER, -- current number of 'pass' actions. Too many you're out.
	dropped INTEGER, -- num reviews accepted and not done.
	
	active_requests INTEGER, -- number of requests you're currently fielding
	active_submissions INTEGER, -- number of submissions you have out
	
	started TIMESTAMP, -- profile creation date
	last_review TIMESTAMP,
	
	enabled BOOLEAN -- 1/0 for are they 1) a student, and 2) haven't dropped 
					-- a review recently
);

CREATE TABLE paper (
	id SERIAL PRIMARY KEY,
	author CHAR(30), -- author's id
	title TEXT,
	abstract TEXT,
	requested_expertise TEXT,
	notes TEXT,
	timeline INTEGER, -- number of days requested for turnaround
	date TIMESTAMP -- date of submission
);

CREATE TABLE assignment (
	id SERIAL PRIMARY KEY,
	paper INT, -- The id of the related submission
	reviewer CHAR(30),			-- finally accepted
	candidates TEXT, -- list of next possibilities
	kind CHAR(10), -- jr/sr
	accepted BOOLEAN, --by a reviewer
	completed BOOLEAN --by a reviewer
);


CREATE TABLE finished_paper (
	-- anything?
) INHERITS (paper);

CREATE TABLE finished_assignment (
	-- anything?
) INHERITS (assignment);


-- Sits around in the box of an active reviewer. 
-- They signal the review is finished by clicking it.
CREATE TABLE finished (
	reviewer CHAR(30),
	requester CHAR(30)
);

CREATE TABLE alert (
	person CHAR(30), -- the intended recipient
	message TEXT, -- either 'you have a reviewer' or 'you have a review due'
	reveal_if_after DATE -- when it should be sent to the inbox
);

CREATE TABLE review (
	id SERIAL PRIMARY KEY,
	reviewer CHAR(30), -- their id
	author CHAR(30),   -- paper's author's id
	title TEXT,		   -- of the paper
	returned TIMESTAMP,-- 
	on_time BOOLEAN
	-- CONTENT, NOTES, UPLOAD IT, ETC.
	
	-- FEATURES OF THE REVIEWERS WHEN they review
	-- As well. Their -- expertise, timing, and ...
	-- milestone, I think.
);

CREATE TABLE review_review (
	id SERIAL PRIMARY KEY,
	paper_id INTEGER, -- the ID for the submission
	review_id INTEGER, -- the ID for the review
	satisfaction INTEGER -- 1-7 satisfaction Likert.
);


-- CREATE TABLE person_paper (
-- 	reviewer TEXT,
-- 	submission INTEGER,
-- );
-- 
-- 
-- -- necessary to 
-- CREATE TABLE person_review (
-- 	reviewer TEXT,
-- 	submission INTEGER,
-- );

-- reviewer_review?


