DROP TABLE person;
DROP TABLE paper cascade;
DROP TABLE assignment cascade;
DROP TABLE feedback cascade;
DROP TABLE finished;
DROP TABLE alert;
DROP TABLE review;


CREATE TABLE person (
	--ID SERIAL PRIMARY KEY,
	id VARCHAR(30) PRIMARY KEY, -- login name for the system (no password)
	name VARCHAR(50),		-- The name that appears in system emails etc.
	email VARCHAR(50),
	year SMALLINT, -- year in the program
	milestone VARCHAR(20), -- None, 1st Paper, 2nd Paper, or Proposal
	expertise TEXT, -- statistics, economics, IS, etc. Comma delimited.
	
	submitted SMALLINT, -- num papers submitted
	reviewed SMALLINT, -- num papers reviewed
	passes SMALLINT, -- current number of 'pass' actions. Too many you're out.
	dropped SMALLINT, -- num reviews accepted and not done. (allowed?)
	
	active_requests SMALLINT, -- number of requests you're currently fielding
	active_submissions SMALLINT, -- number of submissions you have out
	
	started TIMESTAMP, -- profile creation date
	last_review TIMESTAMP,
	
	enabled BOOLEAN, -- could change if they leave heinz, or refuse too much
	disabled_until TIMESTAMP -- if they become disabled after too many passes.
);

CREATE TABLE paper (
	id SERIAL PRIMARY KEY,
	author VARCHAR(30), -- author's id
	title TEXT,
	abstract TEXT,
	requested_expertise TEXT,
	paper BYTEA, -- later
	notes TEXT,
	timeline SMALLINT, -- number of days requested for turnaround
	submitted TIMESTAMP, -- date of submission
	num_assigned_reviewers SMALLINT,
	num_completed_reviews SMALLINT,
	
	active BOOLEAN
);

CREATE TABLE assignment (
	id SERIAL PRIMARY KEY,
	paper INTEGER, -- The id of the related submission
	reviewer VARCHAR(30),			-- currently assigned
	rvr_expertise TEXT, -- reviewer's expertise at time of assignment
	rvr_year SMALLINT,
	rvr_milestone VARCHAR(20),
	rejected TEXT, -- list of those who have turned it down.
	kind VARCHAR(10), -- jr/sr .. other?
	accepted BOOLEAN, --by a reviewer
	completed BOOLEAN, --by a reviewer
	
	assigned TIMESTAMP, -- 24 hours assigned w/ no response => pass
	due TIMESTAMP,
	
	active BOOLEAN
);

-- Sits around in the box of an active reviewer. 
-- They signal the review is finished by clicking it.
CREATE TABLE finished (
	id SERIAL PRIMARY KEY, -- need to find it to remove it
	paper_id INTEGER,
	reviewer_id VARCHAR(30),
	author_id VARCHAR(30),
	reviewer_name VARCHAR(50),
	author_name VARCHAR(50),
	due TIMESTAMP,
	title TEXT
);

CREATE TABLE alert (
	id SERIAL PRIMARY KEY,
	person VARCHAR(30), -- the intended recipient
	message TEXT, -- either 'you have a reviewer' or 'you have a review due'
	reveal_if_after TIMESTAMP -- when it should be sent to the inbox
);

CREATE TABLE review (
	id SERIAL PRIMARY KEY,
	reviewer VARCHAR(30), -- their id
	author VARCHAR(30),   -- paper's author's id
	title TEXT,		   -- of the paper
	reviewer_expertise TEXT, -- this will change over time, so keep a copy here
	review BYTEA, -- later; the  contents of uploaded review itself
	returned TIMESTAMP,-- 
	on_time BOOLEAN
	-- CONTENT, NOTES, UPLOAD IT, ETC.
);

CREATE TABLE feedback (
	id SERIAL PRIMARY KEY,
	author VARCHAR(30),
	author_name VARCHAR(50),
	title TEXT,
	paper_id INTEGER, -- the ID for the submission
	review_id INTEGER, -- the ID for the review
	score SMALLINT, -- 1-7 satisfaction Likert.
	notes TEXT, -- not yet implemented
	
	active BOOLEAN
);

