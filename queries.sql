--1: Simple Where Clause
SELECT title 
FROM work
WHERE first_publish_date > '2000-01-01';

SELECT * 
FROM rating 
WHERE rid = 1;

--2: Simple Group By (HAVING and without)
SELECT w.wid,w.title, COUNT(*) as isbn10_count
FROM work w, edition e
WHERE w.wid =e.wid
GROUP BY w.wid, w.title;

SELECT a.name,  COUNT(*) AS works_count
FROM authors a
JOIN work_authors wa ON a.aid = wa.aid
JOIN work w ON wa.wid = w.wid
GROUP BY a.aid, a.name
HAVING COUNT(*) >= 2;

--3: Join vs Cartesian Product
SELECT w.title, w.wid, e.isbn10
FROM work w
JOIN edition e ON w.wid = e.wid
ORDER BY w.title;

SELECT w.title, w.wid, e.isbn10
FROM work w, edition e
WHERE w.wid = e.wid
ORDER BY w.title;

--4: Join Types
SELECT e.isbn10, d.form
FROM edition e
JOIN digital d ON e.isbn10=d.isbn10;

SELECT e.isbn10, d.form
FROM edition e
LEFT JOIN digital d ON e.isbn10=d.isbn10;

SELECT e.isbn10, d.form
FROM edition e
RIGHT JOIN digital d ON e.isbn10=d.isbn10;

SELECT e.isbn10, d.form
FROM edition e
FULL OUTER JOIN digital d ON e.isbn10=d.isbn10;

--5: Null Values
SELECT wid, avg_rating
FROM rating
WHERE rating IS NULL;


SELECT w.title
FROM rating r, work w
WHERE r.avg_rating IS NULL AND r.wid=w.wid;

--6: Correlated Queries
SELECT w.title
FROM work w
WHERE w.wid IN (
				SELECT e.wid
				FROM edition e
				JOIN physical p ON e.isbn10 = p.isbn10
				WHERE p.type = 'paperback' AND e.wid = w.wid );

SELECT w.title 
FROM work w 
WHERE EXISTS (SELECT * 
			  FROM rating r 
			  WHERE r.avg_rating = 2.50 AND w.wid = r.wid);
			  
--7: Set Operations
	--Intersect
(SELECT w.aid FROM work_authors w WHERE w.wid = 'OL76837W')
INTERSECT
(SELECT w.aid FROM work_authors w WHERE w.wid = 'OL76833W');

	--Union
(SELECT w.aid FROM work_authors w WHERE w.wid = 'OL76837W')
UNION
(SELECT w.aid FROM work_authors w WHERE w.wid = 'OL81634W');

	--Difference
(SELECT w.wid FROM work_authors w WHERE w.aid = 'OL39307A')
EXCEPT
(SELECT w.wid FROM work_authors w WHERE w.wid = 'OL76837W');

--Respective Instances Without Set Operations
	--Intersect
SELECT w1.aid
FROM work_authors w1
INNER JOIN work_authors w2 ON w1.aid = w2.aid
WHERE w1.wid = 'OL76837W' AND w2.wid = 'OL76833W';

	--Union
SELECT w.aid
FROM work_authors w
WHERE w.wid = 'OL76837W' OR w.wid = 'OL81634W';

	--Difference
SELECT w1.wid
FROM work_authors w1
WHERE w1.aid = 'OL39307A' AND NOT EXISTS (
											SELECT 1
											FROM work_authors w2
											WHERE w2.wid = 'OL76837W' AND w1.wid = w2.wid
  );
  
 --8: View
 CREATE VIEW db_workauthors AS
(SELECT*
 FROM work_authors
 WHERE aid = 'OL39307A');
 
 --9: Overlap and Covering Constraints
 	--Overlap
SELECT d.isbn10 AS digital_isbn10, p.isbn10 AS physical_isbn10
FROM digital d
JOIN physical p
ON d.isbn10 = p.isbn10;

	--Covering
SELECT 
    e.isbn10 AS Edition_ISBN10,
    e.wid AS Work_ID,
    e.publish_date AS Publish_Date,
    CASE 
        WHEN d.isbn10 IS NOT NULL AND p.isbn10 IS NOT NULL THEN 'Both'
        WHEN d.isbn10 IS NOT NULL THEN 'Digital'
        WHEN p.isbn10 IS NOT NULL THEN 'Physical'
        ELSE 'None'
    END AS Edition_Type
FROM 
    edition e
LEFT JOIN 
    digital d ON e.isbn10 = d.isbn10
LEFT JOIN 
    physical p ON e.isbn10 = p.isbn10;

--10: Division Operator
-- “List all works that were all created by the author with name = ‘Dan Brown’.”
-- a) Regular Nested Query
SELECT w.title
FROM work w
WHERE w.wid IN (
 
SELECT wid FROM work_authors R
WHERE wid NOT IN (
	SELECT wid FROM (
    	(
        	SELECT sp.wid, p.aid
        	FROM (SELECT aid FROM authors WHERE name = 'Dan Brown') AS p
        	CROSS JOIN (SELECT wid FROM work_authors) AS sp
    	)
    	EXCEPT
    	(SELECT wid, aid FROM work_authors)
	) AS r
));

--b) Correlated Nested Query
SELECT w.title
FROM work w
WHERE w.wid IN (
 				SELECT wa.wid
				FROM work_authors wa
				WHERE NOT EXISTS (
									(SELECT a.aid
 									FROM authors a
 									WHERE a.name = 'Dan Brown') EXCEPT
																		(SELECT wa_inner.aid
 																		FROM work_authors wa_inner
 																		WHERE wa_inner.wid = wa.wid)
));











