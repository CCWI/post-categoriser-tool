-- phases
INSERT INTO phase(id, name) VALUES('0', 'Reamaining posts');
INSERT INTO phase(id, name) VALUES('1', 'Training');
INSERT INTO phase(id, name) VALUES('2', 'Inter-rater reliability');

-- example tweets
INSERT INTO post(id, text) VALUES('463440424141459456', 'I will never forget my first HTTP request measured in µs :-) #elixir #phoenix');

-- assign tweets to phases
INSERT INTO post_has_phase(post_id, phase_id) VALUES('463440424141459456', '1');

-- insert category names
INSERT INTO category_name(id, name) VALUES('1', 'Unrelated');
INSERT INTO category_name(id, name) VALUES('2', 'Trash related');
INSERT INTO category_name(id, name) VALUES('3', 'Trash dump related');
INSERT INTO category_name(id, name) VALUES('4', 'Spam');
commit;